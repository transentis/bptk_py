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


### IMPORTS

from BPTK_Py.logger.logger import log
import importlib

from BPTK_Py import SimultaneousScheduler
from BPTK_Py import DataCollector

from .scenario_manager import scenarioManager
###


##############################
## ClASS scenarioManagerABM ##
##############################


class scenarioManagerABM(scenarioManager):
    """
    This class reads ABM models and manages them
    """

    def __init__(self,json_config,name):
        """

        :param json_config: Configuration as a JSON dict
        :param name: name of scenario manager
        """

        self.json_config = json_config
        self.type = "abm"
        self.scenarios = {}
        self.name = name

    def get_config(self):
        return self.json_config


    def instantiate_model(self,reset=False):
        if reset:
            self.scenarios = {}
            log("[INFO] Resetting the simulation scenarios for {}".format(str(self.name)))


        for scenarioName, scenarioClass in self.json_config["scenarios"].items():

            if scenarioName not in self.scenarios.keys():

                split = scenarioClass.split(".")
                className = split[len(split) - 1]
                packageName = '.'.join(split[:-1])

                mod = importlib.import_module(packageName)
                scenario_class = getattr(mod, className)


                scenario = scenario_class(name=scenarioName, scheduler=SimultaneousScheduler(), data_collector=DataCollector())

                scenario.instantiate_model()

                scenario.configure(self.json_config)

                self.scenarios[scenarioName] = scenario
                log("[INFO] Successfully instantiated the simulation model for scenario {}".format(scenarioName))
