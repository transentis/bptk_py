
### IMPORTS
import json
from BPTK_Py.scenario_manager.scenario import simulation_scenario
import BPTK_Py.config.config as config
from BPTK_Py.logger.logger import log
import glob, os
from BPTK_Py.model_monitor.model_monitor import modelMonitor
###



###########################
## ClASS scenarioManager ##
###########################

### This class reads and writes scenarios and starts the file monitors for each scenario's model
class scenarioManager():

    ### Setup required object variables
    def __init__(self):
        self.scenario_monitors = {}
        self.scenarios = {}

    def add_scenario_during_runtime(self,scenario,source,model):
        if scenario.name in self.scenarios.keys():
            log("[ERROR] Scenario with name {} already exists! I will not overwrite.".format(scenario.name))
        else:
            self.scenarios[scenario.name] = scenario

        if len(source) >0 :
            if not source in self.scenario_monitors.keys():
                self.scenario_monitors[source] = modelMonitor(source, str(
                    model) + ".py")

    ### write scenario (coming as a dict) to file
    def createScenario(self,filename="/Users/dominikschroeck/Code/sd_py_simulator/BPTK_Py/scenarios/scenario.json",dictionary={}):
        #json_string = json.dumps(dictionary)
        with open(filename, 'w',encoding="utf-8") as outfile:
            json.dump(dictionary,outfile,indent=4)


    ### Returns all available scenarios and starts file monitors in case the source model is given
    def getAvailableScenarios(self, path=config.scenario_storage, scenario_managers=[]):
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
                if "source" in scenario.dictionary.keys() and not scenario.dictionary["source"] in self.scenario_monitors.keys():
                    self.scenario_monitors[scenario.dictionary["source"] ] = modelMonitor(scenario.dictionary["source"], str(scenario.dictionary["model"])+".py")
                log("[INFO] Successfully loaded scenario {} from {}".format(scenario.name, str(infile)))

                if not name in self.scenarios.keys():

                    self.scenarios[name] =  scenario


        if len(scenario_managers) > 0:
            return {key : value for  key, value in self.scenarios.items() if value.group in scenario_managers}

        else:
            return self.scenarios


    ### prints all available scenarios to stdout
    def printAvailableScenarios(self,path=config.scenario_storage,scenario_managers=[]):

        scenarios = self.getAvailableScenarios(path=path, scenario_managers=scenario_managers)
        print("\n")

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


    def get_scenario_managers(self):
        if len(self.scenarios.keys()) == 0:
            self.getAvailableScenarios()
        groups_scenarios = {}
        for name, scenario in self.scenarios.items():

            if scenario.group not in groups_scenarios.keys():
                groups_scenarios[scenario.group] = [scenario.name]
            else:
                groups_scenarios[scenario.group] += [scenario.name]

        return groups_scenarios
    ### Kill all monitors
    def destroy(self):
        for scenario in self.scenario_monitors.keys():
            self.scenario_monitors[scenario].kill()

    ### Read scenario from file and build a simulation_scenario object
    def __readScenario(self, filename="/Users/dominikschroeck/Code/sd_py_simulator/scenarios/scenario.json"):
        json_data = open(filename,encoding="utf-8").read()
        json_dict = dict(json.loads(json_data))
        scenarios = {}
        for group_name in json_dict.keys():

            group = group_name
            model = json_dict[group_name]["model"]
            scen_dict = json_dict[group_name]["scenarios"]

            ## Replace string keys as int



            for scenario_name in scen_dict.keys():
                sce = simulation_scenario(group=group,model=model,dictionary=scen_dict[scenario_name],name=scenario_name)
                scenarios[scenario_name] = sce


        return scenarios