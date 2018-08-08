
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
    def __init__(self,scenarios,name):

        ### scenarios stores all available scenarios
        self.scenarios = scenarios
        self.name = name

    def get_scenario_names(self):
        return list(self.scenarios.keys())



    ### prints all available scenarios to stdout
    def print_available_scenarios(self, path=config.configuration["scenario_storage"], scenario_managers=[]):

        scenarios = self.get_available_scenarios(path=path)
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



    ### Read scenarios from file and build a simulation_scenario object
