#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018 transentis labs GmbH
#


####### IMPORTS
from threading import Thread
import time
from BPTK_Py.logger.logger import log
import os
import BPTK_Py.config.config as config
import json


#######

########################
## ClASS JSONMONITOR ##
########################


class jsonMonitor():
    """
    Simple monitoring script for JSON files
    Monitors JSON files and updates the scenarios/scenario managers in the internal object memory
    """

    def __init__(self, filename, json_dictionary,scenario_manager_factory):
        """

        :param filename: JSON file to monitor
        """

        self.json_dictionary = json_dictionary
        self.scenario_manager_factory = scenario_manager_factory

        log(
            "[INFO] Scenario Monitor: Starting to Monitor {} for changes.".format(
               str(filename)))

        # As long as this is True, I will keep monitoring. Otherwise the thread will terminate
        self.running = True


        # Initial last modification timestamp
        self._cached_stamp = os.stat(filename).st_mtime

        # Starting the thread
        t = Thread(target=self.__monitor, args=(filename,))
        t.start()


    def kill(self):
        """
        Kill method. Thread will die after calling this
        :return: None
        """
        self.running = False


    def __monitor(self, filename):
        """
        Actual method that monitors the source file for changes
        :return: None
        """
        while self.running:
            ## Get last modification timestamp and compare to cached one

            stamp = os.stat(filename).st_mtime

            ## Check if changed
            if stamp != self._cached_stamp:

                log("[INFO] Scenario Monitor for {}: Observed a change to scenarios".format(str(filename)))
                self._cached_stamp = stamp

                # a) Get new dictionary
                json_data = open(filename, encoding="utf-8").read()
                try:
                    json_dict = dict(json.loads(json_data))
                except ValueError as e:
                    log("[ERROR] Tried to update scenario from file {}, but was not able to successfully read it. Error message: \"{}\" ".format(filename, str(e)))
                    return None

                # b) Call _find_xx methods
                new_scenario_managers = self.__find_new_scenario_manager(json_dict)


                if len(new_scenario_managers.keys()) > 0:
                    log("[INFO] Found new scenario manager(s): {} ".format(str(new_scenario_managers)) )
                    # Actually just need to run the get_scenario_managers
                    self.scenario_manager_factory.get_scenario_managers()

                # c) store new scenario
                self.json_dictionary = json_dict

                log("[INFO] Scenario Monitor for {}: model updated and relaoded scenarios!".format(str(filename)))

                # Store new timestamp as cached timestamp
                self._cached_stamp = stamp
            time.sleep(1)

        log("[INFO] JSON Monitor for {}: I got killed... Goodbye!".format(str(filename)))


    def __find_new_scenario_manager(self, dictionary):
        current_scenario_managers = [k for k in self.json_dictionary.keys()]
        new_scenario_managers = [k for k in dictionary.keys()]

        for manager in current_scenario_managers:
            if manager in new_scenario_managers:
                new_scenario_managers.remove(manager)

        new_scenarios_and_managers = {}
        for name in new_scenario_managers:
            new_scenarios_and_managers[name] = dictionary[name]

        return new_scenarios_and_managers  # <-- Empty if no new scenario manager was found

