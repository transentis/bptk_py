#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2023 transentis labs GmbH
# MIT License


import glob
import json
import os
from pathlib import Path


import BPTK_Py.config.config as config
from ..modelmonitor import FileMonitor
from ..logger import log
from ..modelmonitor import ModelMonitor
from ..scenariomanager import ScenarioManagerHybrid

from .scenario_manager_sd import ScenarioManagerSd


####################################
### Class ScenarioManagerFactory ###
####################################


class ScenarioManagerFactory():
    """
    This class manages all scenario of all scenario managers and exposes methods to look them up, read from filesystem and flush them
    """

    def __init__(self, start_scenario_monitor: bool, start_model_monitor: bool, scenario_storage=None):
        """
        Initialize object and reserve namespaces for scenario managers, monitors, scenarios and JSON file path (scenario storage)
        :param scenario_storage: folder the scenario files are read from, and read again on a reset. Defaults to the
            package configuration's "scenario_storage"
        """

        self.scenario_managers = {}

        self.scenarios = {}
        self.model_monitors = {}
        self.file_monitors = {}
        self.path = scenario_storage if scenario_storage else config.configuration["scenario_storage"]
        self.scenario_files = []

        self.start_scenario_monitor = start_scenario_monitor
        self.start_model_monitor = start_model_monitor

    def __readScenario(self, filename=""):
        """
        Reads the specified JSON file and generates the scenario_manager and scenario objects
        Pretty large method that does the following:
         - read scenarios from file
         - update the scenario managers in case a new scenario is detected.
         - If you actually updated a scenario, first you need to pop it from a scenario manager's scenarios dict
        :param filename: filename of JSON file to parse
        :return:  self.scenario_managers
        """
        model = None

        ## FIND A PARSER FOR ALL FILES THAT ARE NOT JSON
        if not os.path.isdir(filename):
            from ..modelparser import ParserFactory

            parser_class = ParserFactory(filename)

            if parser_class:
                meta_model = parser_class().parse_model(filename, silent=True)
                model, model_dictionary = meta_model.create_model()

            else:
                log("[ERROR] No parser available for file {}. Skipping!".format(filename))
                return None
        else:
            return

        # ScenarioManager ->
        if "type" in model_dictionary.keys():
            model_dictionary.pop("type")

        base_dictionaries = None
        for scenario_manager_name in model_dictionary.keys():

            # HANDLE Hybrid SCENARIOS
            if "type" in model_dictionary[scenario_manager_name].keys() and model_dictionary[scenario_manager_name][
                "type"].lower() == "abm":

                if scenario_manager_name not in self.scenario_managers:
                    self.scenario_managers[scenario_manager_name] = ScenarioManagerHybrid(
                        json_config=model_dictionary[scenario_manager_name],
                        name=scenario_manager_name, filenames=[filename], model=model)
                    self.scenario_managers[scenario_manager_name].instantiate_model()
                else:
                    self.scenario_managers[scenario_manager_name].add_scenarios(model_dictionary[scenario_manager_name]["scenarios"])
                    if filename not in self.scenario_managers[scenario_manager_name].filenames:
                        self.scenario_managers[scenario_manager_name].filenames +=[filename]

            # HANDLE SD SCENARIOS _ COMPLEX STUFF WITH ALL THE BASE CONSTANTS / BASE POINTS AND POSSIBLE DISTRIBUTION OVER FILES
            else:
                if scenario_manager_name not in self.scenario_managers.keys():
                    self.scenario_managers[scenario_manager_name] = ScenarioManagerSd(base_points={},
                                                                                      base_constants={},
                                                                                      scenarios={},
                                                                                      name=scenario_manager_name)

                manager = self.scenario_managers[scenario_manager_name]

                if filename not in manager.filenames:
                    manager.filenames += [filename]

                # Lookup base constants across all json files with the scenarios/ directory,
                # parsing each of them once per file read rather than once per manager
                if base_dictionaries is None:
                    base_dictionaries = self.__parse_scenario_files(self.scenario_files)
                manager.base_constants = self.__base_values(scenario_manager_name, base_dictionaries, "base_constants")
                manager.base_points = self.__base_values(scenario_manager_name, base_dictionaries, "base_points")

                # ScenarioManager -> "scenarios" ->
                scen_dict = model_dictionary[scenario_manager_name]["scenarios"]
                model_module = model_dictionary[scenario_manager_name]["model"]

                source = model_dictionary[scenario_manager_name].get(
                    "source", None)

                # this holds if there is a scenarios and a models folder in the
                # project directory
                main_dir = Path(filename).parent.parent

                if source:
                    source = str(main_dir / source)

                model_file = str(main_dir / model_module)

                # Create simulation scenarios from structure
                manager.load_scenarios(scen_dict=scen_dict, model_file=model_file, source=source,
                                       model_module=model_module)

                # Start monitor for source file
                if self.start_model_monitor and "source" in model_dictionary[scenario_manager_name].keys():
                    if not source in self.model_monitors.keys() and os.path.isfile(source):
                        self.__add_monitor(manager.source, manager.model_file)
                    elif not os.path.isfile(manager.source):
                        log(
                            "[ERROR] Scenario monitor: Source model file not found: \"{}\". Not attempting to monitor changes to it.".format(
                                str(manager.source)))

                manager.instantiate_model()

            ## CREATE FILE MONITOR
            if self.start_scenario_monitor and not filename in self.file_monitors.keys():
                self.file_monitors[filename] = FileMonitor(json_file=filename,
                                                           update_func=self.__refresh_scenarios_for_json)

        return self.scenario_managers

    def get_scenario_managers(self, path=None, scenario_managers_to_filter=None,
                              scenario_manager_type=""):
        """
        If self.scenario_managers is empty, this method attempts to load all scenario managers from disk in the specified path
        :param path: path to look for JSON files containing scenario managers and scenarios. Defaults to the factory's
            scenario storage, which is also where a reset reads from
        :param scenario_managers_to_filter: only look for certain scenario managers
        :param scenario_manager_type: only look for scenario managers of a given type
        :return: self.scenario_managers, a dictionary
        """
        scenario_managers_to_filter = [] if scenario_managers_to_filter is None else scenario_managers_to_filter

        if not path:
            path = self.path
        # a) Only load scenarios if we do not already have them
        if len(self.scenario_managers.keys()) == 0:
            log("[INFO] New scenario manager or reset. Reading in all scenarios from storage!")
            self.scenario_files = glob.glob(os.path.join(path, '*'))

            for infile in self.scenario_files:
                if not os.path.isdir(infile):
                    self.__readScenario(filename=infile)

            log("[INFO] Successfully loaded all scenarios!")

        scenario_managers = self.scenario_managers

        if scenario_manager_type != "":
            scenario_managers = {k: v for k, v in scenario_managers.copy().items() if v.type == scenario_manager_type}

        if len(scenario_managers_to_filter) > 0:
            scenario_managers = {k: v for k, v in scenario_managers.copy().items() if k in scenario_managers_to_filter}

        return scenario_managers

    def reset_scenario(self, scenario_manager, scenario):
        """
        Reloads exactly one scenario. For lookup, requires scenario manager's name and the scenario's name
        :param scenario_manager: name of scenario manager
        :param scenario: name of scenario
        :return: None
        """
        log("[INFO] Reloading scenario {} from {}".format(scenario, scenario_manager))

        manager = self.get_scenario_managers()[scenario_manager]
        manager_filenames = manager.filenames
        manager.scenarios.pop(scenario)

        for filename in manager_filenames:
            self.__readScenario(filename=filename)

        log("[INFO] Successfully reloaded scenario {} for Scenario Manager {}".format(scenario, scenario_manager))

    def reset_all_scenarios(self):
        """
        Flushes all scenario managers and attempts to reload them
        :return: self.scenario_managers
        """
        self.scenario_managers = {}
        return self.get_scenario_managers()

    def get_scenario(self, scenario_manager, scenario):
        """
        Returns exactly one scenario object specified by the scenario_manager and scenario
        :param scenario_manager: Name of the scenario_manager to lookup
        :param scenario: Name of the scenario to lookup
        :return:
        """
        return self.scenario_managers[scenario_manager].scenarios[scenario]

    def get_scenarios(self, scenario_managers=None, scenarios=None, scenario_manager_type=""):
        """
        Get an arbitrary amount of scenario objects, depending on the arguements:

        Parameters:
            scenario_managers:  List of Strings.
                Names of the scenario_managers to retrieve
            scenarios: List of Strings.
                Names of the scenarios to retrieve.
            scenario_manager_type: String
                "SD" for SD managers or "ABM" for agent-based and hybrid managers.

        Returns:
            Dictionary of scenario objects, indexed by the scenario name. If there is more then one manager, the scenario name is prefixed by the scenario manager name.
        """
        scenario_managers = [] if scenario_managers is None else scenario_managers
        scenarios = [] if scenarios is None else scenarios

        managers = self.get_scenario_managers(scenario_managers_to_filter=scenario_managers, scenario_manager_type=scenario_manager_type)

        # A list of its own: the prefixed names are added to it below, and the caller's
        # list used to grow with them on every call
        scenarios = list(scenarios)

        scenarios_objects = {}
        if len(managers) > 1:

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

    def __add_monitor(self, source, model):
        """
        Add a file monitor for a source model
        :param source:  itmx file link (String)
        :param model:  output file link (without .py)
        :return:  None
        """
        if not source in self.model_monitors.keys():
            self.model_monitors[source] = ModelMonitor(source, str(
                model), update_func=self._refresh_scenarios_for_source_model)

    def destroy(self):
        """
        Kill all file monitor threads
        :return:
        """

        for name, obj in self.model_monitors.items():
            obj.kill()
            log("[INFO] Killing monitoring thread for {}".format(name))

        for name, obj in self.file_monitors.items():
            obj.kill()
            log("[INFO] Killing monitoring thread for {}".format(name))

        self.model_monitors = {}
        self.file_monitors = {}

    def _refresh_scenarios_for_source_model(self, filename):
        """
        Refreshes all scenarios that use the given source file (e.g. itmx)
        :param filename:
        :return:
        """
        # Obtain all scenarios
        managers = self.get_scenario_managers()

        from copy import deepcopy

        for manager_name, manager in managers.items():
            if manager.source == filename:
                for scenario_name in deepcopy(list(manager.scenarios.keys())):
                    self.reset_scenario(scenario=scenario_name, scenario_manager=manager_name)

        log("[INFO] Reset scenarios for all scenarios that require {}".format(filename))

    def __refresh_scenarios_for_json(self, filename):
        """
        Refresh all scenario managers that use this filename as source (JSON!)
        Also update for scenarios that are spread over multiple files
        :param filename: JSON file name
        :return: None
        """
        managers = self.get_scenario_managers()

        managers = list(managers.values())

        for manager in managers:
            if filename in manager.filenames:
                for json_file in manager.filenames:
                    self.__readScenario(json_file)

    def __parse_scenario_files(self, filenames):
        """The dictionaries of all files a parser can read, in the order given.

        A file without a parser - a README beside the scenario files - is skipped, and
        only that file: the others still count.
        """
        from ..modelparser import ParserFactory

        dictionaries = []
        for filename in filenames:
            if os.path.isdir(filename):
                continue

            parser_class = ParserFactory(filename)
            if not parser_class:
                log("[ERROR] No parser available for file {}. Skipping!".format(filename))
                continue

            meta_model = parser_class().parse_model(filename, silent=True)
            _, model_dictionary = meta_model.create_model()
            dictionaries.append(model_dictionary)

        return dictionaries

    @staticmethod
    def __base_values(scenario_manager, dictionaries, key):
        """A scenario manager's `base_constants` or `base_points`, merged over all files.

        If a scenario manager spreads over multiple files and you define base values in
        different files for the same manager, just don't! The later file wins.
        """
        values = {}
        for model_dictionary in dictionaries:
            for name, value in model_dictionary.get(scenario_manager, {}).get(key, {}).items():
                log("[INFO] Updated {} of {}: {} = {}".format(key.replace("_", " "), scenario_manager, name, value))
                values[name] = value
        return values
