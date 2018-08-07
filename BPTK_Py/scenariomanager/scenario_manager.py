
### IMPORTS
import json
from BPTK_Py.scenariomanager.scenario import simulationScenario
import BPTK_Py.config.config as config
from BPTK_Py.logger.logger import log
import glob, os
from BPTK_Py.modelmonitor.model_monitor import modelMonitor
###



###########################
## ClASS scenarioManager ##
###########################

### This class reads and writes scenarios and starts the file monitors for each scenario's model
class scenarioManager():

    ### Setup required object variables
    def __init__(self):
        self.scenario_monitors = {}

        ### scenarios stores all available scenarios
        self.scenarios = {}

    ### Add a simulation scenario during runtime and register it
    def add_scenario_during_runtime(self,scenario,source,model):
        if scenario.name in self.scenarios.keys():
            log("[ERROR] Scenario with name {} already exists! I will not overwrite.".format(scenario.name))
        else:
            self.scenarios[scenario.name] = scenario

        if len(source) >0 :
            self.__add_monitor(source, model)

    ### write scenario (coming as a dict) to file. Does not do any checking. Just converts dict to a JSON string
    def create_scenario(self, filename="/Users/dominikschroeck/Code/sd_py_simulator/BPTK_Py/scenarios/scenario.json", dictionary={}):
        with open(filename, 'w',encoding="utf-8") as outfile:
            json.dump(dictionary,outfile,indent=4)



    ### Returns all available scenarios and starts file monitors in case the source model is given
    def get_available_scenarios(self, path=config.configuration["scenario_storage"], scenario_managers=[]):
        scenarios = {}
        for infile in glob.glob(os.path.join(path, '*.json')):
            if len(scenarios.keys()) >0 :
                scenarios_new = self.__readScenario(infile)
                for key in scenarios_new.keys():
                    scenarios[key] = scenarios_new[key]
            else:
                scenarios= self.__readScenario(infile)


            # If the scenario contains a model and we do not already have a monitor for the scenario, start a new one and store it
            for name,scenario in scenarios.items():

                if not scenario.source is None and not scenario.source in self.scenario_monitors.keys():
                    self.__add_monitor(scenario.source, scenario.model_name)
                log("[INFO] Successfully loaded scenario {} from {}".format(scenario.name, str(infile)))

                if not name in self.scenarios.keys():

                    self.scenarios[name] =  scenario


        if len(scenario_managers) > 0:
            return {key : value for  key, value in self.scenarios.items() if value.group in scenario_managers}

        else:
            return self.scenarios


    ### prints all available scenarios to stdout
    def print_available_scenarios(self, path=config.configuration["scenario_storage"], scenario_managers=[]):

        scenarios = self.get_available_scenarios(path=path, scenario_managers=scenario_managers)
        print("\n")

        # Method that pretty-prints dictionaries
        def printdic(val):

            if type(val) == dict:

                for key in val.keys():

                    print("\t \t {} \t : {}".format(str(key),str(printdic(val[key]))))
            else:
                return val

        for scenario in scenarios.keys():
            dic_scenario = scenarios[scenario].dictionary


            print("*************** Scenario: {} *********************".format(str(scenario)))
            for key in dic_scenario.keys():
                if type(dic_scenario[key]) == dict:
                    print(key +":")
                    nested_dic = dic_scenario[key]
                    for nested_dic_key in nested_dic.keys():
                        print(" \t {}: ".format(str(nested_dic_key)))
                        printdic(nested_dic[nested_dic_key])
                else:

                    print("{} \t: {}".format(str(key), str(dic_scenario[key])))

            print("\n")

        # Kill the monitoring threads because we do not require them
        self.destroy()

    ## Returns all scenario manager names and their corresponding scenrio names
    def get_scenario_managers(self):
        if len(self.scenarios.keys()) == 0:
            self.get_available_scenarios()
        groups_scenarios = {}
        for name, scenario in self.scenarios.items():

            if scenario.group not in groups_scenarios.keys():
                groups_scenarios[scenario.group] = [scenario.name]
            else:
                groups_scenarios[scenario.group] += [scenario.name]

        return groups_scenarios

    ### Kill all monitors and flush scenarios
    def destroy(self):
        for scenario in self.scenario_monitors.keys():
            self.scenario_monitors[scenario].kill()
            self.scenario_monitors.pop(scenario)


    ### Read scenarios from file and build a simulation_scenario object
    def __readScenario(self, filename=""):
        if len(filename)>0:
            json_data = open(filename,encoding="utf-8").read()
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
                    sce = simulationScenario(group=group, model_name=model_name, dictionary=scen_dict[scenario_name], name=scenario_name, source=source)
                    scenarios[scenario_name] = sce


            return scenarios
        else:
            print("[ERROR] Attempted to load a scenario manager without giving a filename. Skipping!")

    ### Add a file monitor for source itmx model and convert to .py model when changes are detected
    def __add_monitor(self, source, model):
        if not source in self.scenario_monitors.keys():
            self.scenario_monitors[source] = modelMonitor(source, str(
                model) + ".py")