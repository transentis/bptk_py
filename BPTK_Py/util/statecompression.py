"""Compact the per-step logs of a session so they survive a round trip.

`settings_log` and `results_log` are keyed by step, and every step repeats the same
scenario-manager, scenario and variable names. Pivoting them - name first, values as a
list over the steps - drops that repetition, and the saving grows with the number of
rounds.

The first version of that pivot threw the step keys away and rebuilt them on the way
back as "1.0", "2.0", ... . That is only correct for a session whose steps happen to be
1, 2, 3; a session on a model with `starttime=0` and `dt=0.25` came back with every
value shifted, and one whose per-step settings were sparse came back with values under
the wrong steps entirely. `bptk.run_step`'s resume path already works around it, by
deriving the step grid from `starttime`/`dt` rather than trusting the log's own keys.

So the format carries the steps now:

    {"__format__": "steps-v2",
     "steps": ["0.0", "0.25", ...],
     "data": {manager: {scenario: {value_type: {name: <entry>}}}}}

An `<entry>` is a plain list when the name has a value at every step - the dense case,
which is the usual one and costs nothing over the old format. A name that appears only
at some steps carries its step indices with it:

    {"at": [0, 3], "values": [1.0, 7.0]}

Data written in the old format still reads, with the renumbering it was stored with:
those step keys are not recoverable, and rewriting them would be a guess of a different
kind. `is_compressed()` tells the two apart, and anything saved from now on is v2.
"""

FORMAT_KEY = "__format__"
FORMAT_V2 = "steps-v2"


def is_compressed(payload):
    """Whether `payload` is a compressed log, in either format."""
    if not isinstance(payload, dict) or not payload:
        return False
    if payload.get(FORMAT_KEY) == FORMAT_V2:
        return True
    return _looks_like_legacy(payload)


def _looks_like_legacy(payload):
    """The old format, recognised by its shape: a list where a step dict would be.

    The first level is scenario managers rather than steps, and the deepest level is a
    list of values rather than a single one. Steps are numbers written as strings, so a
    first key that is not numeric is already a strong hint.
    """
    first_key = next(iter(payload))
    if not isinstance(first_key, str) or first_key.replace(".", "").isdigit():
        return False
    node = payload[first_key]
    while isinstance(node, dict) and node:
        node = next(iter(node.values()))
    return isinstance(node, list)


def _pivot(source, depth):
    """Turn `{step: {...nested...: value}}` into `{...nested...: entry}` plus the steps.

    `depth` is how many dict levels sit between a step and the value: three for
    settings (manager, scenario, value type) and two for results (manager, scenario),
    the variable name being the level below that.
    """
    steps = [str(step) for step in source]
    index = {step: i for i, step in enumerate(source)}
    data = {}

    def walk(node, target, level):
        for key, value in node.items():
            if level < depth:
                walk(value, target.setdefault(key, {}), level + 1)
            else:
                entry = target.setdefault(key, {"at": [], "values": []})
                entry["at"].append(index[step])
                entry["values"].append(value)

    for step, managers in source.items():
        walk(managers, data, 0)

    _collapse_dense(data, len(steps), depth)
    return {FORMAT_KEY: FORMAT_V2, "steps": steps, "data": data}


def _collapse_dense(node, step_count, depth, level=0):
    """Drop the index list wherever a name has a value at every step."""
    for key, value in node.items():
        if level < depth:
            _collapse_dense(value, step_count, depth, level + 1)
        elif value["at"] == list(range(step_count)):
            node[key] = value["values"]


def _unpivot(payload, depth, leaf):
    """The inverse of `_pivot`. `leaf` builds the value stored under a name."""
    steps = payload["steps"]
    result = {}

    def walk(node, path, level):
        for key, value in node.items():
            if level < depth:
                walk(value, path + [key], level + 1)
                continue
            if isinstance(value, list):
                pairs = list(enumerate(value))
            else:
                pairs = list(zip(value["at"], value["values"]))
            for i, item in pairs:
                step = steps[i]
                target = result.setdefault(step, {})
                for part in path:
                    target = target.setdefault(part, {})
                target[key] = leaf(step, item)

    walk(payload["data"], [], 0)
    return result


def compress_settings(settings):
    """`{step: {manager: {scenario: {value_type: {name: value}}}}}` -> compressed."""
    return _pivot(settings, depth=3)


def compress_results(results):
    """`{step: {manager: {scenario: {name: {step: value}}}}}` -> compressed.

    The leaf is a single-entry dict keyed by the step itself, which is the shape the
    session writes; only its value is stored.
    """
    unwrapped = {
        step: {
            manager: {
                scenario: {
                    name: series[step] if isinstance(series, dict) and step in series else series
                    for name, series in scenarios.items()
                }
                for scenario, scenarios in managers.items()
            }
            for manager, managers in step_data.items()
        }
        for step, step_data in results.items()
    }
    return _pivot(unwrapped, depth=2)


