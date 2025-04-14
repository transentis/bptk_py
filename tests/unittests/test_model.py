import unittest

from BPTK_Py import Model, Agent, Event, DataCollector
import BPTK_Py.logger.logger as logmod

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
        from BPTK_Py.logger.logger import logfile

        model = Model()

        model.statistics()

        try:
            with open(logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[ERROR] Tried to obtain Agent statistics but no data Collector available!", content)                        

    def test_plot_lookup(self):
        model = Model()
        import BPTK_Py.sddsl.functions as sd
        model.converter(name="test")
        model.converters["test"].equation = sd.lookup(1,[ (0,0.3) , (4,0.7)])

        self.assertIsNone(model.plot_lookup("test"))

    def test_add_equation(self):
        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        model = Model()
        flow = model.flow("flow")
        flow.equation = 1.0

        model.add_equation(equation="flow", lambda_method= lambda t: 2.0)
        model.add_equation(equation="converter", lambda_method= lambda t: 3.0)

        self.assertEqual(model.equations["flow"](1), 2.0)
        self.assertEqual(model.memo["flow"],{})

        self.assertEqual(model.equations["converter"](1), 3.0)
        self.assertEqual(model.memo["converter"],{})

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[WARN] Hybrid Model : Overwriting equation flow", content)  
        self.assertNotIn("[WARN] Hybrid Model : Overwriting equation converter", content)  

if __name__ == '__main__':
    unittest.main()
