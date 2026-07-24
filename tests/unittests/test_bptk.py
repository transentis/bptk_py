import io
import sys
import unittest
from unittest import mock

import BPTK_Py
import BPTK_Py.logger.logger as logmod
from BPTK_Py import bptk
from BPTK_Py import Agent, Model
from BPTK_Py.config import config as default_config


class _TrainingAgent(Agent):
    """Minimal agent used to exercise bptk.train_scenarios.

    Models a "learning" agent: each episode it accumulates ``rate`` per
    timestep into the property ``x``. ``begin_episode`` performs a soft reset
    of ``x`` (per-episode state) while ``end_episode`` bumps ``rate`` (the
    persistent, "learned" parameter). This produces a strictly increasing
    per-episode final value - i.e. a deterministic learning curve.
    """

    def __init__(self, agent_id, model, properties):
        super().__init__(agent_id=agent_id, model=model, properties=properties)
        self.agent_type = "learner"
        self.state = "active"
        self.rate = 1
        self.begin_episode_calls = []
        self.end_episode_calls = []
        self._initialize_properties()

    def _initialize_properties(self):
        self.set_property("x", {"type": "Double", "value": 0})

    def act(self, time, round_no, step_no):
        self.x += self.rate

    def begin_episode(self, episode_no):
        self.begin_episode_calls.append(episode_no)
        self.set_property_value("x", 0)  # soft reset of per-episode state

    def end_episode(self, episode_no):
        self.end_episode_calls.append(episode_no)
        self.rate += 1  # the "learned" parameter persists across episodes


class _TrainingModel(Model):
    def instantiate_model(self):
        self.register_agent_factory(
            "learner",
            lambda agent_id, model, properties: _TrainingAgent(agent_id, model, properties),
        )


