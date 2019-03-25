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


import csv
import os

class CSVDataCollector:
    """
    A datacollector for the agent based simulation.
    Collects the output data of each agent/event and outputs them to CSV
    For now it only outputs the agent statistics, not the event statistics
    """

    def __init__(self,prefix="csv/"):
        """

        :param filename: filename of output file
        """
        self.agent_statistics = {}
        self.event_statistics = {}

        self.prefix = prefix
        if not os.path.isdir(prefix):
             os.mkdir(prefix)

        self.column_names = None

        self.csvwriters = {}


        self.headlines = None

    def record_event(self, time, event):
        """
        Record an event
        :param time: t (int)
        :param event: event instance
        :return: None
        """
        if time not in self.event_statistics:
            self.event_statistics[time] = {}

        if event.name not in self.event_statistics[time]:
            self.event_statistics[time][event.name] = 0

        self.event_statistics[time][event.name] += 1



    def reset(self):
        self.agent_statistics = {}


    def collect_agent_statistics(self, sim_time, agents):
        """
        Collect agent statistics from agent(s)
        :param sim_time: t (int)
        :param agents: list of Agent
        :return: None
        """

        for agent in agents:

            agent_type = agent.agent_type
            id = agent.id

            stats = {}
            stats["id"] = agent.id
            stats["time"] = sim_time


            for agent_property_name, agent_property_value in agent.properties.items():

                stats[agent_property_name] = agent_property_value['value']

            if not id in self.csvwriters.keys():
                outfile = open(self.prefix + "/" + str(id) + "_" + str(agent_type) + ".csv","w")
                writer = csv.writer(outfile,delimiter=";")
                self.csvwriters[id] = writer
                writer.writerow(list(stats.keys()))

            writer = self.csvwriters[id]
            writer.writerow(list(stats.values()))




    def statistics(self):
        """
        Get the statistics collected
        :return: Dictionary
        """

        return {}


