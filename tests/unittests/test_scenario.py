import unittest

from BPTK_Py import Model
from BPTK_Py.scenariomanager.scenario import SimulationScenario

class TestScenario(unittest.TestCase):
    def setUp(self):
        pass

    def testScenarioInit(self):
        model = Model()
        dictionary = {
            "constants": {
                "constant1": 1.0,
                "constant2": 2.0
            },
            "points": {
                "point1" : 
                       [
                           [0, 0.1],
                           [1, 0.9]
                       ],
                "point2" :
                        [
                           [1, 0.2],
                           [2, 0.8]
                        ]              
            },
            "runspecs": {
                "starttime": 1.0,
                "stoptime": 2.0,
                "dt": 3.0

            }
        }

        emptyScenario = SimulationScenario(dictionary={},name="emptyScenario", model=None, scenario_manager_name="scenarioManagerName1")

        self.assertEqual(emptyScenario.dictionary,{})
        self.assertEqual(emptyScenario.scenario_manager,"scenarioManagerName1")
        self.assertIsNone(emptyScenario.model)
        self.assertIsNone(emptyScenario.sd_simulation)
        self.assertEqual(emptyScenario.stoptime,0.0)
        self.assertEqual(emptyScenario.starttime,0.0)
        self.assertEqual(emptyScenario.dt,0.0)
        self.assertEqual(emptyScenario.constants,{})
        self.assertEqual(emptyScenario.points,{})
        self.assertEqual(emptyScenario.name,"emptyScenario")
        self.assertIsNone(emptyScenario.result)

        scenario = SimulationScenario(dictionary=dictionary,name="scenario", model=model, scenario_manager_name="scenarioManagerName2")

        self.assertEqual(scenario.dictionary,dictionary)
        self.assertEqual(scenario.scenario_manager,"scenarioManagerName2")
        self.assertEqual(scenario.model,model)
        self.assertIsNone(scenario.sd_simulation)
        self.assertEqual(scenario.stoptime,2.0)
        self.assertEqual(scenario.starttime,1.0)
        self.assertEqual(scenario.dt,3.0)
        self.assertEqual(scenario.constants,{ "constant1": 1.0, "constant2": 2.0 })
        self.assertEqual(scenario.points,{ "point1" :  [  [0, 0.1] , [1, 0.9] ] , "point2" : [  [1, 0.2] , [2, 0.8] ] })
        self.assertEqual(scenario.model.points,{ "point1" :  [  [0, 0.1] , [1, 0.9] ] , "point2" : [  [1, 0.2] , [2, 0.8] ] })
        self.assertEqual(scenario.name,"scenario")
        self.assertIsNone(scenario.result)

    def testScenario_configure_settings(self):
        dictionary = {
            "constants": {
                "constant1": 3.0,
                "constant2": 4.0
            },
            "points": {
                "point1" : 
                       [
                           [0.1, 0.1],
                           [1.1, 0.9]
                       ],
                "point2" :
                        [
                           [1.1, 0.2],
                           [2.1, 0.8]
                        ]              
            },
            "runspecs": {
                "starttime": 11.0,
                "stoptime": 12.0,
                "dt": 13.0

            }
        }

        scenario = SimulationScenario(dictionary={},name="scenario", model=None, scenario_manager_name="scenarioManagerName")        

        scenario.configure_settings(dictionary=dictionary)

        self.assertEqual(scenario.stoptime,12.0)
        self.assertEqual(scenario.starttime,11.0)
        self.assertEqual(scenario.dt,13.0)
        self.assertEqual(scenario.constants,{ "constant1": 3.0, "constant2": 4.0 })
        self.assertEqual(scenario.points,{ "point1" :  [  [0.1, 0.1] , [1.1, 0.9] ] , "point2" : [  [1.1, 0.2] , [2.1, 0.8] ] })

if __name__ == '__main__':
    unittest.main()        