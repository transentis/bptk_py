#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018 transentis labs GmbH
# MIT License


import pandas as pd
import numpy as np
import json

from ..logger import log
from .simrunner import SimulationRunner
from ..xmile_wrapper import XmileWrapper


################################
### Class XmileRunner ###
################################


class XmileRunner(SimulationRunner):
    """
    This class runs XMILE simulations
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
            if return_format=="dict":
                simulation_results=sd_results_dict
            elif return_format=="json":
                simulation_results=json.dumps(sd_results_dict, indent=2)
            elif return_format=="df":
                simulation_results=plot_df
           
        return simulation_results

    def run_simulation(self, sd_results_dict, return_format, scenarios, equations, scenario_managers=[], strategy=False, ):
        """
         Generic method for plotting scenarios
         :param sd_results_dict: a dictionary that contains the latest updated values of the simulation results in a dictionary format
        :param return_format: the data type of the return.(can either be dataframe, dictionary or json).
         :param scenarios: names of scenarios to plot
         :param equations:  names of equations to plot
         :param scenario_managers: names of scenario managers to plot
         :param kind: type of graph to plot
         :param alpha:  transparency 0 < x <= 1
         :param stacked: if yes, use stacked (only with kind="bar")
         :param freq: frequency of time series
         :param start_date: start date for time series
         :param title: title of plot
         :param visualize_from_period: visualize from specific period onwards
         :param visualize_to_period; visualize until a specific period
         :param x_label: label for x axis
         :param y_label: label for y axis
         :param series_names: names of series to rename to, using a dict: {equation_name : rename_to}
         :param strategy: set True if you want to use the scenarios' strategies
         :param return_df: set True if you want to receive a dataFrame instead of the plot
         :return: None
         """

        # Obtain simulation results
        if not strategy:

            scenario_objects = self._run_simulations(scenarios=scenarios,
                                                                                                  equations=equations,
                                                                                                  output=["frame"],
                                                                                                  scenario_managers=scenario_managers)

        else:
            scenario_objects = self._run_simulations_with_strategy(
                scenarios=scenarios,
                equations=equations,
                output=["frame"],
                scenario_managers=scenario_managers)
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

    def _run_simulations(self, scenarios, equations=[], output=["frame"], scenario_managers=[]):
        """
        Method to run the simulations
        :param scenarios: names of scenarios to simulate
        :param equations: equations to simulate
        :param output: output type, default as a dataFrame
        :param scenario_managers: scenario managers as a list of names of scenario managers
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
                simu = XmileWrapper(model=sc.model, name=sc.name)
                for const in sc.constants.keys():
                    simu.change_equation(name=const, value=sc.constants[const])
                for name, points in sc.points.items():
                    simu.change_points(name=name, value=points)

                # Store the simulation scenario. If we only want to run a specific equation as specified in parameter (and not all from scenario file), define here
                if len(equations) > 0:
                    # Find equations that I can actually simulate in the specific model of the scenario!
                    equations_to_simulate = []
                    for equation in equations:

                        equations_to_simulate += [equation]

                    sc.result = simu.start(output=output, equations=equations_to_simulate)

                else:
                    log("[ERROR] No equations to simulate given!")
                    return None

        return scenario_objects

    def _run_simulations_with_strategy(self, scenarios, equations=[], output=["frame"], scenario_managers=[]):
        """
        Method to run simulations with strategies

        :param scenarios: names of scenarios to simulate
        :param equations: equations to simulate
        :param output: output type, default as a dataFrame
        :param scenario_managers: scenario managers as a list of names of scenario managers
        :return: dict of SimulationScenario
        """

        log("[INFO] Attempting to load scenarios from scenarios folder.")

        scenarios_objects = self.scenario_manager_factory.get_scenarios(scenario_managers=scenario_managers,
                                                                        scenarios=scenarios, scenario_manager_type="sd")

        #### Run the simulation scenarios

        for key in scenarios_objects.keys():
            scenario = scenarios_objects[key]

            if len(equations) == 0:
                log("[ERROR] No equation to simulate given. Simulation will fail!")

            ## Read strategy from scenario
            strategy = {}
            if "strategy" in scenario.dictionary.keys():
                strategy = scenario.dictionary["strategy"]

            constants = {}
            if '0' in strategy.keys():
                constants = strategy.pop('0')

            for constant_key, constant_value in constants.items():
                scenarios_objects[key].constants[constant_key] = constant_value
                scenarios_objects[key].dictionary[constant_key] = constant_value

            ## Cast all keys to int (standard JSON does not allow int keys)
            strategy = {float(k): v for k, v in strategy.items()}

            simu = XmileWrapper(model=scenario.model, name=scenario.name)

            # Get the strategy's points to change equations at and sort ascending.
            points_to_change_at = sorted(list(strategy.keys()))

            if len(points_to_change_at) == 0:
                log(
                    "[WARN] Strategy does not contain any modifications to constants (Empty strategy). Will run the given scenario without strategy!")

                scenarios_objects[scenario.name] = \
                    self.run_simulations(scenarios=[scenario.name], equations=equations, output=output,
                                         scenario_managers=scenario_managers)[
                        scenario.name]

            # Simulation with a strategy. Iterate the points of the simulation. Run one step at a time
            else:
                for i in np.arange(scenario.model.starttime, scenario.model.stoptime + scenario.model.dt,
                                   scenario.model.dt):
                    t = round(i, 2)

                    if t == scenario.model.starttime:
                        for equation in scenario.constants.keys():
                            simu.change_equation(name=equation, value=scenario.constants[equation])
                        for name, points in scenario.points.items():
                            simu.change_points(name=name, value=points)

                    if t in points_to_change_at:
                        for equation in strategy[t]:
                            log("[INFO] t={}: Changing value of {} to {}".format(str(t), str(equation),
                                                                                 str(strategy[t][equation])))
                            simu.change_equation(name=equation, value=strategy[t][equation])

                    scenario.result = simu.start(equations=equations, output=output, start=t, until=t)

        return scenarios_objects
