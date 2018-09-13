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
#
############################
### Class abmVisualizer  ###
############################
class abmVisualizer():
    """
    Similar to the visualizer class, this class makes sure to create a valid dataframe from the Agent based simulation results and plot them
    """

    def __init__(self,scenario_manager_factory,bptk):
        """

        :param scenario_manager_factory: the scenario manager factory of bptk
        :param bptk: A live bptk object
        """
        self.scenario_manager_factory = scenario_manager_factory
        self.bptk = bptk


    def get_df_for_agent(self,data, agent_name):
        """
        This method creates a dataFrame from the abm agent statistics
        :param agent_name:
        :return:
        """
        def get_stats_for(data, agent_name):


            reshuffled_dict = {}
            output = []
            ts = list(data.keys())
            output = {}
            for t, row in data.items():
                for agent, series in row.items():
                    if agent == agent_name:
                        output[t] = series
            return output

        res = get_stats_for(data, agent_name)

        output = {}
        ts = list(res.keys())
        for i in range(0, len(res)):
            for t, series in res.items():
                for series_name, value in series.items():
                    output[series_name] = {} if series_name not in output.keys() else output[series_name]
                    output[series_name][t] = value

        return pd.DataFrame(output).fillna(0)


    def plot_scenarios(self, scenarios, agents, scenario_managers=[], kind=config.configuration["kind"],
                       alpha=config.configuration["alpha"], stacked=config.configuration["stacked"],
                       freq="D", start_date="", title="", visualize_from_period=0, visualize_to_period=0, x_label="", y_label="",
                       series_names={}, strategy=False,
                       return_df=False):
        """
         Generic method for plotting scenarios
         :param scenarios: simulation scenarios to plot (objects!)
         :param agents:  names of agents to plot the results for
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

        dfs = []
        for scenario in scenarios:
            data = scenario.statistics()

            for agent in agents:

                df = self.get_df_for_agent(data, agent)

                new_df = pd.DataFrame()

                if len(agents) > 1:
                    for series in df.columns:
                        new_df[agent + "-" + series] = df[series]
                else:
                    new_df = df

                dfs += [new_df]


        df = pd.concat(dfs,sort=True).fillna(0)

        ### Prepare the Plottable DataFrame using the visualize class. It generates the time series and the DataFrame


        ## If user did not set return_df=True, plot the simulation results (default behavior)
        if not return_df:
            ### Get the plot object
            if visualize_to_period == 0:

                ax = df.iloc[visualize_from_period:].plot(kind=kind, stacked=stacked, figsize=config.configuration["figsize"],
                                                 title=title,
                                                 alpha=alpha, color=config.configuration["colors"],
                                                 lw=config.configuration["linewidth"])

            elif visualize_from_period == visualize_to_period:
                print("[INFO] No data to plot for period t={} to t={}".format(str(visualize_from_period),str(visualize_to_period)))
                return None

            else:
                if visualize_to_period +1 > len(df):
                    visualize_to_period = len(df)

                ax = df.iloc[visualize_from_period:visualize_to_period].plot(kind=kind, stacked=stacked,
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


            self.update_plot_formats(ax)
            return ax

        ### If user wanted a dataframe instead, here it is!
        if return_df:
            if visualize_to_period == 0:
                return df.iloc[visualize_from_period:]
            elif visualize_from_period == visualize_to_period:
                print("[INFO] No data for period t={} to t={}".format(str(visualize_from_period + 1),
                                                                              str(visualize_to_period + 1)))
                return None
            else:
                return df.iloc[visualize_from_period:visualize_to_period]


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