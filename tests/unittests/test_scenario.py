import unittest

from BPTK_Py import Model
from BPTK_Py.scenariomanager.scenario import SimulationScenario

class TestScenario(unittest.TestCase):
    def setUp(self):
        pass

    def testScenarioInit(self):
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

        model = Model()
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

    def testScenario_setup_constants(self):
        import BPTK_Py.logger.logger as logmod
        logmod.loglevel="INFO"

        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()        

        dictionary1 = {
            "constants": {
                "constant1": 101.0,
                "constant2": 102.0
            }
        }
        dictionary2 = {
            "constants": {
                "constant1": "103.0",
                "constant2": "104.0"
            }
        }        
        dictionary3 = {
            "constants": {
                "constant1": True,
                "constant2": False
            }
        }  

        scenario1 = SimulationScenario(dictionary=dictionary1,name="scenario1", model=Model(), scenario_manager_name="scenarioManagerName1")
        scenario2 = SimulationScenario(dictionary=dictionary2,name="scenario2", model=Model(), scenario_manager_name="scenarioManagerName2")
        scenario3 = SimulationScenario(dictionary=dictionary3,name="scenario3", model=Model(), scenario_manager_name="scenarioManagerName3")
        scenario4 = SimulationScenario(dictionary={},name="scenario4", model=None, scenario_manager_name="scenarioManagerName4")

        scenario1.setup_constants()

        self.assertEqual(scenario1.model.equations["constant1"](1),101.0)
        self.assertEqual(scenario1.model.equations["constant2"](1),102.0)

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[INFO] scenarioManagerName1, scenario1: Changed constant constant1 to 101.0", content) 
        self.assertIn("[INFO] scenarioManagerName1, scenario1: Changed constant constant2 to 102.0", content) 

        scenario2.setup_constants()

        self.assertEqual(scenario2.model.equations["constant1"](2),103.0)
        self.assertEqual(scenario2.model.equations["constant2"](2),104.0)

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[INFO] scenarioManagerName2, scenario2: Changed constant constant1 to 103.0", content) 
        self.assertIn("[INFO] scenarioManagerName2, scenario2: Changed constant constant2 to 104.0", content)       

        scenario3.setup_constants()

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[ERROR] Invalid type for constant constant1: True", content) 
        self.assertIn("[ERROR] Invalid type for constant constant2: False", content) 

        scenario4.setup_constants()

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[ERROR] Attempted to initialize constants of a model before the model is available for Model scenario4", content)         

    def testScenario_setup_points(self):
        import BPTK_Py.logger.logger as logmod
        logmod.loglevel="INFO"

        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()        

        dictionary1 = {
            "points": {
                "point1" : "1+1",
                "point2" : "2+2"
            }   
        }        
        dictionary2 = {
            "points": {
                "point1" : [
                    [0, 0.1],
                    [1, 0.9]
                ],
                "point2" : [
                    [0.1, 0.2],
                    [0.2, 0.8]
                ],                            
            }
        }     
        dictionary3 = {
            "points": {
                "point1" : True,
                "point2" : False
            }   
        }         

        scenario1 = SimulationScenario(dictionary=dictionary1,name="scenario1", model=Model(), scenario_manager_name="scenarioManagerName1")
        scenario2 = SimulationScenario(dictionary=dictionary2,name="scenario2", model=Model(), scenario_manager_name="scenarioManagerName2")
        scenario3 = SimulationScenario(dictionary=dictionary3,name="scenario3", model=Model(), scenario_manager_name="scenarioManagerName3")
        scenario4 = SimulationScenario(dictionary={},name="scenario4", model=None, scenario_manager_name="scenarioManagerName4")

        scenario1.setup_points()

        self.assertEqual(scenario1.model.points["point1"],2)
        self.assertEqual(scenario1.model.points["point2"],4)

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[INFO] scenarioManagerName1, scenario1: Changed points point1 to 1+1", content)  
        self.assertIn("[INFO] scenarioManagerName1, scenario1: Changed points point2 to 2+2", content)  

        scenario2.setup_points()

        self.assertEqual(scenario2.model.points["point1"],[ [0, 0.1] , [1, 0.9] ])
        self.assertEqual(scenario2.model.points["point2"],[ [0.1, 0.2] , [0.2, 0.8] ])

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[INFO] scenarioManagerName2, scenario2: Changed points point1 to [[0, 0.1], [1, 0.9]]", content)  
        self.assertIn("[INFO] scenarioManagerName2, scenario2: Changed points point2 to [[0.1, 0.2], [0.2, 0.8]]", content) 

        scenario3.setup_points()

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[ERROR] Invalid type for points point1: True", content)          
        self.assertIn("[ERROR] Invalid type for points point2: False", content)          

        scenario4.setup_points()

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[ERROR] Attempted to initialize points of a model before the model is available for ABMModel scenario4", content)         

    def testScenario_set_property_value(self):
        dictionary = {
            "constants": {
                "constant1": 201.0,
                "constant2": 202.0
            }
        }        
        scenario = SimulationScenario(dictionary=dictionary,name="scenario", model=Model(), scenario_manager_name="scenarioManagerName")

        scenario.set_property_value(name="constant1", value=301.0)

        self.assertEqual(scenario.constants["constant1"],301.0)
        self.assertEqual(scenario.constants["constant2"],202.0)

    def testScenario_get_property_vallue(self):
        dictionary = {
            "constants": {
                "constant1": 1201.0,
                "constant2": 1202.0
            }
        }        
        scenario = SimulationScenario(dictionary=dictionary,name="scenario", model=Model(), scenario_manager_name="scenarioManagerName")

        self.assertEqual(scenario.get_property_value(name="constant1"),1201.0)
        self.assertEqual(scenario.get_property_value(name="constant2"),1202.0)                

if __name__ == '__main__':
    unittest.main()        