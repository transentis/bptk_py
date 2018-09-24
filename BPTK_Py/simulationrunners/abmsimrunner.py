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

from .simrunner import SimulationRunner
from ..logger import log


############################
### Class abmVisualizer  ###
############################


class AbmSimulationRunner(SimulationRunner):
    """
    Similar to the visualizer class, this class makes sure to create a valid dataframe from the Agent based simulation results and plot them
    """

    def get_df_for_agent(self, data, agent_name, agent_states):

        """
        This method creates a dataFrame from the abm agent statistics
        :param agent_name:
        :return:
        """

        def get_stats_for(data, agent_name, agent_states):
            output = []
            ts = list(data.keys())
            output = {}
            for t, row in data.items():
                for agent, series in row.items():
                    if agent == agent_name:
                        if len(agent_states) > 0:
                            ser = series.copy()
                            columns = list(ser.keys())
                            for column in columns:
                                if column not in agent_states:
                                    ser.pop(column)
                            output[t] = ser
                        else:
                            output[t] = series
            return output

        res = get_stats_for(data, agent_name, agent_states)

        output = {}

        for i in range(0, len(res)):
            for t, series in res.items():
                for series_name, value in series.items():
                    output[series_name] = {} if series_name not in output.keys() else output[series_name]
                    output[series_name][t] = value

        return pd.DataFrame(output).fillna(0)

    def run_sim(self, scenarios, agents, scenario_managers=[], strategy=False, progressBar=False, agent_states=[],rerun=False,widget=False):
        """
        Method that generates the required dataframe(s) for the simulations
        :param scenarios: scenarios to plot for
        :param agents: Agents to plot for
        :param scenario_managers: Scenario managers to plot for
        :param progressBar: Show Progress Bar if True
        :param agent_states: LIst of agent states to plot for (optional)
        :param rerun: If True, will run the simulation. If False, only run if the model was never run before
        :return: DataFrame containing the simulation results
        """
        # Obtain simulation results

        scenario_objects = []

        if widget and len(scenarios) > 1:
            log("[ERROR] Currently, we can only spawn a widget for exactly one ABM simulation! Try to run for only one scenario")



        for manager_name in scenario_managers:
            manager = self.scenario_manager_factory.scenario_managers[manager_name]
            scenario_objects += [scenario_obj for name, scenario_obj in manager.scenarios.items() if name in scenarios]
            manager.instantiate_model(reset=False)

        dfs = []

        if widget:
            try:
                widgetLoader = scenario_objects[0].build_widget()
                from ipywidgets import Output
                from IPython.display import display


                widgetLoader.start()

            except Exception as e:
                log("[ERROR] Make sure you implement the build_widget() method in your ABM model!")
                print(e)



        for scenario in scenario_objects:

            if not len(scenario.statistics()) > 0 or rerun:
                scenario.run(progressBar)

            data = scenario.statistics()

            for agent in agents:

                df = self.get_df_for_agent(data, agent, agent_states)

                new_df = pd.DataFrame()

                for series in df.columns:
                    new_df[scenario.scenario_manager + "_" + scenario.name + "_" + agent + "_" + series] = df[series]


                dfs += [new_df]

        if not widget:
            df = pd.concat(dfs, sort=True).fillna(0)
            df.index.name = "t"

            return df
