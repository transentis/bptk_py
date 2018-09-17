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
import os
import BPTK_Py.config.config as config
from BPTK_Py.logger.logger import log
import importlib
import datetime

from BPTK_Py.abm.simultaneousScheduler  import SimultaneousScheduler
from BPTK_Py.abm.dataCollector import DataCollector
from BPTK_Py.abm.model import Model
###


##############################
## ClASS scenarioManagerABM ##
##############################


class scenarioManagerABM():
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
        self.scenario = None
        self.name = name

    def get_config(self):
        return self.json_config


    def instantiate_model(self):
        scenarioClass = self.json_config["classes"]["scenario"]
        agent_classes = self.json_config["classes"]["agents"]

        split = scenarioClass.split(".")
        className = split[len(split) - 1]
        packageName = '.'.join(split[:-1])

        mod = importlib.import_module(packageName)
        scenario_class = getattr(mod, className)

        model = Model(self.json_config["name"])

        class clazzManager():
            def __init__(self, agent):
                self.agent = agent
                self.split = self.agent.split(".")
                self.className = self.split[len(self.split) - 1]
                self.packageName = '.'.join(self.split[:-1])
                self.module = importlib.import_module(self.packageName)

                self.class_ = getattr(self.module, self.className)

            def getClazz(self):
                return self.class_

            def getAgentFactory(self):
                return lambda agent_id, scenario: self.class_(agent_id, scenario)

            def getType(self):
                return self.getClazz().TYPE

        clazzManagers = []

        for agent in agent_classes:
            clazzManagers += [clazzManager(agent=agent)]

        for i in range(0, len(clazzManagers)):
            model.register_agent_factory(clazzManagers[i].getClazz().TYPE, clazzManagers[i].getAgentFactory())

        self.scenario = scenario_class(model=model, scheduler=SimultaneousScheduler(), data_collector=DataCollector())

        self.scenario.configure(self.json_config)
