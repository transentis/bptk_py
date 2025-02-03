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

    def testBptk_run_scenarios(self):
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

if __name__ == '__main__':
    unittest.main()    