def _build_training_bptk():
    """Register a single-agent ABM scenario suitable for training."""
    testBptk = bptk()
    model = _TrainingModel(name="trainingModel")
    scenario_manager = {
        "trainManager": {
            "type": "abm",
            "model": model,
            "scenarios": {
                "trainScenario": {
                    "runspecs": {"starttime": 1, "stoptime": 10, "dt": 1},
                    "properties": {},
                    "agents": [{"name": "learner", "count": 1}],
                }
            },
        }
    }
    testBptk.register_scenario_manager(scenario_manager)
    return testBptk


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

    def _build_simple_step_bptk(self, configuration=None):
        """Helper: builds a minimal stock/flow bptk for backend-handling tests.

        Pass ``configuration`` to exercise instance-level config such as
        ``{"default_backend": "rust"}``."""
        from BPTK_Py import Model
        testBptk = bptk(configuration=configuration) if configuration else bptk()
        model = Model(starttime=0.0, stoptime=5.0, dt=1.0, name="rustBackendTest")
        stock = model.stock("stock")
        flow = model.flow("flow")
        constant = model.constant("constant")
        stock.initial_value = 0.0
        stock.equation = flow
        flow.equation = constant
        constant.equation = 1.0
        testBptk.register_model(model)
        testBptk.register_scenario_manager({"testManager": {"model": model}})
        testBptk.register_scenarios(scenarios={"testScenario": {}},
                                    scenario_manager="testManager")
        return testBptk

    def testBptk_begin_session_backend_default_is_python(self):
        """When backend is not specified, session_state must record python."""
        testBptk = self._build_simple_step_bptk()
        testBptk.begin_session(scenarios=["testScenario"],
                               scenario_managers=["testManager"],
                               equations=["stock"])
        self.assertEqual(testBptk.session_state["backend"], "python")
        testBptk.end_session()

    def testBptk_begin_session_backend_explicit_python(self):
        testBptk = self._build_simple_step_bptk()
        testBptk.begin_session(scenarios=["testScenario"],
                               scenario_managers=["testManager"],
                               equations=["stock"], backend="python")
        self.assertEqual(testBptk.session_state["backend"], "python")
        testBptk.end_session()

    def testBptk_begin_session_backend_explicit_rust(self):
        testBptk = self._build_simple_step_bptk()
        testBptk.begin_session(scenarios=["testScenario"],
                               scenario_managers=["testManager"],
                               equations=["stock"], backend="rust")
        self.assertEqual(testBptk.session_state["backend"], "rust")
        testBptk.end_session()

    def testBptk_begin_session_backend_invalid_falls_back(self):
        """Invalid backend strings must log an [ERROR] and fall back to python."""
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        testBptk = self._build_simple_step_bptk()
        testBptk.begin_session(scenarios=["testScenario"],
                               scenario_managers=["testManager"],
                               equations=["stock"], backend="bogus")
        self.assertEqual(testBptk.session_state["backend"], "python")

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()
        self.assertIn("[ERROR] begin_session: invalid backend 'bogus'", content)
        testBptk.end_session()

    def testBptk_begin_session_backend_none_uses_default(self):
        """backend=None (the default) resolves to the instance default_backend,
        which is 'python' for an unconfigured instance."""
        testBptk = self._build_simple_step_bptk()
        self.assertEqual(testBptk.default_backend, "python")
        testBptk.begin_session(scenarios=["testScenario"],
                               scenario_managers=["testManager"],
                               equations=["stock"], backend=None)
        self.assertEqual(testBptk.session_state["backend"], "python")
        testBptk.end_session()

    def testBptk_default_backend_rust_used_when_backend_omitted(self):
        """Substep 4i: a bptk configured with default_backend='rust' runs sessions
        on Rust when begin_session omits the backend argument; an explicit backend
        still overrides the instance default."""
        testBptk = self._build_simple_step_bptk(
            configuration={"default_backend": "rust", "interactive": False})
        self.assertEqual(testBptk.default_backend, "rust")

        # Omitted backend ⇒ inherits the 'rust' instance default.
        testBptk.begin_session(scenarios=["testScenario"],
                               scenario_managers=["testManager"],
                               equations=["stock"])
        self.assertEqual(testBptk.session_state["backend"], "rust")
        testBptk.end_session()

        # Explicit 'python' overrides the 'rust' instance default.
        testBptk.begin_session(scenarios=["testScenario"],
                               scenario_managers=["testManager"],
                               equations=["stock"], backend="python")
        self.assertEqual(testBptk.session_state["backend"], "python")
        testBptk.end_session()

    def testBptk_default_backend_invalid_config_falls_back(self):
        """An invalid default_backend in the configuration logs an [ERROR] and
        leaves the instance default at 'python'."""
        testBptk = self._build_simple_step_bptk(
            configuration={"default_backend": "bogus", "interactive": False})
        self.assertEqual(testBptk.default_backend, "python")

    def testBptk_end_session_clears_rust_state(self):
        """After end_session, the four Rust fields populated mid-session must
        all be reset on the underlying SimulationScenario."""
        testBptk = self._build_simple_step_bptk()
        testBptk.begin_session(scenarios=["testScenario"],
                               scenario_managers=["testManager"],
                               equations=["stock", "flow"], backend="rust")
        testBptk.run_step()

        sc = testBptk.scenario_manager_factory.get_scenario(
            scenario_manager="testManager", scenario="testScenario")
        # Sanity: mid-session, the Rust state is populated.
        self.assertIsNotNone(sc.rust_model)
        self.assertIsNotNone(sc._rust_initial)
        self.assertTrue(sc._rust_initial_returned)

        testBptk.end_session()

        self.assertIsNone(sc.rust_model)
        self.assertIsNone(sc._rust_initial)
        self.assertFalse(sc._rust_initial_returned)
        self.assertFalse(sc._rust_failed)
        self.assertIsNone(testBptk.session_state)

    def testBptk_end_session_python_session_no_rust_state(self):
        """A python-backed session must never populate the Rust fields, and
        end_session must leave them at their defaults."""
        testBptk = self._build_simple_step_bptk()
        testBptk.begin_session(scenarios=["testScenario"],
                               scenario_managers=["testManager"],
                               equations=["stock"], backend="python")
        testBptk.run_step()
        sc = testBptk.scenario_manager_factory.get_scenario(
            scenario_manager="testManager", scenario="testScenario")
        self.assertIsNone(sc.rust_model)
        self.assertIsNotNone(sc.sd_simulation)

        testBptk.end_session()

        self.assertIsNone(sc.rust_model)
        self.assertFalse(sc._rust_initial_returned)
        self.assertFalse(sc._rust_failed)

    def testBptk_end_session_reset_exception_swallowed(self):
        """If rust_model.reset() raises, end_session must still complete and
        leave the scenario in a clean state. The real RustSdModel.reset() is a
        Rust-defined attribute and can't be monkeypatched, so we swap the
        rust_model handle out for a MagicMock whose reset() raises."""
        testBptk = self._build_simple_step_bptk()
        testBptk.begin_session(scenarios=["testScenario"],
                               scenario_managers=["testManager"],
                               equations=["stock"], backend="rust")
        testBptk.run_step()
        sc = testBptk.scenario_manager_factory.get_scenario(
            scenario_manager="testManager", scenario="testScenario")

        # Replace the real Rust handle with a MagicMock whose reset() raises.
        sc.rust_model = mock.MagicMock()
        sc.rust_model.reset.side_effect = RuntimeError("simulated boom")

        testBptk.end_session()  # must not raise

        self.assertIsNone(sc.rust_model)
        self.assertIsNone(testBptk.session_state)

    def testBptk_run_step_passes_backend_to_runner(self):
        """run_step must forward session_state['backend'] to SdRunner.run_scenario_step."""
        from BPTK_Py.scenariorunners.sd_runner import SdRunner
        testBptk = self._build_simple_step_bptk()
        testBptk.begin_session(scenarios=["testScenario"],
                               scenario_managers=["testManager"],
                               equations=["stock", "flow"], backend="rust")
        with mock.patch.object(SdRunner, "run_scenario_step",
                               wraps=SdRunner.run_scenario_step,
                               autospec=True) as mock_run:
            testBptk.run_step()
            self.assertTrue(mock_run.called)
            self.assertEqual(mock_run.call_args.kwargs["backend"], "rust")
        testBptk.end_session()

    def testBptk_run_step_defaults_to_python_when_backend_missing(self):
        """Sessions reconstructed from external state may not carry the
        'backend' key; run_step must default to python rather than KeyError."""
        from BPTK_Py.scenariorunners.sd_runner import SdRunner
        testBptk = self._build_simple_step_bptk()
        testBptk.begin_session(scenarios=["testScenario"],
                               scenario_managers=["testManager"],
                               equations=["stock"])
        del testBptk.session_state["backend"]

        with mock.patch.object(SdRunner, "run_scenario_step",
                               wraps=SdRunner.run_scenario_step,
                               autospec=True) as mock_run:
            testBptk.run_step()
            self.assertEqual(mock_run.call_args.kwargs["backend"], "python")
        testBptk.end_session()

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

    def _capture_stdout(self, fn, *args, **kwargs):
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            fn(*args, **kwargs)
            return sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

    def testBptk_update_already_latest(self):
        """bptk.update() prints 'up to date' when local version matches PyPI."""
        fake_index = mock.Mock()
        fake_index.search.return_value = [
            {"name": "BPTK-Py", "version": BPTK_Py.__version__}
        ]

        with mock.patch("distlib.index.PackageIndex", return_value=fake_index):
            output = self._capture_stdout(bptk.update)

        self.assertIn("Nothing to do", output)
        self.assertIn(BPTK_Py.__version__, output)

    def testBptk_update_installs_newer_version_terminal(self):
        """bptk.update() pip-installs when PyPI advertises a newer version (terminal flow, no notebook hint)."""
        newer = "999.0.0"
        fake_index = mock.Mock()
        fake_index.search.return_value = [
            {"name": "Other-Package", "version": "0.0.1"},
            {"name": "BPTK-Py", "version": newer},
        ]

        with mock.patch("distlib.index.PackageIndex", return_value=fake_index), \
             mock.patch("subprocess.check_call", return_value=0) as check_call, \
             mock.patch("builtins.get_ipython", create=True, side_effect=NameError):
            output = self._capture_stdout(bptk.update)

        check_call.assert_called_once()
        called_args = check_call.call_args[0][0]
        self.assertIn("pip", called_args)
        self.assertIn("BPTK-Py", called_args)
        self.assertIn("Update successfully completed", output)
        self.assertNotIn("Jupyter Notebook", output)

    def testBptk_update_pip_failure(self):
        """bptk.update() prints an error when pip returns a non-zero exit code."""
        newer = "999.0.0"
        fake_index = mock.Mock()
        fake_index.search.return_value = [{"name": "BPTK-Py", "version": newer}]

        with mock.patch("distlib.index.PackageIndex", return_value=fake_index), \
             mock.patch("subprocess.check_call", return_value=1), \
             mock.patch("builtins.get_ipython", create=True, side_effect=NameError):
            output = self._capture_stdout(bptk.update)

        self.assertIn("Error Updating", output)

    def testBptk_update_notebook_hint(self):
        """bptk.update() suggests a kernel restart when running inside a Jupyter notebook shell."""
        newer = "999.0.0"
        fake_index = mock.Mock()
        fake_index.search.return_value = [{"name": "BPTK-Py", "version": newer}]

        fake_shell = mock.Mock()
        fake_shell.__class__.__name__ = "ZMQInteractiveShell"
        fake_ipython = mock.Mock(return_value=fake_shell)

        with mock.patch("distlib.index.PackageIndex", return_value=fake_index), \
             mock.patch("subprocess.check_call", return_value=0), \
             mock.patch("builtins.get_ipython", create=True, return_value=fake_shell):
            output = self._capture_stdout(bptk.update)

        self.assertIn("Update successfully completed", output)
        # Notebook detection branch — isnotebook() returns True for ZMQInteractiveShell.
        self.assertIn("Jupyter Notebook", output)

    def _capture_stdout(self, fn, *args, **kwargs):
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            fn(*args, **kwargs)
            return sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

    def testBptk_version_is_resolved(self):
        """BPTK_Py.__version__ resolves to a real version string, not the 'UNAVAILABLE' fallback."""
        self.assertNotEqual(BPTK_Py.__version__, "UNAVAILABLE")
        # Version must be a dotted numeric string that distlib can compare.
        from distlib.version import NormalizedVersion
        NormalizedVersion(BPTK_Py.__version__)

    def testBptk_update_already_latest(self):
        """bptk.update() prints 'up to date' when the local version matches PyPI."""
        fake_index = mock.Mock()
        fake_index.search.return_value = [
            {"name": "BPTK-Py", "version": BPTK_Py.__version__}
        ]

        with mock.patch("distlib.index.PackageIndex", return_value=fake_index):
            output = self._capture_stdout(bptk.update)

        self.assertIn("Nothing to do", output)
        self.assertIn(BPTK_Py.__version__, output)

    def testBptk_update_installs_newer_version_terminal(self):
        """bptk.update() pip-installs when PyPI advertises a newer version (terminal flow, no notebook hint)."""
        fake_index = mock.Mock()
        fake_index.search.return_value = [
            {"name": "Other-Package", "version": "0.0.1"},
            {"name": "BPTK-Py", "version": "999.0.0"},
        ]

        with mock.patch("distlib.index.PackageIndex", return_value=fake_index), \
             mock.patch.object(BPTK_Py, "__version__", "1.0.0"), \
             mock.patch("subprocess.check_call", return_value=0) as check_call, \
             mock.patch("builtins.get_ipython", create=True, side_effect=NameError):
            output = self._capture_stdout(bptk.update)

        check_call.assert_called_once()
        called_args = check_call.call_args[0][0]
        self.assertIn("pip", called_args)
        self.assertIn("BPTK-Py", called_args)
        self.assertIn("Update successfully completed", output)
        self.assertNotIn("Jupyter Notebook", output)

    def testBptk_update_pip_failure(self):
        """bptk.update() prints an error when pip returns a non-zero exit code."""
        fake_index = mock.Mock()
        fake_index.search.return_value = [{"name": "BPTK-Py", "version": "999.0.0"}]

        with mock.patch("distlib.index.PackageIndex", return_value=fake_index), \
             mock.patch.object(BPTK_Py, "__version__", "1.0.0"), \
             mock.patch("subprocess.check_call", return_value=1), \
             mock.patch("builtins.get_ipython", create=True, side_effect=NameError):
            output = self._capture_stdout(bptk.update)

        self.assertIn("Error Updating", output)

    def testBptk_update_notebook_hint(self):
        """bptk.update() suggests a kernel restart when running inside a Jupyter notebook shell."""
        fake_index = mock.Mock()
        fake_index.search.return_value = [{"name": "BPTK-Py", "version": "999.0.0"}]

        # isnotebook() inspects get_ipython().__class__.__name__ — fake a ZMQInteractiveShell instance.
        class ZMQInteractiveShell:
            pass

        with mock.patch("distlib.index.PackageIndex", return_value=fake_index), \
             mock.patch.object(BPTK_Py, "__version__", "1.0.0"), \
             mock.patch("subprocess.check_call", return_value=0), \
             mock.patch("builtins.get_ipython", create=True,
                        return_value=ZMQInteractiveShell()):
            output = self._capture_stdout(bptk.update)

        self.assertIn("Update successfully completed", output)
        self.assertIn("Jupyter Notebook", output)

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

    def testBptk_train_scenarios_learning_curve(self):
        """train_scenarios runs an ABM over episodes and returns one row per
        episode holding the episode's final value (collect_data=False path)."""
        import pandas as pd

        testBptk = _build_training_bptk()
        episodes = 3

        df = testBptk.train_scenarios(
            scenarios=["trainScenario"],
            scenario_managers=["trainManager"],
            episodes=episodes,
            agents=["learner"],
            agent_states=["active"],
            agent_properties=["x"],
            agent_property_types=["total"],
            return_df=True,
        )

        self.assertIsInstance(df, pd.DataFrame)
        # one row per episode
        self.assertEqual(len(df), episodes)

        column_name = "learner_active_x_total"
        self.assertIn(column_name, df.columns)

        # rate is 1, 2, 3 across the three episodes; over 10 timesteps the
        # per-episode final value is 10, 20, 30 - a strictly rising curve.
        #
        # These three values alone prove both episode hooks fired correctly:
        #  - if begin_episode had NOT soft-reset x, it would accumulate across
        #    episodes (ep1 -> 30 instead of 20);
        #  - if end_episode had NOT bumped rate, every episode would yield 10.
        self.assertEqual(list(df[column_name]), [10.0, 20.0, 30.0])

        testBptk.destroy()

    def testBptk_train_scenarios_no_agents_returns_none(self):
        """Without agents there is nothing to train, so None is returned."""
        testBptk = _build_training_bptk()

        result = testBptk.train_scenarios(
            scenarios=["trainScenario"],
            scenario_managers=["trainManager"],
            episodes=2,
            agents=[],
            return_df=True,
        )

        self.assertIsNone(result)
        testBptk.destroy()

    def testBptk_train_scenarios_accepts_comma_separated_strings(self):
        """Scenario/manager/agent args may be passed as comma-separated strings."""
        import pandas as pd

        testBptk = _build_training_bptk()

        df = testBptk.train_scenarios(
            scenarios="trainScenario",
            scenario_managers="trainManager",
            episodes=1,
            agents="learner",
            agent_states=["active"],
            agent_properties=["x"],
            agent_property_types=["total"],
            return_df=True,
        )

        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 1)
        column_name = "learner_active_x_total"
        self.assertEqual(list(df[column_name]), [10.0])
        testBptk.destroy()

    def testBptk_train_scenarios_multiple_managers_join(self):
        """Training across two managers joins their per-episode result frames."""
        import pandas as pd

        testBptk = _build_training_bptk()
        # register a second, independent ABM manager
        testBptk.register_scenario_manager({
            "trainManager2": {
                "type": "abm",
                "model": _TrainingModel(name="trainingModel2"),
                "scenarios": {
                    "trainScenario": {
                        "runspecs": {"starttime": 1, "stoptime": 10, "dt": 1},
                        "properties": {},
                        "agents": [{"name": "learner", "count": 1}],
                    }
                },
            }
        })

        df = testBptk.train_scenarios(
            scenarios=["trainScenario"],
            scenario_managers=["trainManager", "trainManager2"],
            episodes=2,
            agents=["learner"],
            agent_states=["active"],
            agent_properties=["x"],
            agent_property_types=["total"],
            return_df=True,
        )

        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)  # two episodes
        # with two managers the series names keep their full prefix
        col1 = "trainManager_trainScenario_learner_active_x_total"
        col2 = "trainManager2_trainScenario_learner_active_x_total"
        self.assertIn(col1, df.columns)
        self.assertIn(col2, df.columns)
        self.assertEqual(list(df[col1]), [10.0, 20.0])
        self.assertEqual(list(df[col2]), [10.0, 20.0])
        testBptk.destroy()


    # ------------------------------------------------------------------
    # bptk.py coverage: config, isnotebook shell branches, init branches,
    # progress-bar training, lookup/reset/register/export.
    # ------------------------------------------------------------------

    def testBptk_conf_preserves_slider_layout(self):
        """A non-None slider_layout survives the deepcopy (it is popped and restored)."""
        from BPTK_Py.bptk import conf
        from BPTK_Py.config import config as default_config
        sentinel = {"widget": "layout"}
        default_config.configuration["slider_layout"] = sentinel
        try:
            self.assertEqual(conf().configuration["slider_layout"], sentinel)
        finally:
            default_config.configuration.pop("slider_layout", None)

    def _run_update_with_shell(self, shell_name):
        fake_shell = mock.Mock()
        fake_shell.__class__.__name__ = shell_name
        fake_index = mock.Mock()
        fake_index.search.return_value = [{"name": "BPTK-Py", "version": "999.0.0"}]
        with mock.patch("distlib.index.PackageIndex", return_value=fake_index), \
             mock.patch("subprocess.check_call", return_value=0), \
             mock.patch("builtins.get_ipython", create=True, return_value=fake_shell):
            return self._capture_stdout(bptk.update)

    def testBptk_update_terminal_shell(self):
        """isnotebook() returns False for a TerminalInteractiveShell — no notebook hint."""
        output = self._run_update_with_shell("TerminalInteractiveShell")
        self.assertIn("Update successfully completed", output)
        self.assertNotIn("Jupyter Notebook", output)

    def testBptk_update_other_shell(self):
        """isnotebook() returns False for any other shell class — no notebook hint."""
        output = self._run_update_with_shell("SomeOtherShell")
        self.assertIn("Update successfully completed", output)
        self.assertNotIn("Jupyter Notebook", output)

    def testBptk_init_configures_logfire(self):
        """A logfire_config dict triggers configure_logfire during init."""
        import BPTK_Py.logger.logger as logmod2
        with mock.patch.object(logmod2, "configure_logfire", return_value=True) as cfg:
            bptk(configuration={"logfire_config": {"token": "x"}})
        cfg.assert_called_once()

    def testBptk_init_logfire_failure_is_caught(self):
        """A failure while configuring logfire is caught, not raised."""
        import BPTK_Py.logger.logger as logmod2
        with mock.patch.object(logmod2, "configure_logfire", side_effect=RuntimeError("boom")):
            testBptk = bptk(configuration={"logfire_config": {"token": "x"}})
        self.assertIsNotNone(testBptk)

    def testBptk_init_appends_scenario_base_path_to_syspath(self):
        """The parent of the scenario storage path is added to sys.path if absent."""
        import sys, tempfile, os
        from pathlib import Path
        tmp = tempfile.TemporaryDirectory()
        storage = os.path.join(tmp.name, "myproject", "scenarios")
        os.makedirs(storage)
        # bptk resolves the path first, so compare against the resolved parent.
        base_path = str(Path(storage).resolve().parent)  # .../myproject
        self.assertNotIn(base_path, sys.path)
        try:
            bptk(configuration={"scenario_storage": storage})
            self.assertIn(base_path, sys.path)
        finally:
            if base_path in sys.path:
                sys.path.remove(base_path)
            tmp.cleanup()

    def testBptk_train_scenarios_progress_bar(self):
        """train_scenarios with progress_bar=True runs training on a worker thread
        while updating a FloatProgress widget."""
        testBptk = _build_training_bptk()
        # return_df=True keeps the worker thread off the GUI plotting path (the
        # macOS matplotlib backend must not be driven from a non-main thread).
        # The progress_bar branch itself returns None regardless.
        result = testBptk.train_scenarios(
            scenarios=["trainScenario"],
            scenario_managers=["trainManager"],
            episodes=2,
            agents=["learner"],
            agent_states=["active"],
            agent_properties=["x"],
            agent_property_types=["total"],
            return_df=True,
            progress_bar=True,
        )
        self.assertIsNone(result)
        testBptk.destroy()

    def testBptk_plot_lookup_single_scenario(self):
        """plot_lookup with a single lookup source hits the single-dataframe branch."""
        from BPTK_Py import Model
        import pandas as pd
        model = Model(starttime=0.0, stoptime=5.0, dt=1.0, name="lk")
        model.points["testpoints"] = [[0, 0.1], [1, 0.6]]
        testBptk = bptk()
        testBptk.register_scenario_manager({"lkManager": {"model": model}})
        testBptk.register_scenarios(scenarios={"base": {}}, scenario_manager="lkManager")

        result = testBptk.plot_lookup(scenarios=["base"], scenario_managers=["lkManager"],
                                      lookup_names="testpoints", return_df=True)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result.columns), 1)

    def testBptk_reset_scenario_delegates_to_factory(self):
        """reset_scenario and reset_all_scenarios delegate to the factory."""
        testBptk = bptk()
        with mock.patch.object(testBptk.scenario_manager_factory, "reset_scenario") as reset_one:
            testBptk.reset_scenario(scenario_manager="m", scenario="s")
        reset_one.assert_called_once_with(scenario_manager="m", scenario="s")

        with mock.patch.object(testBptk.scenario_manager_factory, "reset_all_scenarios") as reset_all:
            testBptk.reset_all_scenarios()
        reset_all.assert_called_once()

    def testBptk_register_model_from_source_path(self):
        """register_model with a filesystem path registers a manager pointing at that source."""
        import tempfile, os
        tmp = tempfile.NamedTemporaryFile(suffix=".itmx", delete=False)
        tmp.write(b"<xmile></xmile>")
        tmp.close()
        try:
            testBptk = bptk()
            # Stub register_scenarios so we don't XMILE-compile the dummy source;
            # we only care that the path branch registers the manager + prints.
            with mock.patch.object(testBptk, "register_scenarios"):
                output = self._capture_stdout(
                    testBptk.register_model, tmp.name, "SourcedManager")
            self.assertIn("Successfully registered", output)
            self.assertIn("SourcedManager", testBptk.scenario_manager_factory.scenario_managers)
        finally:
            os.unlink(tmp.name)

    def testBptk_export_scenarios_defaults_interactive_and_file(self):
        """export_scenarios: default (all) scenarios, non-empty interactive settings,
        and writing to a spreadsheet file."""
        from BPTK_Py import Model
        import tempfile, os
        model = Model(starttime=0.0, stoptime=2.0, dt=1.0, name="exp")
        stock = model.stock("stock")
        rate = model.constant("rate")
        rate.equation = 1.0
        stock.initial_value = 0.0
        stock.equation = rate

        testBptk = bptk()
        testBptk.register_scenario_manager({"expManager": {"model": model, "base_constants": {"rate": 1.0}}})
        testBptk.register_scenarios(
            scenarios={"base": {}, "fast": {"constants": {"rate": 2.0}}},
            scenario_manager="expManager")

        # No `scenarios` argument -> all scenario names are looked up.
        result = testBptk.export_scenarios(scenario_manager="expManager", equations=["stock"])
        self.assertIn("scenario", result)

        # Non-empty interactive settings exercise the per-setting property assignment.
        result_i = testBptk.export_scenarios(
            scenario_manager="expManager", scenarios=["base"], equations=["stock"],
            interactive_scenario="base", interactive_equations=["stock"],
            interactive_settings={"rate": [1.0, 3.0, 1.0]})
        self.assertFalse(result_i["interactive"].empty)
        self.assertIn("rate", result_i["interactive"].columns)

        # A filename triggers the spreadsheet-export branch (openpyxl is not a
        # dependency here, so the writer and to_excel are stubbed out).
        tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        tmp.close()
        try:
            with mock.patch("pandas.ExcelWriter"), mock.patch("pandas.DataFrame.to_excel"):
                ret = testBptk.export_scenarios(scenario_manager="expManager", scenarios=["base"],
                                                equations=["stock"], filename=tmp.name)
            self.assertIsNone(ret)
        finally:
            os.unlink(tmp.name)

    def testBptk_register_model_from_source_requires_name(self):
        """register_model from a path without a manager name logs an error and aborts."""
        import tempfile, os
        tmp = tempfile.NamedTemporaryFile(suffix=".itmx", delete=False)
        tmp.close()
        try:
            with open(logmod.logfile, "w", encoding="UTF-8"):
                pass
            testBptk = bptk()
            testBptk.register_model(tmp.name)  # no scenario_manager name
            with open(logmod.logfile, "r", encoding="UTF-8") as f:
                content = f.read()
            self.assertIn("[ERROR] Please define a name for the new scenario manager", content)
        finally:
            os.unlink(tmp.name)

if __name__ == '__main__':
    unittest.main()