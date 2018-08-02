
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

    ### write scenario (coming as a dict) to file
    def createScenario(self,filename="/Users/dominikschroeck/Code/sd_py_simulator/BPTK_Py/scenarios/scenario.json",dictionary={}):
        json_string = json.dumps(dictionary)
        with open(filename, 'w',encoding="utf-8") as outfile:
            outfile.write(json_string)


    ### Returns all available scenarios and starts file monitors in case the source model is given
    def getAvailableScenarios(self,path=config.scenario_storage):
        scenarios = {}
        for infile in glob.glob(os.path.join(path, '*.json')):
            scenario = self.__readScenario(infile)
            scenarios[scenario.name] = scenario

            # If the scenario contains a model and we do not already have a monitor for the scenario, start a new one and store it
            if "sourceModel" in scenario.dictionary.keys() and not scenario.name in self.scenario_monitors.keys():
                self.scenario_monitors[scenario.name] = modelMonitor(scenario.dictionary["sourceModel"], str(scenario.dictionary["model"])+".py")
            log("[INFO] Successfully loaded scenario {} from {}".format(scenario.name, str(infile)))

        return scenarios


    ### prints all available scenarios to stdout
    def printAvailableScenarios(self,path=config.scenario_storage):
        scenarios = self.getAvailableScenarios(path=path)
        print("\n")
        for scenario in scenarios.keys():
            dic_scenario = scenarios[scenario].dictionary

            print("*************** Scenario: {} *********************".format(str(scenario)))
            for key in dic_scenario.keys():
                if key == "constants":
                    print("Constants:")
                    constants_dic = dic_scenario[key]
                    for const_key in constants_dic.keys():
                        print(" \t {} : \t{}".format(str(const_key), str(constants_dic[const_key])))

                elif key == "equationsToSimulate":
                    print("\n")
                    print("Equations to simulate (if not explicitly called in Wrapper): ")
                    for item in dic_scenario[key]:
                        print("\t {}".format(str(item)))
                else:

                    print("{} \t: {}".format(str(key), str(dic_scenario[key])))

            print("\n")

        # Kill the monitoring threads because we do not require them
        self.destroy()


    ### Kill all monitors
    def destroy(self):
        for scenario in self.scenario_monitors.keys():
            self.scenario_monitors[scenario].kill()

    ### Read scenario from file and build a simulation_scenario object
    def __readScenario(self, filename="/Users/dominikschroeck/Code/sd_py_simulator/scenarios/scenario.json"):
        json_data = open(filename,encoding="utf-8").read()

        return simulation_scenario(dict(json.loads(json_data)))