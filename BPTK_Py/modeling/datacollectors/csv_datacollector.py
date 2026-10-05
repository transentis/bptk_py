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
import csv
import os

from ...logger import log

#########################
## DATACOLLECTOR CLASS ##
#########################


class CSVDataCollector:
    """
    A datacollector for the agent based simulation that writes to CSV instead of memory.
    One file per agent type, one row per agent and timestep, and one file for the events.
    """

    EVENT_FILE = "events.csv"

    def __init__(self, prefix="csv/"):
        """
        :param prefix: directory the files are written to; created if it does not exist
        """
        self.prefix = prefix
        os.makedirs(prefix, exist_ok=True)

        # The columns of each file, fixed by the first row written to it. A file not in
        # here yet is started afresh, so a re-run after reset() does not append to the
        # results of the run before it.
        self._columns = {}

    def _filename(self, name):
        return os.path.join(self.prefix, name + ".csv")

    def _write_row(self, filename, row):
        if filename not in self._columns:
            self._columns[filename] = list(row.keys())
            with open(filename, "w", newline="", encoding="UTF-8") as outfile:
                csv.writer(outfile, delimiter=";").writerow(self._columns[filename])
        elif set(row.keys()) - set(self._columns[filename]):
            log("[WARN] CSVDataCollector: {} has no columns for {}; these values are not written".format(
                filename, sorted(set(row.keys()) - set(self._columns[filename]))))

        with open(filename, "a", newline="", encoding="UTF-8") as outfile:
            csv.writer(outfile, delimiter=";").writerow(
                [row.get(column, "") for column in self._columns[filename]])

    def record_event(self, time, event):
        """
        Append one event to the event file
        :param time: t (int)
        :param event: event instance
        :return: None
        """
        self._write_row(os.path.join(self.prefix, self.EVENT_FILE),
                        {"time": time, "event": event.name,
                         "sender_id": event.sender_id, "receiver_id": event.receiver_id})

    def reset(self):
        """
        Start every file afresh at the next row written to it
        """
        self._columns = {}

    def collect_agent_statistics(self, sim_time, agents):
        """
        Append the agents' statistics, one row per agent, to the file of its agent type
        :param sim_time: t (int)
        :param agents: list of Agent
        :return: None
        """
        for agent in agents:
            row = {"id": agent.id, "time": sim_time}
            for agent_property_name, agent_property_value in agent.properties.items():
                row[agent_property_name] = agent_property_value["value"]

            self._write_row(self._filename(str(agent.agent_type)), row)

    def statistics(self):
        """
        The results are in the files, not in memory
        :return: an empty dictionary
        """
        return {}
