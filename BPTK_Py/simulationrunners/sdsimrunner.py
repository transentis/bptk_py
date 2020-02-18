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

from ..logger import log
from .simrunner import SimulationRunner
from ..sdsimulator import SDsimulationWrapper


################################
### Class SDSimulationRunner ###
################################


class SDSimulationRunner(SimulationRunner):
    """
    This class runs System dynamics simulations
    """

    # Scenarios comes as scenario object dict, equations as a dict: { equation : [scenario1,scenario2...]}
    def __generate_df(self, scenarios, equations):
        """
        Generates a dataFrame from simulation results. Generate series names and time series
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

                        series.name = scenarios[scenario].scenario_manager + "_" + scenarios[scenario].name + "_" + equation
                        plot_df[series.name] = series
           
        return plot_df

    def run_simulation(self, scenarios, equations, scenario_managers=[], strategy=False, ):
        """
         Generic method for plotting scenarios
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

            scenario_objects = SDsimulationWrapper(self.scenario_manager_factory).run_simulations(scenarios=scenarios,
                                                                                                  equations=equations,
                                                                                                  output=["frame"],
                                                                                                  scenario_managers=scenario_managers)

        else:
            scenario_objects = SDsimulationWrapper(self.scenario_manager_factory).run_simulations_with_strategy(
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
        return self.__generate_df(scenario_objects, dict_equations,
                                )
