#                                                       /`-
# _                                  _   _             /####`-
#| |                                | | (_)           /########`-
#| |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
#| __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
#| |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018 transentis labs GmbH
# MIT License

## IMPORTS
import pandas as pd
from BPTK_Py import log
from .simrunner import simulationRunner
##


################################
### Class sdSimulationRunner ###
################################


class sdSimulationRunner(simulationRunner):
    """
    This class wraps away the visualization part for plots. Implements the plot_scenarios method and builds the plot
    """




    #Scenarios comes as scenario object dict, equations as a dict: { equation : [scenario1,scenario2...]}
    def __generate_df(self, scenarios, equations, series_names={}):
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



        if len(scenarios.keys()) > 1: # If we see more than one scenario, we will attach the scenario name to each Series name.
            for scenario in scenarios.keys():
                df = scenarios[scenario].result

                for equation in equations.keys():
                    if equation in df.columns:
                        series = df[equation]

                        series.name = scenario.name + "_" + equation
                        plot_df[series.name] = series
        else:
            scenario = scenarios[list(scenarios.keys())[0]]
            df = scenario.result

            for equation in equations.keys():
                if equation in df.columns:
                    series = df[equation]
                    series.name = scenario.name + "_" + equation
                    plot_df[series.name] = series


        # Process series name overrides as specified by user. Will traverse the series as they are in the DF
        # Usually this shold follow the order of the equations!
        series_names_keys = series_names.keys()





        return plot_df




    def run_sim(self, scenarios, equations, scenario_managers=[], strategy=False,):
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


        # If no scenario names are given, we will just take all scenarios that are available for the scenario manager(s)
        if len(scenarios) == 0 or scenarios[0] == '':
            scenarios = list(
                self.scenario_manager_factory.get_scenarios(scenario_managers=scenario_managers).keys())


        # Obtain simulation results
        if not strategy:
            scenario_objects = self.bptk.run_simulations(scenarios=scenarios, equations=equations,
                                                         scenario_managers=scenario_managers)
        else:
            scenario_objects = self.bptk.run_simulations_with_strategy(scenario_managers=scenario_managers,
                                                                       scenarios=scenarios, equations=equations)
        if len(scenario_objects.keys()) == 0:
            log("[ERROR] No scenario found for scenario_managers={} and scenario_names={}. Cancelling".format(str(scenario_managers), str(scenarios)))
            return None

        # Visualize Object
        dict_equations = {}


        # Clean up scenarios if we did not find all with the specified scenario managers. Will not warn if a scenario name is missing
        scenarios = [key for key in scenario_objects.keys()]


        # Generate an index {equation .: [scenario1,scenario2...], equation2: [...] }
        for scenario_name in scenarios:
            sc = scenario_objects[scenario_name]  # <-- Obtain the actual scenario object
            for equation in equations:
                if equation not in dict_equations.keys():
                    dict_equations[equation] = []
                if equation in sc.model.equations.keys():
                    dict_equations[equation] += [scenario_name]


        ### Prepare the Plottable DataFrame using the visualize class. It generates the time series and the DataFrame

        df = self.__generate_df(scenario_objects, dict_equations,
                                )

        return df


