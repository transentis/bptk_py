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

        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()        

        class TestableTestScenarioManagerSD(ScenarioManagerSd):
            def __init__(self, base_points, base_constants):
                super().__init__(base_points=base_points, base_constants=base_constants,scenarios={})
                self.called_instantiate_model = 0

            def instantiate_model(self):
                self.called_instantiate_model = 1

        scenarioManager = TestableTestScenarioManagerSD(base_constants={ "constant1" : 1.0 , "constant2" : 2.0 }, base_points= { "point1" : "11+11" , "point2" : "22+22" })

        scenario1 = SimulationScenario(dictionary={ "constants" : { "constant1" : 1.0 , "constant2" : 2.0 } , "points" : { "point1" : "11+11" , "point2" : "22+22" } },name="scenario1", model=Model(), scenario_manager_name="scenarioManagerName")
        scenario2 = SimulationScenario(dictionary={ "constants" : { "constant1" : 11.0 , "constant2" : 12.0 } , "points" : { "point1" : "111+111" , "point2" : "222+222" } },name="scenario2", model=Model(), scenario_manager_name="scenarioManagerName")
        scenarioManager.add_scenario(scenario=scenario1)

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
            },
            "scenario2" : {
                "constants": {
                    "constant1" : 11.0, 
                    "constant2" : 12.0
                },
                "points": {
                    "point1" : "111+111",
                    "point2" : "222+222"
                }               
            },            
        }

        scenarioManager.load_scenarios(scen_dict=scenarioDictionary,model_file="testModelFile",source="testSource")    

        self.assertEqual(scenarioManager.scenarios["base"].dictionary["constants"]["constant1"],1.0)
        self.assertEqual(scenarioManager.scenarios["base"].dictionary["constants"]["constant2"],2.0)
        self.assertEqual(scenarioManager.scenarios["base"].dictionary["points"]["point1"],"11+11")
        self.assertEqual(scenarioManager.scenarios["base"].dictionary["points"]["point2"],"22+22")

        self.assertEqual(scenarioManager.scenarios["scenario1"].dictionary["constants"]["constant1"],1.1)
        self.assertEqual(scenarioManager.scenarios["scenario1"].dictionary["constants"]["constant2"],2.0)
        self.assertEqual(scenarioManager.scenarios["scenario1"].dictionary["points"]["point1"],"11+11")
        self.assertEqual(scenarioManager.scenarios["scenario1"].dictionary["points"]["point2"],"33+33")

        self.assertEqual(scenarioManager.scenarios["scenario2"].dictionary["constants"]["constant1"],11.0)
        self.assertEqual(scenarioManager.scenarios["scenario2"].dictionary["constants"]["constant2"],12.0)
        self.assertEqual(scenarioManager.scenarios["scenario2"].dictionary["points"]["point1"],"111+111")
        self.assertEqual(scenarioManager.scenarios["scenario2"].dictionary["points"]["point2"],"222+222")        

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[INFO] Model scenario1 was updated!", content)          
        self.assertNotIn("[INFO] Model scenario2 was updated!", content) 

        self.assertEqual(scenarioManager.model_file,"testModelFile")
        self.assertEqual(scenarioManager.source,"testSource")      
        self.assertEqual(scenarioManager.called_instantiate_model,1)   

    def testScenarioManagerSD_add_scenarios(self):
        class TestableTestScenarioManagerSD(ScenarioManagerSd):
            def __init__(self, base_points, base_constants):
                super().__init__(base_points=base_points, base_constants=base_constants,scenarios={})
                self.called_instantiate_model = 0

            def instantiate_model(self):
                self.called_instantiate_model = 1

        scenarioManager = TestableTestScenarioManagerSD(base_constants={ "constant1" : 100.0 , "constant2" : 200.0 }, base_points= { "point1" : "8+8" , "point2" : "9+9" })

        scenarioDictionary = {
            "base": {
            },
            "scenario1" : {
                "constants": {
                    "constant1" : 101.0 
                },
                "points": {
                    "point2" : "19+19"
                }               
            },
            "scenario2" : {
                "constants": {
                    "constant1" : 102.0,
                    "constant2" : 202.0
                },
                "points": {
                    "point1" : "28+28",
                    "point2" : "29+29"
                }               
            }                           
        }

        scenarioManager.add_scenarios(scenario_dictionary=scenarioDictionary)

        self.assertEqual(scenarioManager.scenarios["base"].dictionary["constants"]["constant1"],100.0)
        self.assertEqual(scenarioManager.scenarios["base"].dictionary["constants"]["constant2"],200.0)
        self.assertEqual(scenarioManager.scenarios["base"].dictionary["points"]["point1"],"8+8")
        self.assertEqual(scenarioManager.scenarios["base"].dictionary["points"]["point2"],"9+9")

        self.assertEqual(scenarioManager.scenarios["scenario1"].dictionary["constants"]["constant1"],101.0)
        self.assertEqual(scenarioManager.scenarios["scenario1"].dictionary["constants"]["constant2"],200.0)
        self.assertEqual(scenarioManager.scenarios["scenario1"].dictionary["points"]["point1"],"8+8")
        self.assertEqual(scenarioManager.scenarios["scenario1"].dictionary["points"]["point2"],"19+19")        

        self.assertEqual(scenarioManager.scenarios["scenario2"].dictionary["constants"]["constant1"],102.0)
        self.assertEqual(scenarioManager.scenarios["scenario2"].dictionary["constants"]["constant2"],202.0)
        self.assertEqual(scenarioManager.scenarios["scenario2"].dictionary["points"]["point1"],"28+28")
        self.assertEqual(scenarioManager.scenarios["scenario2"].dictionary["points"]["point2"],"29+29")  

        self.assertEqual(scenarioManager.called_instantiate_model,1) 

    def testScenarioManagerSD_get_cloned_model_none(self):
        scenarioManager = ScenarioManagerSd()

        self.assertIsNone(scenarioManager.get_cloned_model(model=None))      

if __name__ == '__main__':
    unittest.main()   
