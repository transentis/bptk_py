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
import BPTK_Py.config.config as config
from BPTK_Py.logger.logger import log
import statistics
##


############################
### Class Visualizations ###
############################


class visualizer():
    """
    This class wraps away the visualization part for plots. Implements the plot_scenarios method and creates the dataFrame for plotting
    """

    def __init__(self,scenario_manager_factory,bptk):
        """

        :param scenario_manager_factory: the scenario manager factory of bptk
        :param bptk: A live bptk object
        """
        self.scenario_manager_factory = scenario_manager_factory
        self.bptk = bptk


    #Scenarios comes as scenario object dict, equations as a dict: { equation : [scenario1,scenario2...]}
    def generate_df(self, scenarios, equations, start_date="1/1/2018", freq="D", series_names={}):
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
                    series = df[equation]

                    series.name = scenario + "_" + equation
                    plot_df[series.name] = series
        else:
            scenario = scenarios[list(scenarios.keys())[0]]
            df = scenario.result

            for equation in equations.keys():
                series = df[equation]
                series.name = equation
                plot_df[series.name] = series



        # Create timeseries if start_date is given
        if not start_date == "":
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
                        new_columns[column] = new_column

            plot_df.rename(columns=new_columns, inplace=True)



        return plot_df

    def update_plot_formats(self,ax):
        """
        Configure the plot formats for the labels. Generates the formatting for y labels
        :param ax:
        :return:
        """
        ylabels_mean = statistics.mean(ax.get_yticks())

        # Override the format based on the mean values
        if ylabels_mean <= 2.0 and ylabels_mean >= -2.0:
            ylabels = [format(label, ',.2f') for label in ax.get_yticks()]

        elif ylabels_mean <= 10.0 and ylabels_mean >= -10.0:
            ylabels = [format(label, ',.1f') for label in ax.get_yticks()]

        else:
            ylabels = [format(label, ',.0f') for label in ax.get_yticks()]

        ax.set_yticklabels(ylabels)


    def plot_scenarios(self, scenarios, equations, scenario_managers=[], kind=config.configuration["kind"],
                       alpha=config.configuration["alpha"], stacked=config.configuration["stacked"],
                       freq="D", start_date="", title="", visualize_from_period=0, visualize_to_period=0, x_label="", y_label="",
                       series_names={}, strategy=False,
                       return_df=False):
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
        visualize = self
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

        df = visualize.generate_df(scenario_objects, dict_equations, start_date=start_date, freq=freq,
                                   series_names=series_names)

        ## If user did not set return_df=True, plot the simulation results (default behavior)
        if not return_df:
            ### Get the plot object
            if visualize_to_period == 0:
                ax = df[visualize_from_period:].plot(kind=kind, stacked=stacked, figsize=config.configuration["figsize"],
                                                 title=title,
                                                 alpha=alpha, color=config.configuration["colors"],
                                                 lw=config.configuration["linewidth"])

            elif visualize_from_period == visualize_to_period:
                print("[INFO] No data to plot for period t={} to t={}".format(str(visualize_from_period),str(visualize_to_period)))
                return None

            else:
                if visualize_to_period +1 > len(df):
                    visualize_to_period = len(df)

                ax = df[visualize_from_period:visualize_to_period].plot(kind=kind, stacked=stacked,
                                                     figsize=config.configuration["figsize"],
                                                     title=title,
                                                     alpha=alpha, color=config.configuration["colors"],
                                                     lw=config.configuration["linewidth"])
            ### Set axes labels and set the formats
            if (len(x_label) > 0):
                ax.set_xlabel(x_label)

            # Set the y-axis label
            if (len(y_label) > 0):
                ax.set_ylabel(y_label)

            for ymaj in ax.yaxis.get_majorticklocs():
                ax.axhline(y=ymaj, ls='-',alpha=0.05,color=(34.1 / 100, 32.9 / 100, 34.1 / 100))


            visualize.update_plot_formats(ax)

        ### If user wanted a dataframe instead, here it is!
        if return_df:
            if visualize_to_period == 0:
                return df[visualize_from_period:]
            elif visualize_from_period == visualize_to_period:
                print("[INFO] No data for period t={} to t={}".format(str(visualize_from_period + 1),
                                                                              str(visualize_to_period + 1)))
                return None
            else:
                return df[visualize_from_period:visualize_to_period]
