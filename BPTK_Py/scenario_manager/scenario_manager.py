
### IMPORTS
import json
from BPTK_Py.scenario_manager.scenario import simulation_scenario
import BPTK_Py.config.config as config
from BPTK_Py.logger.logger import log
import glob, os
###

class scenarioManager():

    def createScenario(self,filename="/Users/dominikschroeck/Code/sd_py_simulator/BPTK_Py/scenarios/scenario.json",dictionary={}):
        json_string = json.dumps(dictionary)
        with open(filename, 'w') as outfile:
            outfile.write(json_string)


    def readScenario(self,filename="/Users/dominikschroeck/Code/sd_py_simulator/scenarios/scenario.json"):
        json_data = open(filename).read()

        return simulation_scenario(dict(json.loads(json_data)))

    def getAvailableScenarios(self,path=config.scenario_storage):
        scenarios = {}
        for infile in glob.glob(os.path.join(path, '*.json')):
            scenario = self.readScenario(infile)
            scenarios[scenario.name] = scenario
            log("[INFO] Successfully loaded scenario {} from {}".format(scenario.name, str(infile)))

        return scenarios



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
                        print("\t {} : \t{}".format(str(const_key), str(constants_dic[const_key])))

                elif key == "equationsToSimulate":
                    print("\n")
                    print("Equations to simulate (if not explicitly called in Wrapper): ")
                    for item in dic_scenario[key]:
                        print("\t {}".format(str(item)))
                else:

                    print("{} \t: {}".format(str(key), str(dic_scenario[key])))

            print("\n")

