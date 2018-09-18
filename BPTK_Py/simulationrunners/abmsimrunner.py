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
from .simrunner import simulationRunner
#
############################
### Class abmVisualizer  ###
############################


class abmSimulationRunner(simulationRunner):
    """
    Similar to the visualizer class, this class makes sure to create a valid dataframe from the Agent based simulation results and plot them
    """


    def get_df_for_agent(self,data, agent_name):
        """
        This method creates a dataFrame from the abm agent statistics
        :param agent_name:
        :return:
        """
        def get_stats_for(data, agent_name):
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


    def run_sim(self, scenarios, agents, scenario_managers=[], strategy=False,progressBar=False):
        """
        Method that generates the required dataframe(s) for the simulations
        :param scenarios:
        :param agents:
        :param scenario_managers:
        :return:
        """
        # Obtain simulation results

        scenario_objects = []

        for manager_name in scenario_managers:
            manager =self.scenario_manager_factory.scenario_managers[manager_name]
            scenario_objects += [scenario_obj for name, scenario_obj in manager.scenarios.items() if name in scenarios ]
            manager.instantiate_model(reset=False)

        dfs = []
        for scenario in scenario_objects:


            if not len(scenario.statistics()) > 0:
                scenario.run(progressBar)

            data = scenario.statistics()


            for agent in agents:

                df = self.get_df_for_agent(data, agent)

                new_df = pd.DataFrame()

                if len(agents) > 1:
                    for series in df.columns:
                        new_df[scenario.name + "-" + agent + "-" + series] = df[series]
                else:
                    new_df = df

                dfs += [new_df]


        df = pd.concat(dfs,sort=True).fillna(0)
        df.index.name = "t"

        ### Prepare the Plottable DataFrame using the visualize class. It generates the time series and the DataFrame


        return df


