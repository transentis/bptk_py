
#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2021 transentis labs GmbH
# MIT License


import pandas as pd

from ..logger import log
from .scenario_runner import ScenarioRunner
from ..sdsimulation import SdSimulation


class SdRunner(ScenarioRunner):
    """Runs pure SD scenarios created with XMILE or with SD DSL.

    This is the class that merges the scenario settings (which it reads from SdScenario) onto the actual simulation model (which is either a Model or a SimulationModel).

    Runs a set of scenarios for a given scenario manager.
    """

    # Scenarios comes as scenario object dict, equations as a dict: { equation : [scenario1,scenario2...]}
    def __generate_df(self, sd_results_dict, return_format, scenarios, equations):
        """
        Generates a dataFrame from simulation results. Generate series names and time series
        :param sd_results_dict: a dictionary that contains the latest updated values of the simulation results in a dictionary format
        :param return_format: the data type of the return.(can either be dataframe, dictionary or json)
        :param scenarios: names of scenarios
        :param equations:  names of equations
        :param start_date: start date of the timeseries
        :param freq: frequency of time series, e.g. "D" for daily data
        :param series_names: names of series to rename to, using a dict: {equation_name : rename_to}
        :return:
        """
        
        ## Generate empty df to plot
        plot_df = pd.DataFrame()


        for scenario in scenarios.keys():
            df = scenarios[scenario].result

            if not df is None:
                for equation in equations.keys():

                    if equation in df.columns:
                        series = df[equation]
            
                        if scenarios[scenario].scenario_manager not in sd_results_dict:
                            sd_results_dict[scenarios[scenario].scenario_manager]=dict()
                        
                        if scenarios[scenario].name not in sd_results_dict[scenarios[scenario].scenario_manager]:
                            sd_results_dict[scenarios[scenario].scenario_manager][scenarios[scenario].name]=dict()
                            
                        if "equations" not in sd_results_dict[scenarios[scenario].scenario_manager][scenarios[scenario].name]:
                            sd_results_dict[scenarios[scenario].scenario_manager][scenarios[scenario].name]["equations"]=dict()
                            
                        if equation not in sd_results_dict[scenarios[scenario].scenario_manager][scenarios[scenario].name]["equations"]:
                            if return_format == "json":
                                sd_results_dict[scenarios[scenario].scenario_manager][scenarios[scenario].name]["equations"][equation]= df[equation].to_dict()
                            else:
                                sd_results_dict[scenarios[scenario].scenario_manager][scenarios[scenario].name]["equations"][equation]= df[equation]
                                
                            
                        series.name = scenarios[scenario].scenario_manager + "_" + scenarios[scenario].name + "_" + equation
                        plot_df[series.name] = series
            
            simulation_results=[]
            if return_format=="dict" or return_format=="json":
                simulation_results=sd_results_dict
            elif return_format=="df":
                simulation_results=plot_df
           
        return simulation_results


    def run_scenario_step(self, step, settings, scenario_manager, scenarios, equations, backend="python", seed=None):
        """
        Run a step of the given scenarios and return data for the given equations and agents.

        :param backend: "python" (default) or "rust" — execution backend. When "rust",
            each scenario's first step lazily initialises a `RustSdModel` cached on
            `sc.rust_model`; subsequent steps advance that model by one timestep.
            If JSON serialization or any Rust call fails, the scenario falls back to
            the Python backend for the rest of the session (sticky via `sc._rust_failed`).
        :param seed: Optional[int] — RNG seed passed to the Rust engine's `init()`.
            Fixing it makes a stochastic model's trajectory reproducible, which is
            what lets a Rust-backed session be replayed identically after the process
            restarts (see `bptk._restore_rust_session`). `None` lets the engine seed
            from entropy (non-reproducible). Ignored by the Python backend.
        """

        log("[INFO] Attempting to load scenarios from scenarios folder.")
        scenario_objects = self.scenario_manager_factory.get_scenarios(scenario_managers=[scenario_manager],
                                                                       scenarios=scenarios, scenario_manager_type="sd")

        #### Run the simulation scenarios

        if len(scenario_objects) == 0 :
            log("[ERROR] No scenarios found for scenario manager \"{}\" and scenarios \"{}\"".format(scenario_manager,",".join(scenarios)))

        for scenario, sc in scenario_objects.items():
            use_rust = (backend == "rust") and not getattr(sc, "_rust_failed", False)

            if use_rust:
                try:
                    self._run_scenario_step_rust(sc, step, settings, scenario_manager, scenario, equations, seed=seed)
                except (ValueError, ImportError, AttributeError) as e:
                    # Falling back on the very first step is harmless - there is no
                    # history yet, so Python starts the session from scratch. Falling
                    # back later is not: the Python backend has no record of the rounds
                    # the Rust engine already played (its memo lives in the engine, not
                    # in scenario_cache), so its lazy evaluator rebuilds them from the
                    # settings that are current *now*. Anything that carries history -
                    # a stock, a delay - then comes out wrong, and stays wrong for the
                    # rest of the session. Loud enough to be seen: a message tagged
                    # [ERROR] is printed even when logging goes to a file or to Logfire.
                    if abs(float(step) - float(sc.starttime)) < 1e-9:
                        log("[WARN] Rust step failed for '{}': {} — falling back to Python for the rest of this session".format(scenario, str(e)))
                    else:
                        log("[ERROR] Rust step failed for '{}' at step {}: {} — falling back to Python "
                            "for the rest of this session. This session has already played earlier "
                            "steps on the Rust engine, and the Python backend cannot see them: it "
                            "recomputes that history with the settings of the current step, so results "
                            "from here on may be wrong wherever the model carries state.".format(
                                scenario, step, str(e)))
                    sc._rust_failed = True
                    sc.rust_model = None
                    sc._rust_initial = None
                    sc._rust_initial_returned = False
                    self._run_scenario_step_python(sc, step, settings, scenario_manager, scenario, equations)
            else:
                self._run_scenario_step_python(sc, step, settings, scenario_manager, scenario, equations)

        return {name:scenario.result.to_dict() for name,scenario in scenario_objects.items()}

    def _run_scenario_step_python(self, sc, step, settings, scenario_manager, scenario, equations):
        """Single-step Python execution via SdSimulation. Lazily creates sc.sd_simulation
        on first call; reuses it for subsequent steps so the model memo persists."""
        if sc.sd_simulation is None:
            # need to set up the sd simulation
            # TODO: the following should really be part of SdSimulation
            sc.sd_simulation = SdSimulation(model=sc.model, name=sc.name)
            # first apply the scenario settings
            for name, value in sc.constants.items():
                sc.sd_simulation.change_equation(name=name, value=value)
            for name, points in sc.points.items():
                sc.sd_simulation.change_points(name=name, value=points)
            sc.sd_simulation.change_runspecs(starttime=sc.starttime, stoptime=sc.stoptime, dt=sc.dt)

        # now the settings relevant for this step
        if settings:
            if scenario_manager in settings:
                if scenario in settings[scenario_manager]:
                    if "constants" in settings[scenario_manager][scenario]:
                        constants = settings[scenario_manager][scenario]["constants"]
                        for name, value in constants.items():
                            sc.sd_simulation.change_equation(name=name, value=value)
                    if "points" in settings[scenario_manager][scenario]:
                        points = settings[scenario_manager][scenario]["points"]
                        for name, points in points.items():
                            sc.sd_simulation.change_points(name=name, value=points)

        sc.result = sc.sd_simulation.start(output=["frame"], start=step, until=step, equations=equations)

    def _run_scenario_step_rust(self, sc, step, settings, scenario_manager, scenario, equations, seed=None):
        """Single-step Rust execution.

        On first call: serialises the model to JSON, loads it into a RustSdEngine,
        applies the scenario-level constants / runspecs, and calls `init(equations, seed)`
        — which evaluates step 0 (t == starttime). The init values are cached on
        `sc._rust_initial` and returned by the first invocation of this method.
        Passing a fixed `seed` makes a stochastic model's trajectory reproducible so
        the session can be replayed identically on resume.

        On subsequent calls: applies any per-step constant / points overrides from
        `settings`, then advances the Rust cursor until it reaches the caller's
        `step` time. When the session's dt is a multiple of the model's dt
        (the sampling case), this issues several `rust_model.step()` calls per
        invocation; the common case (session dt == model dt) advances by exactly
        one timestep.
        """
        first_call = sc.rust_model is None

        if first_call:
            from BPTK_Py._rust_engine import RustSdEngine

            rust_json_str = sc.model.to_json()  # may raise ValueError → caller falls back

            engine = RustSdEngine()
            sc.rust_model = engine.load_model(rust_json_str)

            # Apply baseline scenario overrides (from scenario config, not per-step settings).
            # `sc.points` lookup overrides are already baked into model.points by setup_points()
            # at scenario registration time, so to_json() already includes them.
            for name, value in sc.constants.items():
                if isinstance(value, (int, float)):
                    sc.rust_model.set_constant(name, float(value))
                else:
                    raise ValueError(
                        "Non-numeric constant '{}' — cannot use Rust engine".format(name)
                    )

            sc.rust_model.set_runspecs(float(sc.starttime), float(sc.stoptime), float(sc.dt))

        # Apply per-step settings overrides. On the first call this must happen *before*
        # init(), because init() evaluates step 0 (t == starttime) and its values are what
        # the first run_step() returns. The Python path applies the settings and only then
        # computes the step, so overriding a constant in the very first run_step() would
        # otherwise be silently ignored by the Rust backend.
        if settings and scenario_manager in settings and scenario in settings[scenario_manager]:
            s = settings[scenario_manager][scenario]
            for name, value in s.get("constants", {}).items():
                sc.rust_model.set_constant(name, float(value))
            for name, pts in s.get("points", {}).items():
                # Rust set_points expects list[tuple[float, float]]; settings may carry
                # list[list[float, float]] (JSON-style).
                sc.rust_model.set_points(name, [(float(x), float(y)) for x, y in pts])

        if first_call:
            sc._rust_initial = sc.rust_model.init(equations, seed)
            sc._rust_initial_returned = False

        if not sc._rust_initial_returned:
            values = sc._rust_initial
            t = float(sc.starttime)
            sc._rust_initial_returned = True
        else:
            # Advance the Rust cursor until it reaches the caller's step time.
            # The session's dt (from begin_session) may exceed the model's dt — e.g.
            # sampling a dt=0.25 model at dt=1.0 — in which case we run multiple
            # internal model steps per run_step() call. This matches the Python path,
            # where SdSimulation.start(start=step, until=step) lazily computes
            # intermediate memo entries through the model's recursive evaluator.
            target = float(step)
            model_dt = float(sc.dt)
            current = sc.rust_model.current_time()
            n = max(1, round((target - current) / model_dt))
            values = {}
            for _ in range(n):
                values = sc.rust_model.step()
            t = sc.rust_model.current_time()

        sc.result = pd.DataFrame({eq: {float(t): val} for eq, val in values.items()})
        sc.result.index.name = "t"

    def restore_scenario_state_rust(self, sc, scenario_manager, scenario, equations, blob, folded, seed=None):
        """Rebuild a scenario's Rust engine from an exported memo grid — the fast
        alternative to replaying every step (see `bptk._restore_rust_session`).

        Loads the model, re-applies runspecs, the scenario-level baseline constants
        and the *folded* per-step overrides (`folded` = {"constants": {..}, "points":
        {..}} with last-value-wins), then imports the grid instead of stepping. After
        this the scenario is positioned mid-session: `_rust_initial_returned` is True,
        so the next `run_scenario_step` advances the cursor with `step()`.

        `blob` is the `(current_step, {entity_name: [values]})` pair produced by
        `RustSdModel.export_state()`; JSON round-trips it as a 2-element list.
        Raises (ValueError/ImportError/AttributeError) on failure so the caller can
        fall back to replay.
        """
        from BPTK_Py._rust_engine import RustSdEngine

        current_step, memo = blob[0], blob[1]

        rust_json_str = sc.model.to_json()  # may raise ValueError → caller falls back
        engine = RustSdEngine()
        sc.rust_model = engine.load_model(rust_json_str)

        # Runspecs must be set before the grid is installed.
        sc.rust_model.set_runspecs(float(sc.starttime), float(sc.stoptime), float(sc.dt))

        # Baseline scenario constants (points are already baked into to_json()).
        for name, value in sc.constants.items():
            if isinstance(value, (int, float)):
                sc.rust_model.set_constant(name, float(value))
            else:
                raise ValueError("Non-numeric constant '{}' — cannot use Rust engine".format(name))

        # Folded per-step overrides: reconstruct the model's mutable constant/points
        # state so future steps evaluate with the correct equations (no re-simulation).
        if folded:
            for name, value in folded.get("constants", {}).items():
                sc.rust_model.set_constant(name, float(value))
            for name, pts in folded.get("points", {}).items():
                sc.rust_model.set_points(name, [(float(x), float(y)) for x, y in pts])

        sc.rust_model.import_state(
            int(current_step),
            {name: [float(v) for v in values] for name, values in memo.items()},
            equations,
            seed,
        )

        sc._rust_initial = None
        sc._rust_initial_returned = True
        sc._rust_failed = False

    #TODO this really should just take on scenario manager - it doesn't make sense to call it on multiple scenario managers. It should be called run_scenarios
    def run_scenario(self, sd_results_dict, return_format, scenarios, equations, scenario_managers=[], backend="python"):
        """
        Runs all relevant scenarios for a given scenario manager.

        :param sd_results_dict: a dictionary that contains the latest updated values of the simulation results in a dictionary format
        :param return_format: the data type of the return.(can either be dataframe, dictionary or json).
        :param scenarios: names of scenarios to plot
        :param equations:  names of equations to plot
        :param scenario_managers: names of scenario managers to plot
        :param backend: "python" (default) or "rust" — execution backend
       """

        # Obtain simulation results
        scenario_objects = self._run_scenarios(scenarios=scenarios, equations=equations, output=["frame"], scenario_managers=scenario_managers, backend=backend)

        if len(scenario_objects.keys()) == 0:
            log("[ERROR] No scenario found for scenario_managers={} and scenario_names={}. Cancelling".format(
                str(scenario_managers), str(scenarios)))
            return None

        # Visualize Object
        dict_equations = {}

        # Clean up scenarios if we did not find all with the specified scenario managers. Will not warn if a scenario name is missing
        scenarios = [key for key in scenario_objects.keys()]

        all_equations = [item for sublist in [list(mod.model.equations.keys()) for mod in scenario_objects.values()] for item in sublist]
        all_equations = list(dict.fromkeys(all_equations))
        # Generate an index {equation .: [scenario1,scenario2...], equation2: [...] }
        # We are checking which scenarios can handle which equation
        import re
        for scenario_name in scenarios:
            sc = scenario_objects[scenario_name]  # <-- Obtain the actual scenario object
            for equation in equations:

                # Looking for patterns that refer to an arrayed variable. "*"-Equations are not really equations for us. Hence, removing array notation to find the raw name of the equation
                if "*" in equation:
                    re_find_indices = r'\[([^)]+)\]'
                    search = re.search(re_find_indices, equation)  # .group(0)#.replace("[", "").replace("]", "")
                    if search:
                        group = search.group(0)
                        cleaned_equation =equation.replace(group, "")
                    else: cleaned_equation = equation

                else: # Not an array variable
                    cleaned_equation = equation
                if cleaned_equation not in dict_equations.keys(): dict_equations[equation] = []

                if cleaned_equation in sc.model.equations.keys():
                    dict_equations[equation] += [scenario_name]

        # Search whether we found a match for all equations. Otherwise "did you mean" support
        for equation,scenario in dict_equations.items():
            if scenario == []:
                from ..util.didyoumean import didyoumean
                nearest_equations = didyoumean(equation, all_equations, 3)

                if len(nearest_equations) > 0:log("[ERROR] No simulation model containing equation \"{}\". Did you maybe mean one of \"{}\"?".format(equation,", ".join(nearest_equations)))
                else: log("[ERROR] No simulation model containing equation \"{}\"".format(equation))
        return self.__generate_df(sd_results_dict, return_format, scenario_objects, dict_equations,
                                )

    def _run_scenarios(self, scenarios, equations=[], output=["frame"], scenario_managers=[], backend="python"):
        """
        Method to run the simulations
        :param scenarios: names of scenarios to simulate
        :param equations: equations to simulate
        :param output: output type, default as a dataFrame
        :param scenario_managers: scenario managers as a list of names of scenario managers
        :param backend: "python" (default) or "rust" — execution backend
        :return: dict of SimulationScenario
        """
        ## Load scenarios

        log("[INFO] Attempting to load scenarios from scenarios folder.")
        scenario_objects = self.scenario_manager_factory.get_scenarios(scenario_managers=scenario_managers,
                                                                       scenarios=scenarios, scenario_manager_type="sd")

        #### Run the simulation scenarios

        if len(scenario_objects) == 0 :
            log("[ERROR] No scenarios found for scenario managers \"{}\" and scenarios \"{}\"".format(",".join(scenario_managers),",".join(scenarios)))

        for key in scenario_objects.keys():
            if key in scenarios:
                sc = scenario_objects[key]

                if backend == "rust":
                    try:
                        rust_json_str = sc.model.to_json()
                    except (ValueError, AttributeError) as e:
                        log("[WARN] Cannot serialize model to JSON: {} — falling back to Python".format(str(e)))
                        rust_json_str = None

                    if rust_json_str is not None:
                        sc.result = self._run_scenario_rust(sc, equations, rust_json_str)
                        if sc.result is None:
                            log("[WARN] Falling back to Python engine for scenario '{}'".format(sc.name))
                            sc.result = self._run_scenario_python(sc, equations, output)
                    else:
                        sc.result = self._run_scenario_python(sc, equations, output)
                else:
                    sc.result = self._run_scenario_python(sc, equations, output)

        return scenario_objects

    def _run_scenario_python(self, sc, equations, output):
        """Execute a scenario using the Python engine (SdSimulation)."""
        simu = SdSimulation(model=sc.model, name=sc.name)
        for const in sc.constants.keys():
            simu.change_equation(name=const, value=sc.constants[const])
        for name, points in sc.points.items():
            simu.change_points(name=name, value=points)
        simu.change_runspecs(starttime=sc.starttime, stoptime=sc.stoptime, dt=sc.dt)
        return simu.start(output=output, equations=equations)

    def _run_scenario_rust(self, sc, equations, json_str):
        """Execute a scenario using the Rust engine. Returns None on failure (triggers fallback)."""
        try:
            from BPTK_Py._rust_engine import RustSdEngine

            engine = RustSdEngine()
            rust_model = engine.load_model(json_str)

            # Apply scenario constant overrides
            for name, value in sc.constants.items():
                if isinstance(value, (int, float)):
                    rust_model.set_constant(name, float(value))
                else:
                    log("[WARN] Non-numeric constant '{}' — cannot use Rust engine".format(name))
                    return None

            # Note: scenario lookup points overrides are already applied to
            # model.points by setup_points() at registration time, so to_json()
            # already includes them. No need to call set_points() here.

            # Apply scenario runspec overrides
            rust_model.set_runspecs(float(sc.starttime), float(sc.stoptime), float(sc.dt))

            # Run simulation
            raw = rust_model.simulate(equations)

            # Convert to DataFrame matching SdSimulation output format
            converted = {}
            for eq_name, time_series in raw.items():
                converted[eq_name] = {float(t): v for t, v in time_series.items()}

            df = pd.DataFrame(converted)
            df.index.name = "t"
            df = df.sort_index()
            return df

        except (ValueError, ImportError) as e:
            log("[WARN] Rust engine failed: {} — falling back to Python".format(str(e)))
            return None

