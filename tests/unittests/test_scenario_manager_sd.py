import unittest

from BPTK_Py import Model
from BPTK_Py.scenariomanager.scenario import SimulationScenario
from BPTK_Py.scenariomanager.scenario_manager_sd import ScenarioManagerSd

class TestScenarioManagerSD(unittest.TestCase):
    def setUp(self):
        pass

    def testScenarioManagerSD_add_scenario(self):
        class TestableTestScenarioManagerSD(ScenarioManagerSd):
            def __init__(self):
                super().__init__()
                self.called_instantiate_model = 0

            def instantiate_model(self):
                self.called_instantiate_model = 1 

        scenarioManager = TestableTestScenarioManagerSD()
        scenario1 = SimulationScenario(dictionary={},name="testScenario1", model=Model(), scenario_manager_name="scenarioManagerName1")
        scenario2 = SimulationScenario(dictionary={},name="testScenario2", model=Model(), scenario_manager_name="scenarioManagerName2")

        scenarioManager.add_scenario(scenario=scenario1)
        scenarioManager.add_scenario(scenario=scenario2)

        self.assertEqual(scenarioManager.scenarios["testScenario1"],scenario1)
        self.assertEqual(scenarioManager.scenarios["testScenario2"],scenario2)
        self.assertEqual(scenarioManager.called_instantiate_model,1)

    def testScenarioManagerSD_load_scenarios(self):
        import BPTK_Py.logger.logger as logmod
        logmod.loglevel="INFO"

        class TestableTestScenarioManagerSD(ScenarioManagerSd):
            def __init__(self, base_points, base_constants):
                super().__init__(base_points=base_points, base_constants=base_constants,scenarios={})
                self.called_instantiate_model = 0

            def instantiate_model(self):
                self.called_instantiate_model = 1

        scenarioManager = TestableTestScenarioManagerSD(base_constants={ "constant1" : 1.0 , "constant2" : 2.0 }, base_points= { "point1" : "11+11" , "point2" : "22+22" })

        scenarioDictionary = {
            "base": {
            },
            "scenario1" : {
                "constants": {
                    "constant1" : 1.1 
                },
                "points": {
                    "point2" : "33+33"
                }
                
            }
        }

        scenarioManager.load_scenarios(scen_dict=scenarioDictionary,model_file="modefile")    

        self.assertEqual(scenarioManager.scenarios["base"].dictionary["constants"]["constant1"],1.0)
        self.assertEqual(scenarioManager.scenarios["base"].dictionary["constants"]["constant2"],2.0)
        self.assertEqual(scenarioManager.scenarios["base"].dictionary["points"]["point1"],"11+11")
        self.assertEqual(scenarioManager.scenarios["base"].dictionary["points"]["point2"],"22+22")

        self.assertEqual(scenarioManager.scenarios["scenario1"].dictionary["constants"]["constant1"],1.1)
        self.assertEqual(scenarioManager.scenarios["scenario1"].dictionary["constants"]["constant2"],2.0)
        self.assertEqual(scenarioManager.scenarios["scenario1"].dictionary["points"]["point1"],"11+11")
        self.assertEqual(scenarioManager.scenarios["scenario1"].dictionary["points"]["point2"],"33+33")

if __name__ == '__main__':
    unittest.main()   
