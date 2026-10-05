import pytest
import threading
import unittest

import BPTK_Py
from BPTK_Py import Model, Agent, Event, DataCollector, CyclicDependencyError
from BPTK_Py import sd_functions as sd
from BPTK_Py.util.lookup_data import lookup_data, lookup_points
from tests.helpers.log_helpers import clear_log, read_log

class Test_Model(unittest.TestCase):
    def test_set_scenario_manager(self):
        model = Model()

        valid_scenario_manager = "1"
        invalid_scenario_manager = 1

        self.assertRaises(ValueError,model.set_scenario_manager,scenario_manager=invalid_scenario_manager)

        model.set_scenario_manager(valid_scenario_manager)
        self.assertEqual(model.scenario_manager,valid_scenario_manager)

        self.assertEqual(model.model,model)
        self.assertEqual(id(model),id(model))


    def test_run_step_with_a_progress_bar(self):
        """`show_progress_widget=True` was the only branch of run_step nobody ran.

        Until 3.0.0 it built an ipywidgets FloatProgress and therefore only worked in
        Jupyter, which is presumably why no test touched it. It is tqdm now and runs
        anywhere, so there is no reason left not to.
        """
        from BPTK_Py import SimultaneousScheduler

        model = Model(starttime=0.0, stoptime=2.0, dt=1.0, name="progressModel",
                      scheduler=SimultaneousScheduler())

        with_bar = model.run_step(1, show_progress_widget=True)
        without_bar = model.run_step(2, show_progress_widget=False)

        self.assertEqual(with_bar, without_bar)

    def test_register_agent_factory(self):
        model = Model()

        func = lambda  x : 1
        invalid_agent_type = 1
        valid_agent_type = "1"

        self.assertRaises(ValueError,model.register_agent_factory,agent_type=invalid_agent_type,agent_factory=func)

        model.register_agent_factory(agent_factory=func,agent_type=valid_agent_type)

        self.assertEqual(model.agent_factories[valid_agent_type],func)

    def test_reset(self):
        model = Model()

        model.reset()

        func = lambda agent_id, model, properties: Agent(agent_id=agent_id,model=model,properties=properties)
        model.register_agent_factory(agent_factory=func,agent_type="testType")
        model.create_agent(agent_type="testType",agent_properties={"name": {"type" : "String", "value": "testAgent"}}) 

        dataCollector = DataCollector()
        model.data_collector = dataCollector
        event= Event(name="eventName", sender_id=1, receiver_id=2)
        model.data_collector.record_event(time=101,event=event)
        model.data_collector.collect_agent_statistics(time=201,agents=model.agents)

        model.reset()

        self.assertEqual(model.agent_type_map,{'testType': []})
        self.assertEqual(model.agents,[])
        self.assertEqual(model.data_collector.agent_statistics,{})
        self.assertEqual(model.data_collector.event_statistics,{})

    def test_reset_restarts_the_agent_ids(self):
        """A reconfigured model must hand out ids that index into its own agent list.

        The docstring of `reset` promises that the factories survive so the model can be
        reconfigured - and until 3.0.2 the id counter survived too, so the next agent got
        id 10 while `agents` was a fresh list of ten. Anything indexing by receiver_id -
        the simultaneous scheduler does - then raised IndexError.
        """
        model = Model()
        model.register_agent_factory(
            agent_factory=lambda agent_id, model, properties: Agent(
                agent_id=agent_id, model=model, properties=properties
            ),
            agent_type="testType",
        )
        for _ in range(10):
            model.create_agent(agent_type="testType", agent_properties={})
        self.assertEqual([a.id for a in model.agents], list(range(10)))

        model.reset()
        for _ in range(10):
            model.create_agent(agent_type="testType", agent_properties={})

        self.assertEqual([a.id for a in model.agents], list(range(10)))
        # The point of it: every id is a valid index into the new list.
        for agent in model.agents:
            self.assertIs(model.agents[agent.id], agent)

    def test_configuring_again_restarts_the_ids_and_drops_the_old_events(self):
        """A model configured and run a second time - a notebook cell run again - raised
        IndexError: `configure_agents` kept the id counter, and the events left over from
        the first run were addressed to agents that no longer existed."""
        from BPTK_Py import SimultaneousScheduler

        class Caller(Agent):
            def act(self, time, round_no, step_no):
                # The last agent's event is still queued when the run ends.
                self.model.enqueue_event(Event("call", self.id, len(self.model.agents) - 1))

        model = Model(starttime=1, stoptime=3, dt=1, scheduler=SimultaneousScheduler())
        model.register_agent_factory(
            "caller", lambda agent_id, model, properties: Caller(agent_id, model, properties))
        config = {"runspecs": {"starttime": 1, "stoptime": 3, "dt": 1.0}, "properties": {},
                  "agents": [{"name": "caller", "count": 5}]}

        model.configure(config)
        model.run()
        self.assertTrue(model.events)

        model.configure(config)
        self.assertEqual([agent.id for agent in model.agents], list(range(5)))
        self.assertEqual(model.events, [])
        model.run()

    def test_reset_drops_the_queued_events(self):
        model = Model()
        model.enqueue_event(Event("left over", 0, 3))

        model.reset()

        self.assertEqual(model.events, [])

    def test_reset_cache(self):
        model = Model()

        model.reset_cache()

        class TestableAgent(Agent):
            def __init__(self, agent_id, model, properties, agent_type="agent"):
                super().__init__(agent_id, model, properties, agent_type)
                self.reset_cache_called = 0

            def reset_cache(self):
                self.reset_cache_called = 1      

        func = lambda agent_id, model, properties: TestableAgent(agent_id=agent_id,model=model,properties=properties)
        model.register_agent_factory(agent_factory=func,agent_type="testType")
        model.create_agent(agent_type="testType",agent_properties={"name": {"type" : "String", "value": "testAgent"}})    

        dataCollector = DataCollector()
        model.data_collector = dataCollector
        event= Event(name="eventName", sender_id=1, receiver_id=2)
        model.data_collector.record_event(time=101,event=event)
        model.data_collector.collect_agent_statistics(time=201,agents=model.agents)

        model.reset_cache()

        self.assertEqual(model.data_collector.agent_statistics,{})
        self.assertEqual(model.data_collector.event_statistics,{})
        for agent in model.agents:
            self.assertEqual(agent.reset_cache_called,1)

    def test_reset_cache_skips_an_empty_memo_and_clears_a_filled_one(self):
        """reset_cache walks the memo only when something was computed since the last
        reset: building an array resets it once per cell, with nothing to clear."""
        model = Model(starttime=0.0, stoptime=2.0, dt=1.0, name="memo")
        rate = model.constant("rate")
        rate.equation = 1.0
        stock = model.stock("stock")
        stock.initial_value = 0.0
        stock.equation = rate

        self.assertFalse(model._memo_filled)
        self.assertEqual(model.memoize("stock", 2.0), 2.0)
        self.assertTrue(model._memo_filled)

        # A changed equation still invalidates what was computed with the old one
        rate.equation = 5.0
        self.assertFalse(model._memo_filled)
        self.assertEqual(model.memoize("stock", 2.0), 10.0)

    def test_a_function_defined_again_replaces_the_first(self):
        """The second definition used to be dropped without a word, so a notebook cell
        run again with a changed function kept computing with the old one."""
        model = Model(starttime=0.0, stoptime=10.0, dt=1.0, name="redefined")
        uplift = model.function("uplift", lambda model, t: 5 * t)
        converter = model.converter("converter")
        converter.equation = uplift()
        self.assertEqual(converter(5), 25.0)

        model.function("uplift", lambda model, t: 6 * t)

        # The equation built from the first definition follows, and nothing cached stays
        self.assertEqual(converter(5), 30.0)

    @pytest.mark.requires_rust
    def test_a_function_defined_again_reaches_the_rust_engine(self):
        model = Model(starttime=0.0, stoptime=10.0, dt=1.0, name="redefined")
        uplift = model.function("uplift", lambda model, t: 5 * t)
        model.converter("converter").equation = uplift()
        model.function("uplift", lambda model, t: 6 * t)

        instance = BPTK_Py.bptk()
        instance.register_model(model)
        for backend in ("python", "rust"):
            results = instance.run_scenarios(scenario_managers=["smRedefined"], scenarios=["base"],
                                             equations=["converter"], backend=backend)
            self.assertEqual(results.loc[5.0].tolist(), [30.0], backend)

    def test_a_restored_cache_is_cleared_by_the_next_reset(self):
        from BPTK_Py.scenariomanager.scenario import SimulationScenario

        model = Model(starttime=0.0, stoptime=1.0, dt=1.0, name="restored")
        model.constant("c").equation = 1.0
        scenario = SimulationScenario(dictionary={}, name="s", model=model, scenario_manager_name="m")

        scenario._set_cache({"c": {0.0: 99.0}})
        self.assertEqual(model.memoize("c", 0.0), 99.0)

        model.reset_cache()
        self.assertEqual(model.memoize("c", 0.0), 1.0)

    def test_agent_ids(self):
        model = Model()

        func = lambda agent_id, model, properties: Agent(agent_id=agent_id,model=model,properties=properties)

        model.register_agent_factory(agent_factory=func,agent_type="testType1")
        model.register_agent_factory(agent_factory=func,agent_type="testType2")

        model.create_agent(agent_type="testType1",agent_properties={"name": {"type" : "Integer", "value": "testAgent1"}})
        model.create_agent(agent_type="testType1",agent_properties={"name": {"type" : "Integer", "value": "testAgent2"}})
        model.create_agent(agent_type="testType2",agent_properties={"name": {"type" : "Integer", "value": "testAgent3"}})

        self.assertEqual(model.agent_ids(agent_type="testType1"),[0,1])
        self.assertEqual(model.agent_ids(agent_type="testType2"),[2])

    def test_agent(self):
        model = Model()

        func = lambda agent_id, model, properties: Agent(agent_id=agent_id,model=model,properties=properties)

        model.register_agent_factory(agent_factory=func,agent_type="testType")

        model.create_agent(agent_type="testType",agent_properties={"name": {"type" : "Integer", "value": "testAgent1"}})
        model.create_agent(agent_type="testType",agent_properties={"name": {"type" : "Integer", "value": "testAgent2"}})
        model.create_agent(agent_type="testType",agent_properties={"name": {"type" : "Integer", "value": "testAgent3"}})        

        self.assertEqual(model.agent(agent_id=0).get_property_value(name="name"),"testAgent1")
        self.assertEqual(model.agent(agent_id=1).get_property_value(name="name"),"testAgent2")
        self.assertEqual(model.agent(agent_id=2).get_property_value(name="name"),"testAgent3")
        self.assertIsNone(model.agent(agent_id=3))

    def test_create_agent_exception(self):
        model = Model()

        func = lambda agent_id, model, properties: 1

        model.register_agent_factory(agent_factory=func,agent_type="testType")

        self.assertRaises(Exception, model.create_agent,agent_type="testType",agent_properties={})

    def test_get_property(self):
        model = Model()

        model.set_property(name="name",property_spec={"type" : "String", "value": "testModelName"})
        model.set_property(name="number",property_spec={"type" : "Integer", "value": 111})

        self.assertEqual(model.get_property(name="name"),{"type" : "String", "value": "testModelName"})
        self.assertEqual(model.get_property(name="number"),{"type" : "Integer", "value": 111})

        self.assertIsNone(model.get_property(name="NOT"))

    def test_set_property_value(self):
        model = Model()

        model.set_property(name="name",property_spec={"type" : "String", "value": "testModelName"}) 

        model.set_property_value(name="name",value="testModelNameEdited")      

        self.assertEqual(model.get_property(name="name"),{"type" : "String", "value": "testModelNameEdited"})

    def test_property_attribute_follows_every_way_of_setting_it(self):
        model = Model()
        model.set_property(name="rate", property_spec={"type": "Double", "value": 0.1})

        model.rate = 0.2
        self.assertEqual(model.rate, 0.2)
        self.assertEqual(model.get_property_value(name="rate"), 0.2)

        # An assignment used to leave a copy in __dict__ that hid every later change
        model.set_property_value(name="rate", value=0.3)
        self.assertEqual(model.rate, 0.3)

        model.set_property(name="rate", property_spec={"type": "Double", "value": 0.4})
        self.assertEqual(model.rate, 0.4)

    def test_property_named_like_an_attribute_still_sets_the_attribute(self):
        model = Model(dt=1.0)
        model.set_property(name="dt", property_spec={"type": "Double", "value": 1.0})

        model.dt = 0.5

        self.assertEqual(model.dt, 0.5)
        self.assertEqual(model.get_property_value(name="dt"), 0.5)

    def test_get_property_value(self):
        model = Model()

        model.set_property(name="name",property_spec={"type" : "String", "value": "testModelName"}) 
        model.set_property(name="number",property_spec={"type" : "Integer", "value": 112})
        model.set_property(name="active",property_spec={"type" : "Integer", "value": True})

        self.assertEqual(model.get_property_value(name="name"),"testModelName")
        self.assertEqual(model.get_property_value(name="number"),112)
        self.assertTrue(model.get_property_value(name="active"))

    def test_getattr(self):
        model = Model()

        model.set_property(name="description",property_spec={"type" : "String", "value": "testModelDescription"}) 
        model.set_property(name="number",property_spec={"type" : "Integer", "value": 113})

        self.assertEqual(model.agents,[])
        self.assertEqual(model.description,"testModelDescription")
        self.assertEqual(model.number,113)

        # Fallback branch: a name that is not a property but exists in __dict__.
        # Normal attribute access finds it without invoking __getattr__, so call
        # __getattr__ directly to exercise the fallback return.
        model.__dict__["plain_attr"] = "plainValue"
        self.assertEqual(model.__getattr__("plain_attr"), "plainValue")

        with self.assertRaises(AttributeError) as context:
            model.invalid_property

    def test_settattr(self):
        model = Model(name="testModelName")

        model.set_property(name="description",property_spec={"type" : "String", "value": "testModelDescription"}) 
        model.set_property(name="lookup",property_spec={"type" : "Lookup", "value": {0 : 0, 1 : 1}})

        model.name="testModelNameEdited"
        model.description = "testModelDescriptionEdited"
        model.lookup = {0 : 0.1 , 1 : 0.9}

        self.assertEqual(model.name,"testModelNameEdited")
        self.assertEqual(model.description,"testModelDescriptionEdited")
        self.assertEqual(model.lookup,{0 : 0.1 , 1 : 0.9})
        self.assertEqual(model.points,{'lookup': {0: 0.1, 1: 0.9}})

    def test_begin_episode(self):
        model = Model()

        class TestableAgent(Agent):
            def __init__(self, agent_id, model, properties, agent_type="agent"):
                super().__init__(agent_id, model, properties, agent_type)
                self.begin_called_with = None

            def begin_episode(self, episode_no):
                self.begin_called_with = episode_no   

        func = lambda agent_id, model, properties: TestableAgent(agent_id=agent_id,model=model,properties=properties)

        model.register_agent_factory(agent_factory=func,agent_type="testType")

        model.create_agent(agent_type="testType",agent_properties={"name": {"type" : "Integer", "value": "testAgent1"}})     
        model.create_agent(agent_type="testType",agent_properties={"name": {"type" : "Integer", "value": "testAgent1"}})    

        model.begin_episode(episode_no=3)

        for agent in model.agents:
            self.assertEqual(agent.begin_called_with,3) 

    def test_end_episode(self):
        model = Model()

        class TestableAgent(Agent):
            def __init__(self, agent_id, model, properties, agent_type="agent"):
                super().__init__(agent_id, model, properties, agent_type)
                self.end_called_with = None

            def end_episode(self, episode_no):
                self.end_called_with = episode_no   

        func = lambda agent_id, model, properties: TestableAgent(agent_id=agent_id,model=model,properties=properties)

        model.register_agent_factory(agent_factory=func,agent_type="testType")

        model.create_agent(agent_type="testType",agent_properties={"name": {"type" : "Integer", "value": "testAgent1"}})     
        model.create_agent(agent_type="testType",agent_properties={"name": {"type" : "Integer", "value": "testAgent1"}})    

        model.end_episode(episode_no=4)

        for agent in model.agents:
            self.assertEqual(agent.end_called_with,4)             

    def test_instantiate_model(self):
        model = Model()

        result_value = model.instantiate_model()

        self.assertIsNone(result_value)

    def test_run(self):
        """Model.run delegates to the scheduler and steps every round."""
        from BPTK_Py.modeling.simultaneousScheduler import SimultaneousScheduler

        class CountingAgent(Agent):
            def __init__(self, agent_id, model, properties, agent_type="counter"):
                super().__init__(agent_id, model, properties, agent_type)
                self.act_calls = 0

            def act(self, time, round_no, step_no):
                self.act_calls += 1

        def _build_model():
            model = Model(scheduler=SimultaneousScheduler(), data_collector=DataCollector())
            # run_specs keeps integer runspecs (the scheduler's range() needs ints);
            # this mirrors how the framework configures ABM models from scenario JSON.
            model.run_specs(starttime=1, stoptime=3, dt=1)
            model.register_agent_factory(
                agent_type="counter",
                agent_factory=lambda agent_id, model, properties: CountingAgent(
                    agent_id=agent_id, model=model, properties=properties),
            )
            model.create_agent(agent_type="counter", agent_properties={})
            return model

        # normal path (show_progress_widget=False)
        model = _build_model()
        model.run()
        # rounds 1, 2, 3 -> one act call per round
        self.assertEqual(model.agents[0].act_calls, 3)

        # Jupyter progress-widget path (show_progress_widget=True)
        model = _build_model()
        model.run(show_progress_widget=True)
        self.assertEqual(model.agents[0].act_calls, 3)

    def test_enqueue_event(self):
        model = Model()

        class NotAnEvent():
            pass

        from BPTK_Py import Event, DelayedEvent
        valid_event = Event(name="test", sender_id=1, receiver_id=0, data=[0])
        invalid_event = NotAnEvent()


        from BPTK_Py.exceptions import WrongTypeException
        self.assertRaises(WrongTypeException,model.enqueue_event,event=invalid_event)

        model.enqueue_event(valid_event)

        self.assertEqual(model.events[0],valid_event)

    def test_next_agent(self):
        model = Model()

        func = lambda agent_id, model, properties: Agent(agent_id=agent_id,model=model,properties=properties,agent_type="testType1")

        model.register_agent_factory(agent_factory=func,agent_type="testType1")

        model.create_agent(agent_type="testType1",agent_properties={"name": {"type" : "Integer", "value": "testAgent"}})

        self.assertEqual(model.next_agent(agent_type="testType1",state="active").name,"testAgent")
        self.assertIsNone(model.next_agent(agent_type="testType",state="active"))

    def test_random_agents(self):
        model = Model()

        func1 = lambda agent_id, model, properties: Agent(agent_id=agent_id,model=model,properties=properties,agent_type="testType1")
        func2 = lambda agent_id, model, properties: Agent(agent_id=agent_id,model=model,properties=properties,agent_type="testType2")

        model.register_agent_factory(agent_factory=func1,agent_type="testType1")
        model.register_agent_factory(agent_factory=func2,agent_type="testType2")

        model.create_agent(agent_type="testType1",agent_properties={"name": {"type" : "Integer", "value": "testAgent11"}})  #id=0
        model.create_agent(agent_type="testType1",agent_properties={"name": {"type" : "Integer", "value": "testAgent12"}})  #id=1
        model.create_agent(agent_type="testType1",agent_properties={"name": {"type" : "Integer", "value": "testAgent13"}})  #id=2
        model.create_agent(agent_type="testType2",agent_properties={"name": {"type" : "Integer", "value": "testAgent21"}})  #id=3
        model.create_agent(agent_type="testType2",agent_properties={"name": {"type" : "Integer", "value": "testAgent22"}})  #id=4

        agent_list1 = model.random_agents(agent_type="testType1",num_agents=2)
        self.assertEqual(len(agent_list1),2)
        for id_number in agent_list1:
            self.assertIn(id_number,[0, 1, 2])

        #at most the number of actually available agents
        agent_list2 = model.random_agents(agent_type="testType1",num_agents=20)
        self.assertEqual(len(agent_list2),3)
        for id_number in agent_list2:
            self.assertIn(id_number,[0, 1, 2])

        agent_list3 = model.random_agents(agent_type="testType2",num_agents=1)
        self.assertEqual(len(agent_list3),1)
        self.assertIn(agent_list3[0],[3, 4])

        agent_list4 = model.random_agents(agent_type="testType2",num_agents=0)
        self.assertEqual(len(agent_list4),0)
        self.assertEqual(agent_list4,[]
                         )
        agent_list4 = model.random_agents(agent_type="testType2",num_agents=-1)
        self.assertEqual(len(agent_list4),0)
        self.assertEqual(agent_list4,[])

    def test_random_events(self):
        model = Model()

        func_agents = lambda agent_id, model, properties: Agent(agent_id=agent_id,model=model,properties=properties,agent_type="testAgentType")
        func_events = lambda agent_id: Event(name="testEvent" + str(agent_id), sender_id=agent_id, receiver_id=-agent_id-1, data=None)

        model.register_agent_factory(agent_factory=func_agents,agent_type="testAgentType")

        model.create_agent(agent_type="testAgentType",agent_properties={"name": {"type" : "Integer", "value": "testAgent1"}})  #id=0
        model.create_agent(agent_type="testAgentType",agent_properties={"name": {"type" : "Integer", "value": "testAgent2"}})  #id=1
        model.create_agent(agent_type="testAgentType",agent_properties={"name": {"type" : "Integer", "value": "testAgent2"}})  #id=2

        model.random_events(agent_type="testAgentType",num_agents=2, event_factory=func_events)

        self.assertEqual(len(model.events),2)

        for event in model.events:
            self.assertIn(event.name,["testEvent0","testEvent1","testEvent2"])
            self.assertIn(event.sender_id,[0,1,2])
            self.assertIn(event.receiver_id,[-1,-2,-3])
            self.assertIsNone(event.data)

    def test_broadcast_event(self):
        model = Model()
        from BPTK_Py import Agent, Event
        event = Event("name", 1,1,None)
        factory = lambda id : event

        from BPTK_Py.exceptions import WrongTypeException
        self.assertRaises(WrongTypeException,model.broadcast_event,agent_type=1,event_factory=factory)

        self.assertRaises(KeyError,model.broadcast_event,"testAgent",factory)

        agent = Agent(agent_id=1, model=model, properties={}, agent_type="testAgent")

        model.agents += [agent]
        model.agent_type_map[agent.agent_type] = [agent.id]
        model.broadcast_event(agent_type="testAgent",event_factory=factory)

        self.assertEqual(model.events,[event])

    def test_configure_properties_dict(self):
        model = Model()

        properties = { "address": {"type" : "String", "value": "address_of_model"} , "model_rate": {"type" : "Lookup", "value": {0 : 0.1 , 1 : 0.9}} }

        model.configure_properties(properties=properties)

        self.assertEqual(model.properties,properties)
        self.assertEqual(model.points["model_rate"],{0 : 0.1 , 1 : 0.9})

    def test_agent_count(self):
        model = Model()

        func = lambda agent_id, model, properties: Agent(agent_id=agent_id,model=model,properties=properties)

        model.register_agent_factory(agent_factory=func,agent_type="testType1")
        model.register_agent_factory(agent_factory=func,agent_type="testType2")

        model.create_agent(agent_type="testType1",agent_properties={"name": {"type" : "String", "value": "testAgent1"}}) 
        model.create_agent(agent_type="testType2",agent_properties={"name": {"type" : "String", "value": "testAgent2"}}) 
        model.create_agent(agent_type="testType2",agent_properties={"name": {"type" : "String", "value": "testAgent3"}}) 

        self.assertEqual(model.agent_count(agent_type="testType1"),1)    
        self.assertEqual(model.agent_count(agent_type="testType2"),2)      

    def test_agent_count_per_state(self):
        model = Model()

        func = lambda agent_id, model, properties: Agent(agent_id=agent_id,model=model,properties=properties)

        model.register_agent_factory(agent_factory=func,agent_type="testType1")
        model.register_agent_factory(agent_factory=func,agent_type="testType2")

        model.create_agent(agent_type="testType1",agent_properties={"name": {"type" : "String", "value": "testAgent1"}}) #id=0 (inactive)
        model.create_agent(agent_type="testType2",agent_properties={"name": {"type" : "String", "value": "testAgent2"}}) #id=1 (active)
        model.create_agent(agent_type="testType2",agent_properties={"name": {"type" : "String", "value": "testAgent3"}}) #id=2 (inactive)
        model.create_agent(agent_type="testType2",agent_properties={"name": {"type" : "String", "value": "testAgent4"}}) #id=3 (active)

        for agent in model.agents:
            if agent.id == 0 or agent.id == 2:
                agent.state = "inactive"

        self.assertEqual(model.agent_count_per_state(agent_type="testType1",state="active"),0)        
        self.assertEqual(model.agent_count_per_state(agent_type="testType1",state="inactive"),1)        
        self.assertEqual(model.agent_count_per_state(agent_type="testType2",state="inactive"),1)        
        self.assertEqual(model.agent_count_per_state(agent_type="testType2",state="active"),2)  

    def test_statistics_errorlog(self):
        model = Model()

        model.statistics()

        content = read_log()

        self.assertIn("[ERROR] Tried to obtain Agent statistics but no data Collector available!", content)                        

    @pytest.mark.requires_extra("plotting")
    def test_plot_lookup(self):
        model = Model()
        import BPTK_Py.sddsl.functions as sd
        model.converter(name="test")
        model.converters["test"].equation = sd.lookup(1,[ (0,0.3) , (4,0.7)])

        self.assertIsNone(model.plot_lookup("test"))

    def _lookup_model(self):
        import BPTK_Py.sddsl.functions as sd
        model = Model()
        model.converter(name="test")
        model.converters["test"].equation = sd.lookup(1, [(0, 0.3), (4, 0.7)])
        return model

    @pytest.mark.requires_extra("plotting")
    def test_plot_lookup_format_axes(self):
        """format="axes" hands the Axes back, the way Element.plot() does.

        Without it the method only produced output as a side effect of Jupyter's
        inline backend, so the documentation pages showed nothing under marimo.
        """
        import matplotlib.axes

        ax = self._lookup_model().plot_lookup("test", format="axes")

        self.assertIsInstance(ax, matplotlib.axes.Axes)

    def test_plot_lookup_format_df(self):
        """format="df" returns the underlying dataframe."""
        import pandas as pd

        df = self._lookup_model().plot_lookup("test", format="df")

        self.assertIsInstance(df, pd.DataFrame)

    def test_add_equation(self):
        #cleanup logfile
        clear_log()

        model = Model()
        flow = model.flow("flow")
        flow.equation = 1.0

        model.add_equation(equation="flow", lambda_method= lambda t: 2.0)
        model.add_equation(equation="converter", lambda_method= lambda t: 3.0)

        self.assertEqual(model.equations["flow"](1), 2.0)
        self.assertEqual(model.memo["flow"],{})

        self.assertEqual(model.equations["converter"](1), 3.0)
        self.assertEqual(model.memo["converter"],{})

        content = read_log()

        self.assertIn("[WARN] Hybrid Model : Overwriting equation flow", content)  
        self.assertNotIn("[WARN] Hybrid Model : Overwriting equation converter", content)  

    def test_a_cold_evaluation_far_into_the_run_answers_instead_of_raising(self):
        """A stock asks for the step before it, so a cold late step is a long chain.

        Python's stack runs out at about 330 steps of it - counted in steps, so a fine
        `dt` reaches that early in model time. Computing forward keeps each step shallow.
        """
        model = Model(starttime=0.0, stoptime=2000.0, dt=1.0, name="deep")
        stock = model.stock("stock")
        stock.initial_value = 0.0
        inflow = model.flow("inflow")
        inflow.equation = 1.0
        stock.equation = inflow

        # Well past the ~330 steps a chain of calls fits into
        self.assertEqual(stock(1500.0), 1500.0)

    def test_a_fine_dt_reaches_the_same_depth_early_in_model_time(self):
        """The limit counts steps, not time: at dt=0.125 it used to arrive at t=41.5."""
        model = Model(starttime=0.0, stoptime=200.0, dt=0.125, name="fine")
        stock = model.stock("stock")
        stock.initial_value = 0.0
        inflow = model.flow("inflow")
        inflow.equation = 8.0
        stock.equation = inflow

        self.assertEqual(stock(100.0), 800.0)

    def test_computing_forward_keeps_what_was_already_worked_out(self):
        """Ask for an early step, then jump far ahead: the gap is what gets filled.

        The jump is longer than a chain of calls can be, so it computes forward - and
        the steps from the first question are still there to be found rather than
        worked out a second time.
        """
        model = Model(starttime=0.0, stoptime=2000.0, dt=1.0, name="partly_known")
        stock = model.stock("stock")
        stock.initial_value = 0.0
        inflow = model.flow("inflow")
        inflow.equation = 1.0
        stock.equation = inflow

        self.assertEqual(stock(100.0), 100.0)
        before = dict(model.memo["stock"])

        self.assertEqual(stock(1500.0), 1500.0)

        # every step of the first answer survived the second, unchanged
        for t, value in before.items():
            self.assertEqual(model.memo["stock"][t], value)

    def test_an_element_without_a_past_is_still_evaluated_once(self):
        """Computing forward is the answer to a chain, not the way everything is run.

        An element that does not look back has no chain to shorten, and computing it
        from starttime would turn one evaluation into thousands.
        """
        model = Model(starttime=0.0, stoptime=10000.0, dt=1.0, name="flat")
        calls = []

        def counting(t):
            calls.append(t)
            return t * 2.0

        model.add_equation("flat", counting)

        self.assertEqual(model.memoize("flat", 5000.0), 10000.0)
        self.assertEqual(len(calls), 1)

    def test_one_timestep_too_deep_says_what_happened(self):
        """Not the timestep chain but a chain of elements, which computing forward
        cannot shorten. The bare RecursionError said nothing about which it was."""
        model = Model(starttime=0.0, stoptime=10.0, dt=1.0, name="chain")
        previous = None
        for index in range(600):
            element = model.converter("c{}".format(index))
            element.equation = 1.0 if previous is None else previous + 1.0
            previous = element

        with self.assertRaises(RecursionError) as caught:
            previous(5.0)

        self.assertIn("a chain of elements referring to one another",
                      str(caught.exception))


