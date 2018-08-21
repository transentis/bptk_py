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


## IMPORTS
from BPTK_Py.scenariomanager.scenario import simulationScenario
import BPTK_Py.config.config as config
from BPTK_Py.scenariomanager.scenario_manager import scenarioManager
from BPTK_Py.logger.logger import log
from BPTK_Py.modelmonitor.model_monitor import modelMonitor
import glob
import os
import json


##

####################################
### Class ScenarioManagerFactory ###
####################################


class ScenarioManagerFactory():
    """
    This class manages all scenario of all scenario managers and exposes methods to look them up, read from filesystem and flush them
    """

    def __init__(self):
        """
        Initialize object and reserve namespaces for scenario managers, monitors, scenarios and JSON file path (scenario storage)
        """

        self.scenario_managers = {}
        self.scenarios = {}
        self.scenario_monitors = {}
        self.path = ""

    def __readScenario(self, filename=""):
        """
        Reads the specified JSON file and generates the scenario_manager and scenario objects
        :param filename: filename of JSON file to parse
        :return:  self.scenario_managers
        """

        def merge_two_dicts(x, y):
            """
            Little helper method to merge dict x into y. If a key exists in x and y, x will win!
            Note: It is inplace! I return a copy z. This way, the original x and y dicts stay untouched and available for your own use
            :param x:
            :param y:
            :return: Merged dict of x and y
            """
            z = y.copy()  # start with y's keys and values
            z.update(x)  # modifies z with x's keys and values & returns None
            return z

        if len(filename) > 0:
            json_data = open(filename, encoding="utf-8").read()
            try:
                json_dict = dict(json.loads(json_data))
            except ValueError as e:
                log("[ERROR] Problem reading {}. Error message: {}".format(filename, str(e)))
                return None

            # ScenarioManager ->
            for group_name in json_dict.keys():
                base_constants = {}
                if "base_constants" in json_dict[group_name].keys():
                    base_constants = json_dict[group_name]["base_constants"]
                else:
                    base_constants = {}

                if group_name not in self.scenario_managers.keys():
                    self.scenario_managers[group_name] = scenarioManager(base_constants=base_constants, scenarios={},
                                                                         name=group_name)

                manager = self.scenario_managers[group_name]

                base_constants_updated = False
                # If we have new base constants
                if base_constants != manager.base_constants:
                    base_constants_merged = merge_two_dicts(base_constants, manager.base_constants)
                    manager.base_constants = base_constants_merged
                    base_constants_updated = True
                    log(
                        "[WARN] Found updated base constants for the scenario manager {}. Seems like this scenario manager is defined in multiple files. Updating all base constants for all scenarios. Make sure to only define the base_constants field exactly once!".format(
                            str(group_name)))

                # Make sure we obtain the original base constants from the scenario manager, although we read some already.

                manager.filename = filename

                manager.model_file = json_dict[group_name]["model"]

                # ScenarioManager -> "scenarios" ->
                scen_dict = json_dict[group_name]["scenarios"]

                # Create simulation scenarios from structure
                for scenario_name in scen_dict.keys():
                    ## Only add scenarios that the scenario manager did not observe yet --> avoid changing running models
                    ## If you need to reload a scenario pop it first.
                    ## Otherwise: If the base constants changed, I will make an update again and reload the scenario
                    if not scenario_name in manager.scenarios.keys() or base_constants_updated:
                        scenario_dict = scen_dict[scenario_name]

                        # ScenarioManager -> "scenarios" -> scenario_name -> "constants"
                        if len(manager.base_constants.keys()) > 0:
                            if not "constants" in scenario_dict.keys():
                                scenario_dict["constants"] = {}

                            for const, value in manager.base_constants.items():
                                if not const in scenario_dict["constants"].keys():
                                    scenario_dict["constants"][const] = value

                        sce = simulationScenario(dictionary=scen_dict[scenario_name], name=scenario_name, model=None,
                                                 group=group_name)

                        manager.scenarios[scenario_name] = sce

                if "source" in json_dict[group_name].keys():
                    manager.source = json_dict[group_name]["source"]
                    manager.instantiate_model()
                    if not manager.source in self.scenario_monitors.keys() and os.path.isfile(manager.source):
                        self.__add_monitor(manager.source, manager.model_file)
                    elif not os.path.isfile(manager.source):
                        log(
                            "[ERROR] Model monitor: Source model file not found: \"{}\". Not attempting to monitor changes to it.".format(
                                str(manager.source)))

            return self.scenario_managers
        else:
            print("[ERROR] Attempted to load a scenario manager without giving a filename. Skipping!")

    def get_scenario_managers(self, path=config.configuration["scenario_storage"], scenario_managers_to_filter=[]):
        """
        If self.scenario_managers is empty, this method attempts to load all scenario managers from disk in the specified path
        :param path: path to look for JSON files containing scenario managers and scenarios
        :param scenario_managers_to_filter: only look for certain scenario managers
        :return: self.scenario_managers
        """

        self.path = path
        # a) Only load scenarios if we do not already have them
        if len(self.scenario_managers.keys()) == 0:
            log("[INFO] New scenario manager or reset. Reading in all scenarios from storage!")
            for infile in glob.glob(os.path.join(path, '*.json')):
                self.__readScenario(filename=infile)

            log("[INFO] Successfully loaded all scenarios!")

        if len(scenario_managers_to_filter) > 0:
            scenario_managers = {k: v for k, v in self.scenario_managers.items() if k in scenario_managers_to_filter}

            return scenario_managers
        else:
            return self.scenario_managers

    def reset_scenario(self, scenario_manager, scenario):
        """
        Reloads exactly one scenario. For lookup, requires scenario manager's name and the scenario's name
        :param scenario_manager: name of scenario manager
        :param scenario: name of scenario
        :return: None
        """
        log("[INFO] Reloading scenario {} from {}".format(scenario, scenario_manager))

        manager = self.get_scenario_managers()[scenario_manager]
        scenario_filename = manager.filename
        manager.scenarios.pop(scenario)

        scenario_managers = self.__readScenario(filename=scenario_filename)

        log("[INFO] Successfully reloaded scenario {} for Scenario Manager {}".format(scenario_manager, scenario))

    def reset_all_scenarios(self):
        """
        Flushes all scenario managers and attempts to reload them
        :return: self.scenario_managers
        """
        self.scenario_managers = {}
        log("[INFO] Successfully reset all scenarios to original state")
        return self.get_scenario_managers()

    def get_scenario(self, scenario_manager, scenario):
        """
        Returns exactly one scenario object specified by the scenario_manager and scenario
        :param scenario_manager: Name of the scenario_manager to lookup
        :param scenario: Name of the scenario to lookup
        :return:
        """
        return self.scenario_managers[scenario_manager].scenarios[scenario]

    def get_scenarios(self, scenario_managers=[], scenarios=[]):
        """
        Get an arbitrary amount of scenario objects, depending on the parameters
        :param scenario_managers:  Names of the scenario_managers to lookup
        :param scenarios: Names of the scenarios to lookup
        :return:
        """

        managers = self.get_scenario_managers(scenario_managers_to_filter=scenario_managers)
        scenarios_objects = {}
        if len(scenario_managers) > 1:

            for manager_name, manager in managers.items():
                for scenario_name, scenario in manager.scenarios.items():

                    scenarios_objects[manager_name + "_" + scenario_name] = scenario
                    if scenario_name in scenarios:
                        scenarios += [manager_name + "_" + scenario_name]

        else:
            for manager_name, manager in managers.items():
                for scenario_name, scenario in manager.scenarios.items():

                    scenarios_objects[scenario_name] = scenario
                    if scenario_name in scenarios:
                        scenarios += [scenario_name]

        if len(scenarios) > 0:
            filtered_scenarios = {}
            for key in scenarios:
                if key in scenarios_objects.keys():
                    filtered_scenarios[key] = scenarios_objects[key]
            scenarios_objects = filtered_scenarios
        return scenarios_objects

    def add_scenario_during_runtime(self, scenario, scenario_manager, source="", model=None):
        """
        Add a scenario object during runtime
        :param scenario: scenario object to add
        :param scenario_manager: scenario_manager's name to add scenario to
        :param source: source file of the itmx file (optional)
        :param model: model name of the python file containing the python code for the model
        :return: None
        """
        if scenario_manager not in self.get_scenario_managers().keys():
            self.scenario_managers[scenario_manager] = scenarioManager({scenario.name: scenario}, name=scenario_manager,
                                                                       model_file=model)
            self.scenario_managers[scenario_manager].instantiate_model()

        else:
            log("[WARN] Scenario Manager already existing. Not overwriting the model!")
            self.scenario_managers[scenario_manager].add_scenario(scenario)

        if len(source) > 0:
            self.__add_monitor(source, model)

    def __add_monitor(self, source, model):
        """
        Add a file monitor for a source model
        :param source:  itmx file link (String)
        :param model:  output file link (without .py)
        :return:  None
        """
        if not source in self.scenario_monitors.keys():
            self.scenario_monitors[source] = modelMonitor(source, str(
                model), update_func=self.refresh_scenarios_for_filename)

    def destroy(self):
        """
        Kill all file monitor threads
        :return:
        """
        values = self.scenario_monitors.keys()
        for scenario in values:
            scenario.kill()

        self.scenario_monitors = {}

    def create_scenario(self, filename="/Users/dominikschroeck/Code/sd_py_simulator/BPTK_Py/scenarios/scenario.json",
                        dictionary={}):
        """
        Method for writing scenarios to JSON file
        :param filename: filename to write to
        :param dictionary: dictionary to parse to JSON
        :return:
        """
        with open(filename, 'w', encoding="utf-8") as outfile:
            json.dump(dictionary, outfile, indent=4)

    def refresh_scenarios_for_filename(self, filename):
        """
        Refreshes all scenarios that
        :param filename:
        :return:
        """
        # Obtain all scenarios
        managers = self.get_scenario_managers()

        for manager_name, manager in managers.items():
            if manager.source == filename:
                for scenario_name in manager.scenarios.keys():
                    log("[INFO] Resetting scenario {}".format(scenario_name))
                    self.reset_scenario(scenario=scenario_name, scenario_manager=manager_name)

        log("[INFO] Reset scenarios for all scenarios that require {}".format(filename))
