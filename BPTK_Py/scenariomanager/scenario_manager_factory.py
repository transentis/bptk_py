from BPTK_Py.scenariomanager.scenario import simulationScenario
import BPTK_Py.config.config as config
from BPTK_Py.scenariomanager.scenario_manager import scenarioManager
from BPTK_Py.logger.logger import log
from BPTK_Py.modelmonitor.model_monitor import modelMonitor
import glob
import os
import json


class ScenarioManagerFactory():
    def __init__(self):
        self.scenario_managers = {}
        self.scenarios = {}
        self.scenario_monitors = {}
        self.path = ""

    def __readScenario(self, filename=""):
        if len(filename) > 0:
            json_data = open(filename, encoding="utf-8").read()
            json_dict = dict(json.loads(json_data))
            scenarios = {}
            for group_name in json_dict.keys():

                group = group_name
                model_name = json_dict[group_name]["model"]
                scen_dict = json_dict[group_name]["scenarios"]

                source = ""
                if "source" in json_dict[group_name].keys():
                    source = json_dict[group_name]["source"]
                ## Replace string keys as int

                for scenario_name in scen_dict.keys():
                    sce = simulationScenario(group=group, model_name=model_name,
                                             dictionary=scen_dict[scenario_name], name=scenario_name, source=source,filename=filename)
                    if not scenario_name in scenarios.keys():
                        scenarios[scenario_name] = sce
                    else:
                        scenarios[scenario_name +"_"+ sce.group] = sce

            return scenarios
        else:
            print("[ERROR] Attempted to load a scenario manager without giving a filename. Skipping!")

    def get_available_scenarios(self, path=config.configuration["scenario_storage"], scenario_managers=[]):
        self.path=path
        # a) Only load scenarios if we do not already have them
        if len(self.scenario_managers.keys()) == 0:

            scenarios = {}
            groups = {}
            for infile in glob.glob(os.path.join(path, '*.json')):
                if len(scenarios.keys()) > 0:
                    scenarios_new = self.__readScenario(infile)
                    for key in scenarios_new.keys():
                        scenarios[key] = scenarios_new[key]
                else:
                    scenarios = self.__readScenario(infile)

                # If the scenario contains a model and we do not already have a monitor for the scenario, start a new one and store it
                for name, scenario in scenarios.items():

                    if not scenario.source is None and not scenario.source in self.scenario_monitors.keys():
                        self.__add_monitor(scenario.source, scenario.model_name)
                        log("[INFO] Successfully loaded scenario {} from {}".format(scenario.name, str(infile)))



                print(scenarios['MakeYourStartUpGrow_strategy_ScenarioManager2'])

            # b) Create ScenarioManagers for each group that I ever observed

            for key, scenario in scenarios.items():

                if scenario.group not in groups.keys():
                    groups[scenario.group] = {}

                groups[scenario.group][scenario.name] = scenario

            # c) Add Scenarios to ScenarioManagers
            self.scenario_managers = {}
            for group, scenarios in groups.items():
                self.scenario_managers[group] = scenarioManager(scenarios)

                # INstantiate new scenario managers and add the scenarios
        # b) Return self.scenarioManagers

        return self.scenario_managers

    def reset_scenario(self,scenario_manager,scenario_name):
        scenario_filename = self.scenario_managers[scenario_manager].scenarios[scenario_name].filename
        scenarios_from_file = self.__readScenario(filename=scenario_filename)
        self.scenario_managers[scenario_manager].scenarios[scenario_name] = scenarios_from_file
        log("[INFO] Successfully reloaded scenario {} for Scenario Manager {}".format(scenario_manager,scenario_name))

    def get_scenario(self,scenario_manager, scenario_name):
        return self.scenario_managers[scenario_manager].scenarios[scenario_name]




    def add_scenario_during_runtime(self, scenario, source, model):
        if scenario.name in self.scenarios.keys():
            log("[ERROR] Scenario with name {} already exists! I will not overwrite.".format(scenario.name))
        else:
            self.scenarios[scenario.name] = scenario

        if len(source) > 0:
            self.__add_monitor(source, model)


    def __add_monitor(self, source, model):
        if not source in self.scenario_monitors.keys():
            self.scenario_monitors[source] = modelMonitor(source, str(
                model) + ".py")

    def destroy(self):
        keys = self.scenario_monitors.keys()
        for scenario in keys:
            self.scenario_monitors[scenario].kill()

        self.scenario_monitors = {}
