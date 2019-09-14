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


from ..logger import log
import importlib

from ..abm.simultaneousScheduler import SimultaneousScheduler
from ..abm.dataCollector import DataCollector

from .scenario_manager import ScenarioManager


##############################
## ClASS ScenarioManagerABM ##
##############################


class ScenarioManagerABM(ScenarioManager):
    """
    This class reads ABM models and manages them
    """

    def __init__(self, json_config, name, filenames=[], model=None):
        """

        :param json_config: Configuration as a JSON dict
        :param name: name of scenario manager
        :param model: If this parameter contains an instance of BPTK_Py.Model, the scenario manager does not try to load an external code file
        """
        from ..abm.model import Model
        if model and not isinstance(model, Model):
            raise ValueError("model param is not of type BPTK_Py.Model")

        self.json_config = json_config
        self.type = "abm"
        self.scenarios = {}
        self.name = name
        self.filenames = filenames
        self.model = model


    def get_config(self):
        """

        :return: configuration dictionary
        """
        return self.json_config

    def add_scenarios(self, scenario_dictionary):
        self.instantiate_model(scenario_dictionary)

    def old_add_scenarios(self, scenario_dictionary):
        if not self.model:
            model = self.json_config["model"]

            for scenarioName, configuration in scenario_dictionary.items():

                if scenarioName not in self.scenarios.keys():

                    split = model.split(".")
                    className = split[len(split) - 1]
                    packageName = '.'.join(split[:-1])

                    try:
                        mod = importlib.import_module(packageName)
                    except ModuleNotFoundError as e:
                        log(
                            "[ERROR] File {}.py not found. Probably this is due to a faulty configuration or you forget to delete one. Skipping. Original Error: ".format(
                                packageName.replace(".", "/"),e))

                        return

                    try:
                        scenario_class = getattr(mod, className)
                    except AttributeError as e:
                        log(
                            "[ERROR] Could not find class {} in {}. Probably there is still a configuration that you do not use anymore. Skipping.".format(
                                className, packageName))
                        return

                    scenario = scenario_class(name=scenarioName, scheduler=SimultaneousScheduler(),
                                              data_collector=DataCollector())

                    scenario.instantiate_model()

                    scenario.configure(configuration)

                    scenario.set_scenario_manager(self.name)

                    self.scenarios[scenarioName] = scenario
                    log("[INFO] Successfully instantiated the simulation model for scenario {}".format(scenarioName))

        else:
            from copy import deepcopy
            for scenarioName, configuration in scenario_dictionary.items():

                if scenarioName not in self.scenarios.keys():
                    scenario = deepcopy(self.model)
                    scenario.name = scenarioName

                    scenario.scheduler = SimultaneousScheduler()
                    scenario.data_collector = DataCollector() if not scenario.data_collector else scenario.data_collector

                    scenario.instantiate_model()
                    scenario.configure(configuration)

                    scenario.set_scenario_manager(self.name)
                    self.scenarios[scenarioName] = scenario

                    log("[INFO] Successfully instantiated the simulation model for scenario {}".format(scenarioName))

    def instantiate_model(self, scenario_dictionary=None, reset=False):
        """
        Create the simulation model from the relative path to the file
        :param reset: If True, clear all scenarios and reinstantiate
        :return: None
        """
        if reset:
            self.scenarios = {}
            log("[INFO] Resetting the simulation scenarios for {}".format(str(self.name)))

        if not scenario_dictionary:
            scenario_dictionary = self.json_config["scenarios"]

        if not self.model:
            model = self.json_config["model"]

            for scenarioName, configuration in scenario_dictionary.items():

                if scenarioName not in self.scenarios.keys():

                    split = model.split(".")
                    className = split[len(split) - 1]
                    packageName = '.'.join(split[:-1])

                    try:
                        mod = importlib.import_module(packageName)
                    except ModuleNotFoundError as e:
                        log(
                            "[ERROR] File {}.py not found. Probably this is due to a faulty configuration or you forget to delete one. Skipping. Original Error: ".format(
                                packageName.replace(".", "/"),e))

                        return

                    try:
                        scenario_class = getattr(mod, className)
                    except AttributeError as e:
                        log(
                            "[ERROR] Could not find class {} in {}. Probably there is still a configuration that you do not use anymore. Skipping.".format(
                                className, packageName))
                        return

                    scenario = scenario_class(name=scenarioName, scheduler=SimultaneousScheduler(),
                                              data_collector=DataCollector())

                    scenario.instantiate_model()

                    scenario.configure(configuration)

                    scenario.set_scenario_manager(self.name)

                    self.scenarios[scenarioName] = scenario
                    log("[INFO] Successfully instantiated the simulation model for scenario {}".format(scenarioName))

        else:
            from copy import deepcopy
            for scenarioName, configuration in scenario_dictionary.items():

                if scenarioName not in self.scenarios.keys():
                    scenario = deepcopy(self.model)
                    scenario.name = scenarioName

                    scenario.scheduler = SimultaneousScheduler()
                    scenario.data_collector = DataCollector() if not scenario.data_collector else scenario.data_collector

                    scenario.instantiate_model()
                    scenario.configure(configuration)

                    scenario.set_scenario_manager(self.name)
                    self.scenarios[scenarioName] = scenario

                    log("[INFO] Successfully instantiated the simulation model for scenario {}".format(scenarioName))

