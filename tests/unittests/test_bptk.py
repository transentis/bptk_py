import unittest

import BPTK_Py.logger.logger as logmod
from BPTK_Py import bptk
from BPTK_Py.config import config as default_config

class TestBptk(unittest.TestCase):
    def setUp(self):
        pass

    def testBptk_init_with_config(self):
        matplotlib_via_config = {
            "font.family": "Arial",
            "axes.titlesize": 36,
            "axes.labelsize": 26,
            "lines.linewidth": 4,
            "lines.markersize": 16,
            "xtick.labelsize": 16,
            "ytick.labelsize": 16,
            "figure.figsize": (21, 11),
            'legend.fontsize': 18,
        }     

        testbptk1 = bptk(configuration={"interactive": False})
        self.assertEqual(testbptk1.config.matplotlib_rc_settings,default_config.matplotlib_rc_settings)
        self.assertEqual(testbptk1.config.configuration["matplotlib_rc_settings"],default_config.matplotlib_rc_settings)    

        testbptk2 = bptk(configuration={"matplotlib_rc_settings" : matplotlib_via_config, "interactive": False})
        self.assertEqual(testbptk2.config.matplotlib_rc_settings,matplotlib_via_config)
        self.assertEqual(testbptk2.config.configuration["matplotlib_rc_settings"],matplotlib_via_config)
        self.assertFalse(testbptk2.config.configuration["interactive"])
        self.assertEqual(testbptk2.config.loglevel,"WARN")        

        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        testbptk3= bptk(loglevel="DEBUG")

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[ERROR] Invalid log level. Not starting up BPTK-Py! Valid loglevels: ['INFO', 'WARN', 'ERROR']", content) 

    def testBptk_set_state(self):
        testbptk1 = bptk()
        testbptk2 = bptk()

        testbptk1._set_state(state={"testproperty" : "testValue"})
        testbptk2._set_state(state={"lock" : True})

        self.assertEqual(testbptk1.session_state["testproperty"],"testValue")
        self.assertFalse(testbptk1.session_state["lock"])
        self.assertTrue(testbptk2.session_state["lock"])

    def testBptk_is_locked(self):
        testbptk1 = bptk()
        testbptk2 = bptk()
        testbptk2.session_state = {"testproperty" : "testValue"}
        testbptk3 = bptk()
        testbptk3._set_state(state={"lock" : True})

        self.assertFalse(testbptk1.is_locked())
        self.assertFalse(testbptk2.is_locked())
        self.assertTrue(testbptk3.is_locked())

    def testBptk_train_scenario_invalid(self):
        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        testBptk = bptk()

        self.assertIsNone(testBptk._train_scenarios(scenarios=["1"],scenario_managers=["firstManager"],agent_states=["active"]))
        self.assertIsNone(testBptk._train_scenarios(scenarios=["1"],scenario_managers=["firstManager"],agent_properties=["property"]))  
        self.assertIsNone(testBptk._train_scenarios(scenarios=["1"],scenario_managers=["firstManager"],agent_properties=["property"],agent_property_types=[],agents=["agent"]))
        self.assertIsNone(testBptk._train_scenarios(scenarios=["1"],scenario_managers=["firstManager"],agent_properties=[],agent_property_types=["property_type"],agents=["agent"]))

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[ERROR] You may only use the agent_states parameter if you also set the agents parameter!", content)     
        self.assertIn("[ERROR] You may only use the agent_properties parameter if you also set the agents parameter!", content)  
        self.assertIn("[ERROR] No agents given, aborting!", content)  
        self.assertIn("[ERROR] You must set the relevant property types if you specify an agent_property!", content)  
        self.assertIn("[ERROR] You may only use the agent_property_types parameter if you also set the agent_properties parameter!", content)  

    def testBptk_begin_session_errors(self):
        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        testBptk = bptk()

        self.assertIsNone(testBptk.begin_session(scenarios=["1","2","3"],scenario_managers=["firstManager","secondManager"]))
        self.assertIsNone(testBptk.begin_session(scenarios=["1","2","3"],scenario_managers=["firstManager","secondManager"],equations=["stock"],agent_states=["active"]))
        self.assertIsNone(testBptk.begin_session(scenarios=["1","2","3"],scenario_managers=["firstManager","secondManager"],equations=["stock"],individual_agent_properties=["property"]))
        self.assertIsNone(testBptk.begin_session(scenarios=["1","2","3"],scenario_managers=["firstManager","secondManager"],equations=["stock"],agent_properties=["property"]))
        self.assertIsNone(testBptk.begin_session(scenarios=["1","2","3"],scenario_managers=["firstManager","secondManager"],equations=["stock"],agent_properties=["property"],agents=["agent1"]))
        self.assertIsNone(testBptk.begin_session(scenarios=["1","2","3"],scenario_managers=["firstManager","secondManager"],equations=["stock"],agent_property_types=["type"]))
        self.assertIsNone(testBptk.begin_session(scenarios=["1","2","3"],scenario_managers=[],equations=["stock"],agents=["agent1"]))

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[ERROR] start_session: Neither any agents nor equations to simulate given! Aborting!", content)  
        self.assertIn("[ERROR] You may only use the agent_states parameter if you also set the agents parameter!", content)     
        self.assertIn("[ERROR] You may only use the individual_agent_properties parameter if you also set the agents parameter!", content)  
        self.assertIn("[ERROR] You may only use the agent_properties parameter if you also set the agents parameter!", content)  
        self.assertIn("[ERROR] You must set the relevant property types if you specify an agent_property!", content)  
        self.assertIn("[ERROR] You may only use the agent_property_types parameter if you also set the agent_properties parameter!", content)  
        self.assertIn("[ERROR] Did not find any of the scenario manager(s) you specified. Maybe you made a typo or did not store the model in the scenarios folder? Scenario folder:", content)  

    def testBptk_run_step(self):
        testBptk = bptk()

        self.assertIsNone(testBptk.run_step())     

        from BPTK_Py import Model
        model = Model(starttime=0.0,stoptime=1.0,dt=1.0,name='test')
        stock = model.stock("stock")     
        stock.equation = 1.0
        flow = model.flow("flow")
        flow.equation= 2.0
        scenario_manager = {"testManager": {"model": model}}

        testBptk.register_model(model)
        testBptk.register_scenario_manager(scenario_manager)
        testBptk.register_scenarios(scenarios ={"testScenario": {}},scenario_manager="testManager")

        testBptk.begin_session(scenarios=["testScenario"],scenario_managers=["testManager"],equations=["stock"])
        self.assertNotEqual(testBptk.run_step(),{"msg":"Stoptime reached"}) #step 0
        self.assertNotEqual(testBptk.run_step(),{"msg":"Stoptime reached"}) #step 1
        self.assertEqual(testBptk.run_step(),{"msg":"Stoptime reached"}) #step 2

        testBptk2 = bptk()
        testBptk2.register_model(model)
        testBptk2.register_scenario_manager(scenario_manager)
        testBptk2.register_scenarios(scenarios ={"testScenario": {}},scenario_manager="testManager")

        testBptk2.begin_session(scenarios=["testScenario"],scenario_managers=["testManager"],equations=["stock","flow"])
        self.assertEqual(testBptk2.run_step(flat=False),{'testManager': {'testScenario': {'stock': {0.0: 0.0}, 'flow': {0.0: 2.0}}}})
        self.assertEqual(testBptk2.run_step(flat=True),{'testManager': {'testScenario': {'stock': 1.0, 'flow': 2.0}}})

    def testBptk_session_results(self):
        testBptk = bptk()

        self.assertEqual(testBptk.session_results(),{})   

        from BPTK_Py import Model
        model = Model(starttime=0.0,stoptime=15.0,dt=1.0,name='Portfolio')
        totalValue = model.stock("totalValue")
        interest = model.flow("interest")
        deposit = model.flow("deposit")
        interestRate = model.constant("interestRate")
        depositRate = model.constant("depositRate")
        initialValue = model.constant("initialValue")
        interestRate.equation = 0.05
        depositRate.equation = 1000.0
        initialValue.equation = 1000
        totalValue.initial_value = initialValue
        interest.equation = interestRate * totalValue
        deposit.equation = depositRate
        totalValue.equation = interest + deposit 

        scenario_manager = {
            "smPortfolio":{
            "model": model,
            "base_constants": {
                "totalValue": 1000.0,
                "interestRate": 0.05,
                "depositRate": 1000.0
                }
            }
        }          

        testBptk.register_model(model)
        testBptk.register_scenario_manager(scenario_manager)
        testBptk.register_scenarios(
            scenarios ={
                "base": {
                    },
                "scenarrioLowInterest": {
                    "constants": {
                        "interestRate": 0.01
                        }
                    }
            },
            scenario_manager="smPortfolio")        

        testBptk.begin_session(scenarios=["base","scenarrioLowInterest"],scenario_managers=["smPortfolio"],equations=["totalValue","interest"])
        testBptk.run_step()
        testBptk.run_step()
        self.assertEqual(testBptk.session_results(),testBptk.session_state["results_log"])

        result1= testBptk.session_results(index_by_time=False)
        result2= testBptk.session_results(index_by_time=False, flat=True)

        self.assertEqual(result1["smPortfolio"]["base"]["equations"]["totalValue"][0.0],1000)
        self.assertEqual(result1["smPortfolio"]["base"]["equations"]["totalValue"][1.0],2050)
        self.assertEqual(result1["smPortfolio"]["base"]["equations"]["interest"][0.0],50)
        self.assertEqual(result1["smPortfolio"]["base"]["equations"]["interest"][1.0],102.5)
        self.assertEqual(result1["smPortfolio"]["scenarrioLowInterest"]["equations"]["totalValue"][0.0],1000)
        self.assertEqual(result1["smPortfolio"]["scenarrioLowInterest"]["equations"]["totalValue"][1.0],2010)
        self.assertEqual(result1["smPortfolio"]["scenarrioLowInterest"]["equations"]["interest"][0.0],10)
        self.assertEqual(result1["smPortfolio"]["scenarrioLowInterest"]["equations"]["interest"][1.0],20.1)

        self.assertEqual(result2["smPortfolio"]["base"]["equations"]["totalValue"],[1000,2050])
        self.assertEqual(result2["smPortfolio"]["base"]["equations"]["interest"],[50,102.5])
        self.assertEqual(result2["smPortfolio"]["scenarrioLowInterest"]["equations"]["totalValue"],[1000,2010])
        self.assertEqual(result2["smPortfolio"]["scenarrioLowInterest"]["equations"]["interest"],[10,20.1])

    def testBptk_run_scenarios_invalid(self):
        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        testBptk = bptk()

        self.assertIsNone(testBptk.run_scenarios(scenarios=["1","2","3"],scenario_managers=["firstManager","secondManager"]))
        self.assertIsNone(testBptk.run_scenarios(scenarios=["1","2","3"],scenario_managers=["firstManager","secondManager"],equations=["stock"],agent_states=["active"]))
        self.assertIsNone(testBptk.run_scenarios(scenarios=["1","2","3"],scenario_managers=["firstManager","secondManager"],equations=["stock"],agent_properties=["property"]))
        self.assertIsNone(testBptk.run_scenarios(scenarios=["1","2","3"],scenario_managers=["firstManager","secondManager"],equations=["stock"],agent_properties=["property"],agents=["agent1"]))
        self.assertIsNone(testBptk.run_scenarios(scenarios=["1","2","3"],scenario_managers=["firstManager","secondManager"],equations=["stock"],agent_property_types=["type"]))
        self.assertIsNone(testBptk.run_scenarios(scenarios=["1","2","3"],scenario_managers=[],equations=["stock"],agents=["agent1"]))        
        self.assertIsNone(testBptk.run_scenarios(scenarios=["1"], scenario_managers=["firstManager"],equations=["stock"]))

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[ERROR] Neither any agents nor equations to simulate given! Aborting!", content) 
        self.assertIn("[ERROR] You may only use the agent_states parameter if you also set the agents parameter!", content)     
        self.assertIn("[ERROR] You may only use the agent_properties parameter if you also set the agents parameter!", content)  
        self.assertIn("[ERROR] You must set the relevant property types if you specify an agent_property!", content)  
        self.assertIn("[ERROR] You may only use the agent_property_types parameter if you also set the agent_properties parameter!", content)  
        self.assertIn("[ERROR] Did not find any of the scenario manager(s) you specified. Maybe you made a typo or did not store the model in the scenarios folder? Scenario folder:", content)  
        self.assertIn("[ERROR] Scenario manager \"firstManager\" not found!", content)  
        self.assertIn("[ERROR] Scenario \"1\" not found in any scenario manager!", content)  

        from BPTK_Py import Model
        model = Model(starttime=0.0,stoptime=15.0,dt=1.0,name='test')
        stock = model.stock("stock")     
        stock.equation = 1.0
        scenario_manager = {"testManager":{"model": model}}

        testBptk.register_model(model)
        testBptk.register_scenario_manager(scenario_manager)
        testBptk.register_scenarios(scenarios ={"base": {}},scenario_manager="testManager")

        self.assertIsNone(testBptk.run_scenarios(scenarios=["base"], scenario_managers=["testManage"],equations=["stock"]))
        self.assertIsNone(testBptk.run_scenarios(scenarios=["bas"], scenario_managers=["testManager"],equations=["stock"]))

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[ERROR] Scenario manager \"testManage\" not found! Did you maybe mean one of \"testManager", content) 
        self.assertIn("[ERROR] Scenario \"bas\" not found in any scenario manager! Did you maybe mean one of \"base\"?", content) 

    def testBptk_plot_lookup(self):
        from BPTK_Py import Model
        from BPTK_Py import sd_functions as sd
        model = Model(starttime=0.0,stoptime=5.0,dt=1.0,name='test')     
        model.points["testpoints"] = [
            [0, 0.1],
            [0.2, 0.2],
            [0.4, 0.3],
            [0.6, 0.4],
            [0.8, 0.5],
            [1, 0.6]
        ]

        scenario_manager = {"testManager": {"model": model}}

        testBptk = bptk()

        testBptk.register_model(model)
        testBptk.register_scenario_manager(scenario_manager)
        testBptk.register_scenarios(scenarios ={"testScenario": {"points": {"testpoints" : [[0,0.2],[0.2,0.4],[0.4,0.6],[0.6,0.8],[0.8,1.0],[1,1.2]]}}},scenario_manager="testManager")

        data = {
            "smTest_base_testpoints": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            "testManager_testScenario_testpoints": [0.2, 0.4, 0.6, 0.8, 1.0, 1.2]
        } 

        result = testBptk.plot_lookup(scenarios=["base","testScenario"],scenario_managers=["smTest","testManager"], lookup_names="testpoints",return_df=True)

        import pandas as pd
        self.assertTrue(result.equals(pd.DataFrame(data=data, index=[0.0,0.2,0.4,0.6,0.8,1.0])))

    def testBptk_register_scenarios_error(self):
        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        testBptk = bptk()  

        testBptk.register_scenarios(scenarios={},scenario_manager="testScenarioManager")

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[ERROR] Scenario manager not found. Did you register it?", content) 

    def testBptk_list_scenarios(self):
        from BPTK_Py import Model
        model = Model(starttime=0.0,stoptime=15.0,dt=1.0,name='test')
        stock = model.stock("stock")     
        stock.equation = 1.0
        scenario_manager1 = {"testManager1": {"model": model, "type": "type1"}}
        scenario_manager2 = {"testManager2": {"model": model, "type": "type2"}}

        testBptk = bptk()

        testBptk.register_model(model)
        testBptk.register_scenario_manager(scenario_manager1)
        testBptk.register_scenario_manager(scenario_manager2)
        testBptk.register_scenarios(scenarios ={"scenario11": {}, "scenario12": {}},scenario_manager="testManager1")
        testBptk.register_scenarios(scenarios ={"scenario21": {}, "scenario22": {}},scenario_manager="testManager2")

        #Redirect the console output
        import sys, io
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout 

        testBptk.list_scenarios()
        output = new_stdout.getvalue()
        new_stdout.truncate(0)  # reset stdout
        new_stdout.seek(0)
        self.assertIn("*** smTest ***", output)
        self.assertIn("base", output)
        self.assertIn("*** testManager1 ***", output)
        self.assertIn("scenario11", output)
        self.assertIn("scenario12", output)
        self.assertIn("*** testManager2 ***", output)
        self.assertIn("scenario21", output)
        self.assertIn("scenario22", output)

        testBptk.list_scenarios(scenario_managers=["testManager1"])
        output = new_stdout.getvalue()
        self.assertNotIn("*** smTest ***", output)
        self.assertNotIn("base", output)
        self.assertIn("*** testManager1 ***", output)
        self.assertIn("*** testManager1 ***", output)
        self.assertIn("scenario11", output)
        self.assertIn("scenario12", output)
        self.assertNotIn("*** testManager2 ***", output)
        self.assertNotIn("scenario21", output)
        self.assertNotIn("scenario22", output)

        #Remove the redirection of the console output
        sys.stdout = old_stdout

    def testBptk_get_scenario_names_empty(self):
        testBptk = bptk()  

        self.assertEqual(testBptk.get_scenario_names(format="invalid"),[])

    def testBptk_get_scenarios(self):
        from BPTK_Py import Model
        model = Model(starttime=0.0,stoptime=15.0,dt=1.0,name='test')
        stock = model.stock("stock")     
        stock.equation = 1.0
        scenario_manager1 = {"testManager1": {"model": model, "type": "type1"}}
        scenario_manager2 = {"testManager2": {"model": model, "type": "type2"}}

        testBptk = bptk()

        testBptk.register_model(model)
        testBptk.register_scenario_manager(scenario_manager1)
        testBptk.register_scenario_manager(scenario_manager2)
        testBptk.register_scenarios(scenarios ={"scenario11": {}, "scenario12": {}},scenario_manager="testManager1")
        testBptk.register_scenarios(scenarios ={"scenario21": {}, "scenario22": {}},scenario_manager="testManager2")

        result=testBptk.get_scenarios()    

        from BPTK_Py.scenariomanager.scenario import SimulationScenario
        self.assertIsInstance(result["smTest_base"],SimulationScenario)    
        self.assertIsInstance(result["testManager1_scenario11"],SimulationScenario)    
        self.assertIsInstance(result["testManager1_scenario12"],SimulationScenario)    
        self.assertIsInstance(result["testManager2_scenario21"],SimulationScenario)    
        self.assertIsInstance(result["testManager2_scenario22"],SimulationScenario)    

    def testBptk_list_equations(self):
        from BPTK_Py import Model
        model = Model(starttime=0.0,stoptime=15.0,dt=1.0,name='test')
        stock = model.stock("testStock")     
        stock.equation = 1.0
        flow = model.flow("testFlow")
        flow.equation = 2.0
        converter = model.converter("testConverter")
        converter.equation = 3.0
        constant = model.constant("testConstant")
        constant.equation = 4.0

        scenario_manager = {"testManager": {"model": model}}
        testBptk = bptk()
        testBptk.register_model(model)
        testBptk.register_scenario_manager(scenario_manager)       
        testBptk.register_scenarios(scenarios ={"testScenario": {}},scenario_manager="testManager")

        #Redirect the console output
        import sys, io
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout 

        testBptk.list_equations(scenario_managers=["smTest"])
        output = new_stdout.getvalue()
        new_stdout.truncate(0)  # reset stdout
        new_stdout.seek(0)
        self.assertIn("Available Equations", output)
        self.assertIn("Scenario Manager: smTest", output)
        self.assertIn("Scenario: base", output)
        self.assertIn("\tstock: \t\t\ttestStock", output)
        self.assertIn("\tflow: \t\t\ttestFlow", output)
        self.assertIn("\tconverter: \t\ttestConverter", output)
        self.assertIn("\tconstant: \t\ttestConstant", output)
        self.assertNotIn("Scenario Manager: testManager", output)        
        self.assertNotIn("Scenario: testScenario", output)

        testBptk.list_equations(scenario_managers= [], scenarios=["testScenario"])
        output = new_stdout.getvalue()
        self.assertIn("Available Equations", output)
        self.assertIn("Scenario Manager: smTest", output)
        self.assertNotIn("Scenario: base", output)
        self.assertIn("Scenario Manager: testManager", output)
        self.assertIn("Scenario: testScenario", output)
        self.assertIn("\tstock: \t\t\ttestStock", output)
        self.assertIn("\tflow: \t\t\ttestFlow", output)
        self.assertIn("\tconverter: \t\ttestConverter", output)
        self.assertIn("\tconstant: \t\ttestConstant", output)

        #Remove the redirection of the console output
        sys.stdout = old_stdout
        output = new_stdout.getvalue()

    def testBptk_export_scenarios(self):
        from BPTK_Py import Model
        from BPTK_Py import sd_functions as sd
        model = Model(starttime=0.0,stoptime=3.0,dt=1.0,name='test')
        x = model.flow("x")
        testFunction1 = model.function("2times", lambda model, t: 2*(t+1))
        x.equation = testFunction1()
        y = model.flow("y")
        testFunction2 = model.function("3times", lambda model, t: 3*(t+1))
        y.equation = testFunction2()
        
        stock1 = model.stock("stock1")
        initialValue_stock1 = model.constant("initialValue_stock1")
        initialValue_stock1.equation = 1.0
        stock1.initial_value = initialValue_stock1
        stock1.equation = x

        stock2 = model.stock("stock2")
        initialValue_stock2 = model.constant("initialValue_stock2")
        initialValue_stock2.equation = 2.0
        stock2.initial_value = initialValue_stock2
        stock2.equation = y     

        testBptk = bptk()   

        scenario_manager = {
            "testmanager":{
            "model": model,
            "base_constants": {
                "initialValue_stock1": 1.0,
                "initialValue_stock2": 2.0
                }
            }
        }          

        testBptk.register_model(model)
        testBptk.register_scenario_manager(scenario_manager)
        testBptk.register_scenarios(
            scenarios ={
                "highStock1": {
                    "constants": {
                        "initialValue_stock1": 10.0
                    }
                },
                "highStock2": {
                    "constants": {
                        "initialValue_stock2": 20.0
                    }
                },
                "VeryHighStock1": {
                    "constants": {
                        "initialValue_stock1": 100.0
                    }
                },                                
            },
            scenario_manager="testmanager")        

        result1 = testBptk.export_scenarios(scenario_manager="testmanager", scenarios=["highStock1","highStock2"], equations=["stock1","stock2"])
        result2 = testBptk.export_scenarios(scenario_manager="testmanager", scenarios=["highStock1","highStock2"], equations=["stock1","stock2"],
                                        interactive_scenario= "VeryHighStock1",
                                        interactive_equations=["stock1"],
                                        interactive_settings={})
        data_scenario = {
            "stock1": [10.0, 12.0, 16.0, 22.0, 1.0, 3.0, 7.0, 13.0],
            "stock2": [2.0, 5.0, 11.0, 20.0, 20.0, 23.0, 29.0, 38.0],
            "scenario": ["highStock1", "highStock1", "highStock1", "highStock1","highStock2", "highStock2", "highStock2", "highStock2"],
            "time": [0.0, 1.0, 2.0, 3.0, 0.0, 1.0, 2.0, 3.0]
        }

        data_indicator = {
            "highStock1": [10.0, 12.0, 16.0, 22.0, 2.0, 5.0, 11.0, 20.0],
            "highStock2": [1.0, 3.0, 7.0, 13.0, 20.0, 23.0, 29.0, 38.0],
            "indicator": ["stock1", "stock1", "stock1", "stock1","stock2", "stock2", "stock2", "stock2"],
            "time": [0.0, 1.0, 2.0, 3.0, 0.0, 1.0, 2.0, 3.0]            
        }

        data_interactive = {
            "stock1" : [100.0, 102.0, 106.0, 112.0],
            "time" : [0.0, 1.0, 2.0, 3.0]
        }

        import pandas as pd
        self.assertTrue(result1["scenario"].equals(pd.DataFrame(data=data_scenario)))
        self.assertTrue(result1["indicator"].equals(pd.DataFrame(data=data_indicator)))
        self.assertTrue(result1["interactive"].equals(pd.DataFrame()))
        self.assertTrue(result2["interactive"].equals(pd.DataFrame(data=data_interactive)))

if __name__ == '__main__':
    unittest.main()    