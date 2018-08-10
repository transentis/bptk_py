from BPTK_Py.scenariomanager.scenario import simulationScenario
import BPTK_Py.config.config as config
from BPTK_Py.scenariomanager.scenario_manager import scenarioManager
from BPTK_Py.logger.logger import log
from BPTK_Py.modelmonitor.model_monitor import modelMonitor
import glob
import os
import json
from  json import JSONDecodeError
import sys



class ScenarioManagerFactory():
    def __init__(self):
        self.scenario_managers = {}
        self.scenarios = {}
        self.scenario_monitors = {}
        self.path = ""

    def __readScenario(self, filename=""):
        if len(filename) > 0:
            json_data = open(filename, encoding="utf-8").read()
            try:
                json_dict = dict(json.loads(json_data))
            except JSONDecodeError as e:
                log("[ERROR] Problem reading the JSON file {}. Skipping the file. Error message: {}".format(str(filename),str(e)))
                return None


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

    def get_scenario_managers(self, path=config.configuration["scenario_storage"], scenario_managers_to_filter=[]):
        self.path=path
        # a) Only load scenarios if we do not already have them
        if len(self.scenario_managers.keys()) == 0:
            log("[INFO] New scenario manager or reset. Reading in all scenarios from storage!")

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



            # b) Create ScenarioManagers for each group that I ever observed

            for key, scenario in scenarios.items():

                if scenario.group not in groups.keys():
                    groups[scenario.group] = {}

                groups[scenario.group][scenario.name] = scenario

            # c) Add Scenarios to ScenarioManagers
            self.scenario_managers = {}
            for group, scenarios in groups.items():
                self.scenario_managers[group] = scenarioManager(scenarios,name=group)

                # INstantiate new scenario managers and add the scenarios
        # b) Return self.scenarioManagers
            log("[INFO] Successfully loaded all scenarios!")

        if len(scenario_managers_to_filter)>0:
            return_value = {k:v for k,v in self.scenario_managers.items() if k in scenario_managers_to_filter}

            return return_value
        else:
            return self.scenario_managers

    def reset_scenario(self,scenario_manager,scenario_name):
        log("[INFO] Reloading scenario {} from {}".format(scenario_name,scenario_manager))

        scenario_filename = self.get_scenario_managers()[scenario_manager].scenarios[scenario_name].filename

        scenario_from_file = self.__readScenario(filename=scenario_filename)[scenario_name]

        self.scenario_managers[scenario_manager].scenarios[scenario_name] = scenario_from_file

        log("[INFO] Successfully reloaded scenario {} for Scenario Manager {}".format(scenario_manager,scenario_name))

    def reset_all_scenarios(self):
        self.scenario_managers = {}
        return self.get_scenario_managers()

    def get_scenario(self, scenario_manager, scenario):
        return self.scenario_managers[scenario_manager].scenarios[scenario]


    def get_scenarios(self,scenario_managers=[],scenario_names=[]):

        managers = self.get_scenario_managers(scenario_managers_to_filter=scenario_managers)

        scenarios = {}
        for manager_name, manager in managers.items():
            for scenario_name, scenario in manager.scenarios.items():
                    if scenario_name in scenarios.keys():
                        scenarios[scenario_name + "_" + manager_name] = scenario
                        if scenario_name in scenario_names:
                            scenario_names += [scenario_name + "_" + manager_name]
                    else:
                        scenarios[scenario_name] = scenario

        if len(scenario_names)>0:
            filtered_scenarios= {}
            for key in scenario_names:
                if key in scenarios.keys():
                    filtered_scenarios[key] = scenarios[key]
            scenarios = filtered_scenarios
        return scenarios




    def add_scenario_during_runtime(self, scenario, scenario_manager, source, model):
        if scenario_manager not in self.get_scenario_managers().keys():
            self.scenario_managers[scenario_manager] = scenarioManager({},name=scenario_manager)

        manager = self.get_scenario_managers()[scenario_manager]

        if scenario.name in manager.scenarios.keys():
            log("[ERROR] Scenario with name {} already exists! I will not overwrite.".format(scenario.name))
        else:
            manager.scenarios[scenario.name] = scenario

        if len(source) > 0:
            self.__add_monitor(source, model)


    def __add_monitor(self, source, model):
        if not source in self.scenario_monitors.keys():
            self.scenario_monitors[source] = modelMonitor(source, str(
                model) + ".py",update_func=self.refresh_scenarios_for_filename)

    def destroy(self):
        keys = self.scenario_monitors.keys()
        for scenario in keys:
            self.scenario_monitors[scenario].kill()

        self.scenario_monitors = {}


    def create_scenario(self, filename="/Users/dominikschroeck/Code/sd_py_simulator/BPTK_Py/scenarios/scenario.json", dictionary={}):
        with open(filename, 'w',encoding="utf-8") as outfile:
            json.dump(dictionary,outfile,indent=4)

    def refresh_scenarios_for_filename(self,filename):
        # Obtain all scenarios
        scenarios = self.get_scenarios()

        # Call reset_scenario for all scenarios that use the updated model
        for scenario in scenarios.values():
            if scenario.filename ==filename:
                self.reset_scenario(scenario_name=scenario.name,scenario_manager=scenario.group)