class Test_CycleDetection(unittest.TestCase):
    """Elements that read one another within the same timestep can never be evaluated.
    The engine notices the moment an equation is asked for again while it is still
    being computed, and names the loop in the same words as the Rust engine. A stock or
    a delay reads an earlier step and so breaks a loop - those models must keep running.
    """

    PREFIX = "Cyclic dependency among non-stock entities: "

    def two_element_cycle(self):
        model = Model(starttime=0.0, stoptime=5.0, dt=1.0, name="cycle")
        a = model.converter("a")
        b = model.converter("b")
        a.equation = b + 1.0
        b.equation = a * 2.0
        return model

    def assertNamesLoop(self, model, equation, t, loop):
        with self.assertRaises(CyclicDependencyError) as caught:
            model.evaluate_equation(equation, t)
        self.assertEqual(str(caught.exception), self.PREFIX + loop)

    def test_a_two_element_cycle_is_named(self):
        self.assertNamesLoop(self.two_element_cycle(), "a", 2.0, "a → b → a")

    def test_the_loop_is_named_the_same_whichever_element_is_asked_first(self):
        self.assertNamesLoop(self.two_element_cycle(), "b", 2.0, "a → b → a")

    def test_it_is_a_value_error_as_on_the_rust_engine(self):
        with self.assertRaises(ValueError):
            self.two_element_cycle().evaluate_equation("a", 0.0)

    def test_a_self_reference_is_a_cycle(self):
        model = Model(starttime=0.0, stoptime=5.0, dt=1.0, name="self")
        a = model.converter("a")
        a.equation = a + 1.0
        self.assertNamesLoop(model, "a", 1.0, "a → a")

    def test_a_cycle_through_module_names_reports_the_names_verbatim(self):
        model = Model(starttime=1.0, stoptime=5.0, dt=1.0, name="modules")
        decision = model.converter("wholesaler.orderDecision")
        making = model.flow("wholesaler.makingOrders")
        sending = model.flow("wholesaler.sendingOrders")
        decision.equation = sending + 1.0
        making.equation = decision
        sending.equation = making
        self.assertNamesLoop(model, "wholesaler.orderDecision", 1.0,
                             "wholesaler.makingOrders → wholesaler.orderDecision → "
                             "wholesaler.sendingOrders → wholesaler.makingOrders")

    def test_a_cycle_reached_through_a_stock_leaves_the_stock_out(self):
        """The stock reads its flow one step earlier; the loop is among flow and
        converter at that step, and the stock is no part of it."""
        model = Model(starttime=0.0, stoptime=5.0, dt=1.0, name="behind_stock")
        level = model.stock("level")
        inflow = model.flow("inflow")
        rate = model.converter("rate")
        level.initial_value = 1.0
        level.equation = inflow
        inflow.equation = rate
        rate.equation = inflow * 0.5
        self.assertNamesLoop(model, "level", 3.0, "inflow → rate → inflow")

    def test_a_cycle_is_raised_from_a_run(self):
        with self.assertRaises(CyclicDependencyError):
            self.two_element_cycle().simulate(["a"], backend="python")

    def test_a_loop_broken_by_a_stock_still_runs(self):
        model = Model(starttime=0.0, stoptime=5.0, dt=1.0, name="stock_loop")
        level = model.stock("level")
        inflow = model.flow("inflow")
        rate = model.converter("rate")
        level.initial_value = 10.0
        level.equation = inflow
        inflow.equation = rate
        rate.equation = level * 0.1
        self.assertAlmostEqual(model.evaluate_equation("level", 5.0), 10.0 * 1.1 ** 5)

    def test_a_loop_broken_by_a_delay_still_runs(self):
        model = Model(starttime=0.0, stoptime=5.0, dt=1.0, name="delay_loop")
        a = model.converter("a")
        d = model.converter("d")
        a.equation = d + 1.0
        d.equation = sd.delay(model, a, 1.0, 0.0)
        self.assertEqual([model.evaluate_equation("a", t) for t in range(6)],
                         [1, 2, 3, 4, 5, 6])

    def test_a_loop_closed_by_a_zero_duration_delay_is_a_cycle(self):
        """delay(x, 0) reads the current step, so it breaks nothing."""
        model = Model(starttime=0.0, stoptime=5.0, dt=1.0, name="delay_zero")
        a = model.converter("a")
        d = model.converter("d")
        a.equation = d + 1.0
        d.equation = sd.delay(model, a, 0.0, 0.0)
        self.assertNamesLoop(model, "a", 2.0, "a → d → a")

    def test_two_sub_elements_of_one_array_reading_each_other_are_a_cycle(self):
        model = Model(starttime=0.0, stoptime=3.0, dt=1.0, name="array_cycle")
        a = model.converter("a")
        a.setup_vector(2, 0.0)
        a[0].equation = a[1] + 1.0
        a[1].equation = a[0] * 2.0
        self.assertNamesLoop(model, "a[1]", 1.0, "a[0] → a[1] → a[0]")

    def test_a_sub_element_reading_its_neighbour_is_no_cycle(self):
        model = Model(starttime=0.0, stoptime=3.0, dt=1.0, name="array_chain")
        a = model.converter("a")
        a.setup_vector(2, 0.0)
        a[0].equation = 5.0
        a[1].equation = a[0] + 1.0
        self.assertEqual([model.evaluate_equation("a[1]", t) for t in range(4)], [6.0] * 4)

    def test_an_error_caught_inside_an_equation_leaves_no_false_cycle_behind(self):
        """An equation that catches a failure below it and carries on must not leave the
        failed element recorded as still being computed."""
        model = Model(starttime=0.0, stoptime=5.0, dt=1.0, name="caught")
        attempts = []

        def fragile(t):
            attempts.append(t)
            if len(attempts) == 1:
                raise KeyError("first attempt fails")
            return 1.0

        def tolerant(t):
            try:
                model.memoize("fragile", t)
            except KeyError:
                pass
            return model.memoize("fragile", t) + 1.0

        model.add_equation("fragile", fragile)
        model.add_equation("tolerant", tolerant)
        self.assertEqual(model.memoize("tolerant", 0.0), 2.0)

    @pytest.mark.requires_threads
    def test_threads_evaluating_one_model_do_not_see_each_other_as_a_loop(self):
        """Threads can evaluate one model at once on its shared memo - two server
        requests, say. What one thread is computing is not a loop for another that asks
        for the same equation."""
        model = Model(starttime=0.0, stoptime=5.0, dt=1.0, name="threads")
        inside = threading.Event()
        release = threading.Event()

        def slow(t):
            inside.set()
            release.wait(timeout=5)
            return 3.0

        model.add_equation("slow", slow)
        model.add_equation("reader", lambda t: model.memoize("slow", t) + 1.0)

        results, errors = {}, []

        def run(name):
            try:
                results[name] = model.memoize(name, 0.0)
            except Exception as error:
                errors.append(error)

        first = threading.Thread(target=run, args=("slow",))
        first.start()
        inside.wait(timeout=5)
        second = threading.Thread(target=run, args=("reader",))
        second.start()
        release.set()
        first.join()
        second.join()

        self.assertEqual(errors, [])
        self.assertEqual(results, {"slow": 3.0, "reader": 4.0})

    def test_the_error_is_exported_at_package_level(self):
        self.assertIs(BPTK_Py.CyclicDependencyError, BPTK_Py.exceptions.CyclicDependencyError)


