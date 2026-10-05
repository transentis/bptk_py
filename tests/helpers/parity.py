"""Running a model on both engines and comparing them at every timestep."""

import pytest

from BPTK_Py.util import timerange


def rust_time_key(t):
    """Format time value to match Rust engine's time key format."""
    if t == int(t):
        return f"{t:.1f}"
    else:
        return str(t)


def run_parity(model, equations, atol=1e-10):
    """
    Run a model through both Python and Rust engines and compare results.

    Args:
        model: an SD DSL Model instance (fully defined)
        equations: list of equation/entity names to compare
        atol: absolute tolerance for pytest.approx

    Returns:
        (python_results, rust_results) dicts for further inspection if needed.
    """
    # --- Python results ---
    py_results = {}
    times = timerange(model.starttime, model.stoptime, model.dt, exclusive=False)
    for eq_name in equations:
        # Look up the element by name
        element = (
            model.stocks.get(eq_name)
            or model.flows.get(eq_name)
            or model.biflows.get(eq_name)
            or model.converters.get(eq_name)
            or model.constants.get(eq_name)
        )
        assert element is not None, f"Element '{eq_name}' not found in model"
        py_results[eq_name] = {t: element(t) for t in times}

    # --- Rust results ---
    # Imported here, not at module level: a module importing this helper must still be
    # collectable where the engine is not installed.
    from BPTK_Py._rust_engine import RustSdEngine

    json_str = model.to_json()
    engine = RustSdEngine()
    rust_model = engine.load_model(json_str)
    rust_results = rust_model.simulate(equations)

    # --- Compare ---
    for eq_name in equations:
        for t in times:
            py_val = py_results[eq_name][t]
            key = rust_time_key(t)
            assert key in rust_results[eq_name], \
                f"Missing Rust key '{key}' for {eq_name}"
            rust_val = rust_results[eq_name][key]
            assert py_val == pytest.approx(rust_val, abs=atol), \
                f"{eq_name} at t={t}: Python={py_val}, Rust={rust_val}"

    return py_results, rust_results
