#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2019 transentis labs GmbH
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



    def get_df_for_agent(self, data, agent_name, agent_states, agent_properties, agent_property_types):

        """
        This method creates a dataFrame from the abm agent statistics
        :param agent_name:
        :return:
        """

        def get_stats_for(data, agent_name, agent_states, agent_properties, agent_property_types):
            output = {}
            for t, row in data.items():
                for agent, states in row.items():
                    if agent == agent_name:
                        if len(agent_states) > 0:
                            if len(agent_properties) > 0:
                                if len(agent_property_types) > 0:

                                    counts = {}
                                    columns = list(states.keys())
                                    for column in columns:
                                        if column in agent_states:
                                            for agent_property in agent_properties:
                                                for property_type in agent_property_types:
                                                    counts[column + "_" + agent_property + "_" + property_type] = states[column][agent_property][property_type]
                                    output[t] = counts
                            else:
                                counts = {}
                                columns = list(states.keys())
                                for column in columns:
                                    if column in agent_states:
                                        counts[column] = states[column]["count"]
                                output[t] = counts
                        else:
                            output[t] = series
            return output

        res = get_stats_for(data, agent_name, agent_states, agent_properties, agent_property_types)

        output = {}

        for i in range(0, len(res)):
            for t, series in res.items():
                for series_name, value in series.items():
                    output[series_name] = {} if series_name not in output.keys() else output[series_name]
                    output[series_name][t] = value

        return pd.DataFrame(output).fillna(0)

    def run_simulation(self, scenarios, equations=[], agents=[], scenario_managers=[], strategy=False, progress_bar=False, agent_states=[], agent_properties=[], agent_property_types=[], rerun=False, widget=False):
        """
        Method that generates the required dataframe(s) for the simulations
        :param scenarios: scenarios to plot for
        :param agents: Agents to plot for
        :param scenario_managers: Scenario managers to plot for
        :param progressBar: Show Progress Bar if True
        :param agent_states: List of agent states to plot for (optional)
        :param agent_properties: List of agent properties to plot for (optional)
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

        if len(scenario_objects) <= 0:
            log("[ERROR] No scenario to simulate found")

        dfs = []


        if widget:
            try:
                widgetLoader = scenario_objects[0].build_widget()
                from ipywidgets import Output
                from IPython.display import display


                widgetLoader.start()

            except Exception as e:
                log("[ERROR] Make sure you implement the build_widget() method in your ABM model!")

        threads = []
        from threading import Thread

        for scenario in scenario_objects:

            if not len(scenario.statistics()) > 0:
                threads += [Thread(target=scenario.run,args=(progress_bar,))]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        for scenario in scenario_objects:

            ## IGNORE UNFINISHED ABM SCENARIOS. E.G. if it was cancelled before completion
            if hasattr(scenario,"scheduler"):
                if scenario.scheduler.progress < 1.0 :
                    continue # Skip this scenario

            data = scenario.statistics()


            if len(data) == 0:
                log("[WARN] No output data produced. Hopefully this was your intention.")
                return pd.DataFrame()


            for agent in agents:
                new_df = pd.DataFrame()

                df = self.get_df_for_agent(data, agent, agent_states, agent_properties, agent_property_types)


                if agent_properties:
                    for state in agent_states:
                        for agent_property in agent_properties:
                                for property_type in agent_property_types:
                                    new_df[scenario.scenario_manager + "_" + scenario.name + "_" + agent + "_" + state+ "_" + agent_property+ "_" + property_type] = df[state+"_"+agent_property + "_" + property_type]

                else:
                    for state in df.columns:
                        new_df[scenario.scenario_manager + "_" + scenario.name + "_" + agent + "_" + state] = df[state]

                dfs += [new_df]


        try:
            df = pd.concat(dfs, axis=1, sort=True).fillna(0)
        except ValueError as e:
            log("[ERROR] No data to plot found. It seems there is no scenario available.")

            return pd.DataFrame()

        df.index.name = "t"

        return df

    def train_simulation(self, scenarios, agents, episodes = 1, scenario_managers=[], progress_widget=None, agent_states=[], agent_properties=[], agent_property_types=[]):
        """
        Method that generates the required dataframe(s) for the simulations
        :param scenarios: scenarios to plot for
        :param agents: Agents to plot for
        :param scenario_managers: Scenario managers to plot for
        :param progressBar: Show Progress Bar if True
        :param agent_states: List of agent states to plot for (optional)
        :param agent_properties: List of agent properties to plot for (optional)
        :return: DataFrame containing the simulation results
        """
        # Obtain simulation results

        scenario_objects = []


        # find the appropriate scenarios

        for manager_name in scenario_managers:
            manager = self.scenario_manager_factory.scenario_managers[manager_name]
            scenario_objects += [scenario_obj for name, scenario_obj in manager.scenarios.items() if name in scenarios]
            manager.instantiate_model(reset=True)

        dfs = []

        episode_count = 0

        while episode_count < episodes:

            log("[INFO] Starting episode {} of {}".format(episode_count, episodes-1))

            if progress_widget:
                #TODO: need to handle the case of multiple simulations being trained - the following is only correct for the single simulation case
                progress_widget.value = episode_count/episodes

            for scenario in scenario_objects:
                scenario.begin_episode(episode_count)

                scenario.run(collect_data=False)

                data = scenario.statistics()

                for agent in agents:
                    # now collect the data for the agents - we just want the final value
                    new_df = pd.DataFrame()

                    df = self.get_df_for_agent(data, agent, agent_states, agent_properties, agent_property_types)


                    if agent_properties:
                        for state in agent_states:
                            for agent_property in agent_properties:
                                    for property_type in agent_property_types:
                                        new_df[scenario.scenario_manager + "_" + scenario.name + "_" + agent + "_" + state+ "_" + agent_property+ "_" + property_type] = df[state+"_"+agent_property + "_" + property_type]

                    else:
                        for state in df.columns:
                            new_df[scenario.scenario_manager + "_" + scenario.name + "_" + agent + "_" + state] = df[state]

                    dfs += [new_df]

                scenario.end_episode(episode_count)

            episode_count += 1

        df = pd.concat(dfs, axis=0, ignore_index=True).fillna(0)

        return df
