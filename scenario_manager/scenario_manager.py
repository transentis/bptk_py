import json
from scenario_manager.scenario import simulation_scenario

class scenarioManager():

    def createScenario(self,filename="/Users/dominikschroeck/Code/sd_py_simulator/scenarios/scenario.json",dictionary={}):

        json_string = json.dumps(dictionary)
        with open(filename, 'w') as outfile:
            outfile.write(json_string)


    def readScenario(self,filename="/Users/dominikschroeck/Code/sd_py_simulator/scenarios/scenario.json"):
        json_data = open(filename).read()

        return simulation_scenario(dict(json.loads(json_data)))