class Test_LookupPoints(unittest.TestCase):
    """A lookup table's points are sorted by x before interpolation, and points that are
    no table are refused - the same rule as on the Rust engine."""

    def lookup_model(self, points):
        model = Model(starttime=0.0, stoptime=1.0, dt=1.0, name="points")
        model.points["tab"] = points
        return model

    def test_points_in_order_are_returned_as_they_are(self):
        points = [[0, 0], [1, 1]]
        self.assertIs(lookup_points("tab", points), points)

    def test_points_out_of_order_are_sorted(self):
        self.assertEqual(lookup_points("tab", [[10, 100], [0, 0], [5, 50]]),
                         [[0, 0], [5, 50], [10, 100]])
        self.assertEqual(self.lookup_model([[10, 100], [0, 0]])._lookup(2.5, "tab"), 25.0)

    def test_two_points_at_one_x_are_refused(self):
        with self.assertRaisesRegex(ValueError, "Lookup table 'tab' has two points at x=5.0"):
            lookup_points("tab", [[5, 10], [0, 0], [5, 90]])

    def test_a_table_without_points_is_refused(self):
        with self.assertRaisesRegex(ValueError, "Lookup table 'tab' has no points"):
            lookup_points("tab", [])

    def test_a_point_whose_x_is_not_a_number_is_refused(self):
        with self.assertRaisesRegex(ValueError, "x must be a finite number"):
            lookup_points("tab", [[float("nan"), 0], [1, 1]])

    def test_inline_points_are_checked_where_they_are_written(self):
        with self.assertRaisesRegex(ValueError, "Lookup table 'inline' has two points"):
            sd.lookup(1.0, [[1, 0], [1, 1]])

    def test_a_table_the_model_does_not_have_is_named(self):
        with self.assertRaisesRegex(ValueError, "Lookup of a table the model does not have: 'x'"):
            self.lookup_model([[0, 0], [1, 1]])._lookup(0.5, "x")

    def test_a_plotted_table_is_sorted_too(self):
        frame = lookup_data(self.lookup_model([[10, 100], [0, 0], [5, 50]]), "tab")
        self.assertEqual(list(frame.index), [0, 5, 10])
