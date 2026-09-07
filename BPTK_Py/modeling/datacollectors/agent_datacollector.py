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


#########################
## DATACOLLECTOR CLASS ##
#########################

from ..dataCollector import DataCollector
from copy import deepcopy
import pandas as pd


class AgentDataCollector(DataCollector):

    def collect_agent_statistics(self, time, agents):
        """
               Collect agent statistics from agent(s)
                   :param time: t (int)
                   :param agents: list of Agent
                   :return: None
               """

        for agent in agents:

            stats = {}
            stats["id"] = agent.id
            stats["time"] = time
            stats["agent_state"] = agent.state
            stats["agent_type"] = agent.agent_type
            if not agent.agent_type in self.agent_statistics:
                self.agent_statistics[agent.agent_type] = {}
            for agent_property_name, agent_property_value in agent.properties.items():
                if agent_property_value["type"] == "Integer" or agent_property_value["type"] == "Double":
                    stats[agent_property_name] = agent_property_value['value']

            if not agent.id in self.agent_statistics[agent.agent_type]:
                self.agent_statistics[agent.agent_type][agent.id] = {}

            self.agent_statistics[agent.agent_type][agent.id][time] = deepcopy(stats)

    def get_agent_stats(self):
        all_dfs = {}
        for agent_type in self.agent_statistics.keys():
            all_dfs[agent_type] = {}
            for agent_id in self.agent_statistics[agent_type].keys():
                agent_stats = {}
                for time, value in self.agent_statistics[agent_type][agent_id].items():
                    for col_name in value.keys():
                        if col_name in agent_stats:
                            agent_stats[col_name] += [value[col_name]]
                        else:
                            agent_stats[col_name] = [value[col_name]]
                df_agent = pd.DataFrame.from_dict(agent_stats)
                all_dfs[agent_type][agent_id] = df_agent
        return all_dfs

    def plot_agent_stats(self, agent_ids=[], properties=[], title="Base", agent_type=""):
        df_plot = pd.DataFrame()
        agent_stats = self.get_agent_stats()
        for agent_id in agent_ids:
            for property in properties:
                df_plot[str(agent_id) + "_" + agent_type + "_" + property] = agent_stats[agent_type][agent_id][property]
        from BPTK_Py.visualizations import bptk_style, plotting_config

        settings = plotting_config.resolved()
        with bptk_style():
            agent_plot = df_plot.plot(kind=settings["kind"],
                                      alpha=settings["alpha"],
                                      stacked=settings["stacked"],
                                      figsize=settings["figsize"],
                                      title=title,
                                      color=settings["colors"],
                                      lw=settings["linewidth"])
        return agent_plot
