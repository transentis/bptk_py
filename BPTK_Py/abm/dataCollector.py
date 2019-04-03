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

class DataCollector:
    """
    A datacollector for the agent based simulation.
    Collects the output data of each agent/event and makes it available to external resources such as BPTK-Py to plot the data
    """

    def __init__(self):
        """

        """
        self.agent_statistics = {}
        self.event_statistics = {}

    def reset(self):
        self.agent_statistics = {}
        self.event_statistics = {}

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

    def collect_agent_statistics(self, time, agents):
        """
        Collect agent statistics from agent(s)
            :param time: t (int)
            :param agents: list of Agent
            :return: None
        """
        self.agent_statistics[time] = {}

        for agent in agents:

            if agent.agent_type not in self.agent_statistics[time]:
                self.agent_statistics[time][agent.agent_type] = {}

            if agent.state not in self.agent_statistics[time][agent.agent_type]:
                self.agent_statistics[time][agent.agent_type][agent.state] = {"count": 0}

            self.agent_statistics[time][agent.agent_type][agent.state]["count"] += 1

            if agent.properties:

                for agent_property_name, agent_property_value in agent.properties.items():
                    if agent_property_value["type"] == "Integer" or agent_property_value["type"] == "Double":
                        if agent_property_name not in self.agent_statistics[time][agent.agent_type][agent.state]:
                            self.agent_statistics[time][agent.agent_type][agent.state][agent_property_name] = {
                                "total": 0, "max": None, "min": None}

                        self.agent_statistics[time][agent.agent_type][agent.state][agent_property_name]["total"] += \
                        agent_property_value["value"]

                        self.agent_statistics[time][agent.agent_type][agent.state][agent_property_name]["mean"] = (
                                    self.agent_statistics[time][agent.agent_type][agent.state][agent_property_name]["total"]/
                                    self.agent_statistics[time][agent.agent_type][agent.state]["count"]
                        )

                        if self.agent_statistics[time][agent.agent_type][agent.state][agent_property_name][
                            "max"] is None:
                            (self.agent_statistics[time][agent.agent_type][agent.state]
                            [agent_property_name]["max"]) = agent_property_value["value"]

                            (self.agent_statistics[time][agent.agent_type][agent.state]
                            [agent_property_name]["min"]) = agent_property_value["value"]


                        else:
                            (self.agent_statistics[time][agent.agent_type][agent.state]
                            [agent_property_name]["max"]) = (max(self.agent_statistics[time][agent.agent_type]
                                                                 [agent.state][agent_property_name]["max"],
                                                                 agent_property_value["value"]))

                            (self.agent_statistics[time][agent.agent_type][agent.state]
                            [agent_property_name]["min"]) = (min(self.agent_statistics[time][agent.agent_type]
                                                                 [agent.state][agent_property_name]["min"],
                                                                 agent_property_value["value"]))


    def statistics(self):
        """
        Get the statistics collected
            :return: Dictionary
        """

        return self.agent_statistics