def decompress_settings(settings):
    """Compressed -> `{step: {manager: {scenario: {value_type: {name: value}}}}}`."""
    if isinstance(settings, dict) and settings.get(FORMAT_KEY) == FORMAT_V2:
        return _unpivot(settings, depth=3, leaf=lambda step, value: value)
    return _decompress_settings_legacy(settings)


def decompress_results(results):
    """Compressed -> `{step: {manager: {scenario: {name: {step: value}}}}}`."""
    if isinstance(results, dict) and results.get(FORMAT_KEY) == FORMAT_V2:
        return _unpivot(results, depth=2, leaf=lambda step, value: {step: value})
    return _decompress_results_legacy(results)


# The readers for anything written before the format carried its steps. They rebuild
# the step keys as "1.0", "2.0", ... , which is what the data was stored with.
def _decompress_settings_legacy(settings):
    #               step: scenarioManager:  scenario:    constants:   constant: value
    result = dict[str, dict[str, dict[str, dict[str, dict[str, float]]]]]()
    
    for scenario_manager_name in settings.keys():
        for scenario_name in settings[scenario_manager_name]:
            for value_type in settings[scenario_manager_name][scenario_name]:
                for constant_name in settings[scenario_manager_name][scenario_name][value_type]:
                    constant = settings[scenario_manager_name][scenario_name][value_type][constant_name]
                    for i in range(1, len(constant) + 1):
                        # converts int to float in x.0 format (e.g. 3 -> 3.0)
                        step_str = f"{i:.1f}"
                        
                        if not step_str in result:
                            result[step_str] = dict()
                        step_transformed = result[step_str]
                        
                        if not scenario_manager_name in step_transformed:
                            step_transformed[scenario_manager_name] = dict()
                        scenario_manager_transformed = step_transformed[scenario_manager_name]
                        
                        if not scenario_name in scenario_manager_transformed:
                            scenario_manager_transformed[scenario_name] = dict()
                        scenario_transformed = scenario_manager_transformed[scenario_name]
                        
                        if not value_type in scenario_transformed:
                            scenario_transformed[value_type] = dict()
                        value_type_transformed = scenario_transformed[value_type]
                    
                        value_type_transformed[constant_name] = constant[i - 1]
                    
    return result

def _decompress_results_legacy(results):
    #               step: scenarioManager:  scenario:    constants:   constant: value
    result = dict[str, dict[str, dict[str, dict[str, dict[str, float]]]]]()
    
    for scenario_manager_name in results.keys():
        for scenario_name in results[scenario_manager_name]:
            for constant_name in results[scenario_manager_name][scenario_name]:
                constant = results[scenario_manager_name][scenario_name][constant_name]
                for i in range(1, len(constant) + 1):
                    # converts int to float in x.0 format (e.g. 3 -> 3.0)
                    step_str = f"{i:.1f}"
                    
                    if not step_str in result:
                        result[step_str] = dict()
                    step_transformed = result[step_str]
                    
                    if not scenario_manager_name in step_transformed:
                        step_transformed[scenario_manager_name] = dict()
                    scenario_manager_transformed = step_transformed[scenario_manager_name]
                    
                    if not scenario_name in scenario_manager_transformed:
                        scenario_manager_transformed[scenario_name] = dict()
                    scenario_transformed = scenario_manager_transformed[scenario_name]
                
                    scenario_transformed[constant_name] = {step_str: constant[i - 1]}

    return result


def _compress_time_series_data(data):
    """
    Helper function to compress time-series data similar to compress_settings logic.
    """
    if not data:
        return data

    # Transform step-indexed data into compressed format
    compressed = {}

    for step in data.keys():
        step_data = data[step]
        if not isinstance(step_data, dict):
            continue

        for key, value in step_data.items():
            if key not in compressed:
                compressed[key] = [value]
            else:
                compressed[key].append(value)

    return compressed

def _decompress_time_series_data(compressed_data):
    """
    Helper function to decompress time-series data similar to decompress_settings logic.
    """
    if not compressed_data:
        return compressed_data

    # Transform compressed format back to step-indexed data
    result = {}

    # Find the maximum length to determine number of steps
    max_length = max(len(values) if isinstance(values, list) else 1
                    for values in compressed_data.values()) if compressed_data else 0

    for i in range(max_length):
        step_str = f"{i + 1:.1f}"
        result[step_str] = {}

        for key, values in compressed_data.items():
            if isinstance(values, list) and i < len(values):
                result[step_str][key] = values[i]
            else:
                result[step_str][key] = values

    return result

def _is_compressed_time_series_data(data):
    """
    Helper function to detect if data looks like compressed time-series data.
    """
    if not isinstance(data, dict):
        return False

    # Check if values are lists (indicating compressed time-series)
    for value in data.values():
        if isinstance(value, list):
            return True
    return False