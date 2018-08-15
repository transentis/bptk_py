#                                                       /`-
# _                                  _   _             /####`-
#| |                                | | (_)           /########`-
#| |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
#| __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
#| |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018 transentis management & consulting. All rights reserved.
#

## IMPORTS
import pandas as pd
import BPTK_Py.config.config as config
from BPTK_Py.logger.logger import log
##


############################
### Class Visualizations ###
############################

## A simple class to configure the plot properties given by the user
class Visualizations():

    def __init__(self,scenario_manager_factory,bptk):
        self.scenario_manager_factory = scenario_manager_factory
        self.bptk = bptk


    #Scenarios comes as scenario object dict, equations as a dict: { equation : [scenario1,scenario2...]}
    def generate_plottable_df(self, scenarios, equations, start_date="1/1/2018", freq="D", series_names={}):
        scenario_names = list(scenarios.keys())

        ## Generate df to plot
        plot_df = pd.DataFrame()

        if len(scenarios.keys()) > 1: # If we see more than one scenario, we will attach the scenario name to each Series name.
            for scenario in scenarios.keys():
                df = scenarios[scenario].result

                for equation in equations.keys():
                    if scenarios[scenario].name in equations[equation]:

                        series = df[equation]
                        series.name = scenario + "_" + equation
                        plot_df[series.name] = series
        else:
            scenario = scenarios[list(scenarios.keys())[0]]
            df = scenario.result

            for equation in equations.keys():
                if scenario.name in equations[equation]:
                    series = df[equation]
                    series.name = equation
                    plot_df[series.name] = series

        plot_df.index= pd.date_range(start_date, periods=len(plot_df),freq=freq)


        # Process series name overrides as specified by user. Will traverse the series as they are in the DF
        # Usually this shold follow the order of the equations!
        series_names_keys = series_names.keys()

        if len(series_names) > 0:
            new_columns = {}
            for column in plot_df.columns:
                for series_names_key in series_names_keys:
                    if series_names_key in column:
                        new_column = column.replace(series_names_key, series_names[series_names_key])
                        if len(equations) == 1:
                            new_column = new_column.replace(equation[0], "")
                        new_columns[column] = new_column



            plot_df.rename(columns=new_columns, inplace=True)



        return plot_df

    def update_plot_formats(self,ax):

        ylabels = [format(label, ',.0f') for label in ax.get_yticks()]
        ax.set_yticklabels(ylabels)


    def plot_scenarios(self, scenario_names, equations, scenario_managers=[], kind=config.configuration["kind"],
                       alpha=config.configuration["alpha"], stacked=config.configuration["stacked"],
                       freq="D", start_date="1/1/2018", title="", visualize_from_period=0, x_label="", y_label="",
                       series_names=[], strategy=False,
                       return_df=False):

        # Run the simulations for the scenario and the specified equations (or all if no equation is given)

        # If no scenario names are given, we will just take all scenarios that are available for the scenario manager(s)
        if len(scenario_names) == 0 or scenario_names[0] == '':
            scenario_names = list(
                self.scenario_manager_factory.get_scenarios(scenario_managers=scenario_managers).keys())


        # Obtain simulation results
        if not strategy:
            scenario_objects = self.bptk.run_simulations(scenarios=scenario_names, equations=equations,
                                                         scenario_managers=scenario_managers)
        else:
            scenario_objects = self.bptk.run_simulations_with_strategy(scenario_managers=scenario_managers,
                                                                    scenario_names=scenario_names, equations=equations)
        if len(scenario_objects.keys()) == 0:
            log("[ERROR] No scenario found for scenario_managers={} and scenario_names={}. Cancelling".format(str(scenario_managers),str(scenario_names)))
            return None

        # Visualize Object
        visualize = self
        dict_equations = {}


        # Clean up scenarios if we did not find all with the specified scenario managers. Will not warn if a scenario name is missing
        scenario_names = [key for key in scenario_objects.keys()]


        # Generate an index {equation .: [scenario1,scenario2...], equation2: [...] }
        for scenario_name in scenario_names:
            sc = scenario_objects[scenario_name]  # <-- Obtain the actual scenario object
            for equation in equations:
                if equation not in dict_equations.keys():
                    dict_equations[equation] = []
                if equation in sc.model.equations.keys():
                    dict_equations[equation] += [scenario_name]


        ### Prepare the Plottable DataFrame using the visualize class. It generates the time series and the DataFrame
        df = visualize.generate_plottable_df(scenario_objects, dict_equations, start_date=start_date, freq=freq,
                                             series_names=series_names)

        ## If user did not set return_df=True, plot the simulation results (default behavior)
        if not return_df:
            ### Get the plot object
            ax = df[visualize_from_period:].plot(kind=kind, stacked=stacked, figsize=config.configuration["figsize"],
                                                 title=title,
                                                 alpha=alpha, color=config.configuration["colors"],
                                                 lw=config.configuration["linewidth"])

            ### Set axes labels and set the formats
            if (len(x_label) > 0):
                ax.set_xlabel(x_label)

            # Set the y-axis label
            if (len(y_label) > 0):
                ax.set_ylabel(y_label)

            visualize.update_plot_formats(ax)

        ### If user wanted a dataframe instead, here it is!
        if return_df:
            return df
