import unittest
from unittest.mock import patch

from BPTK_Py import Agent, Event

from BPTK_Py import Model


class TestAgent(unittest.TestCase):
    def setUp(self):
        pass

    def testAgentInit(self):

        model = Model()
        properties = {}

        self.assertEqual(Agent(agent_id=1, model=model, properties={},agent_type="testAgent").id,1)
        self.assertEqual(Agent(agent_id=1, model=model, properties={}, agent_type="testAgent").state, "active")
        self.assertEqual(Agent(agent_id=1, model=model, properties={}, agent_type="testAgent").agent_type, "testAgent")
        self.assertEqual(Agent(agent_id=1, model=model, properties={}, agent_type="testAgent").model, model)
        self.assertEqual(Agent(agent_id=1, model=model, properties={}, agent_type="testAgent").eventHandlers, {})
        self.assertNotEqual(id(Agent(agent_id=1, model=model, properties={}, agent_type="testAgent").properties), id(properties))
        self.assertEqual(id(Agent(agent_id=1, model=model, properties={}, agent_type="testAgent").model),
                            id(model))
        self.assertEqual(Agent(agent_id=1, model=model, properties={}, agent_type="testAgent").events,[])
        self.assertEqual(Agent(agent_id=1, model=model, properties={}, agent_type="testAgent").properties,properties)
        self.assertEqual(Agent(agent_id=1, model=model, properties={}, agent_type="testAgent").agent_type, "testAgent")

        self.assertRaises(ValueError, Agent, agent_id=1, model="model", properties={}, agent_type="testAgent")
        self.assertRaises(ValueError, Agent, agent_id="1", model=model, properties={}, agent_type="testAgent")
        self.assertRaises(ValueError, Agent, agent_id=1, model=model, properties={}, agent_type=1)
        self.assertRaises(ValueError, Agent, agent_id=1, model=model, properties="DICT", agent_type="testAgent")


    def testAgentSerialize(self):
        model = Model()
        self.assertEqual(Agent(agent_id=1, model=model, properties={"name": {"type" : "String", "value": "testName"}}, agent_type="testAgent").serialize(), {'name': 'testName', 'id': 1, 'state': 'active', 'type': 'testAgent'})

    def testAgentRegister_event_handler(self):
        from BPTK_Py import Event
        model = Model()
        agent = Agent(agent_id=1, model=model, properties={},agent_type="testAgent")

        handler = lambda event : None

        self.assertEqual(len(agent.eventHandlers.keys()),0)
        agent.register_event_handler(["active"],"event",handler)
        self.assertEqual(len(agent.eventHandlers.keys()), 1)
        self.assertEqual(id(agent.eventHandlers["active"]["event"]),id(handler))

        class subAgent(Agent):
            def handler(self,event):
                return


        agent = subAgent(agent_id=1, model=model, properties={},agent_type="testAgent")

        self.assertEqual(len(agent.eventHandlers.keys()), 0)
        agent.register_event_handler(["active"], "event", agent.handler)
        self.assertEqual(len(agent.eventHandlers.keys()), 1)
        self.assertEqual(agent.eventHandlers["active"]["event"], agent.handler)

        self.assertRaises(ValueError, agent.register_event_handler,"states","event",handler)       
        self.assertRaises(ValueError, agent.register_event_handler,["active"],1,handler)        

    def test_ReceiveEvent(self):
        from BPTK_Py import Event
        model = Model()
        agent = Agent(agent_id=1, model=model, properties={}, agent_type="testAgent")

        valid_event = Event(name="event",sender_id=0,receiver_id=0,data={})
        wrong_event = {}

        agent.receive_event(valid_event)
        self.assertEqual(agent.events, [valid_event])

        self.assertRaises(ValueError,agent.receive_event,event=wrong_event)
        self.assertEqual(agent.events, [valid_event])

    def test_set_property(self):
        model = Model()
        agent = Agent(agent_id=1, model=model, properties={}, agent_type="testAgent")

        valid_property_Double = {"name": {"type" : "Double", "value": 0.01}}
        valid_property_Integer = {"name": {"type" : "Integer", "value": 0}}
        valid_property_String = {"name": {"type": "String", "value": "Hallo"}}

        invalid_property_Double = {"name": {"type": "Double", "value": "text"}}
        invalid_property_Integer = {"name": {"type": "Integer", "value": "text"}}
        invalid_property_String = {"name": {"type": "String", "value": 9}}

        agent.set_property("name",valid_property_Double["name"])
        self.assertEqual(agent.properties["name"],valid_property_Double["name"])

        agent.set_property("name",valid_property_Integer["name"])
        self.assertEqual(agent.properties["name"], valid_property_Integer["name"])

        agent.set_property("name", valid_property_String["name"])
        self.assertEqual(agent.properties["name"], valid_property_String["name"])

        self.assertRaises(ValueError,agent.set_property,name=1,data=valid_property_Double["name"])

        from BPTK_Py.exceptions import  WrongTypeException
        self.assertRaises(WrongTypeException, agent.set_property, name="name", data=invalid_property_Double["name"])
        self.assertRaises(WrongTypeException, agent.set_property, name="name", data=invalid_property_Integer["name"])
        self.assertRaises(WrongTypeException, agent.set_property, name="name", data=invalid_property_String["name"])

        invalid_property_type_value = {"name": {"type" : "Invalid", "value": 0.01}}
        invalid_property_type = {"name": {"invalid_type" : "Double", "value": 0.01}}

        self.assertRaises(ValueError, agent.set_property, name="Name", data=invalid_property_type_value["name"])
        self.assertRaises(KeyError, agent.set_property, name="Name", data=invalid_property_type["name"])

        invalid_property_value = {"name": {"type" : "Integer", "invalid_value": 0.01}}

        self.assertRaises(KeyError, agent.set_property, name="Name", data=invalid_property_value["name"])        
        
    def test_set_property_value(self):
        model = Model()
        agent = Agent(agent_id=1, model=model, properties={}, agent_type="testAgent")

        valid_property_Double = {"doub": {"type": "Double", "value": 0.01}}
        valid_property_Integer = {"int": {"type": "Integer", "value": 0}}
        valid_property_String = {"str": {"type": "String", "value": "Hallo"}}

        agent.set_property("doub", valid_property_Double["doub"])
        agent.set_property("int", valid_property_Integer["int"])
        agent.set_property("str", valid_property_String["str"])

        agent.set_property_value("doub",1.0)
        self.assertEqual(agent.properties["doub"]["value"],1.0)

        agent.set_property_value("int",1)
        self.assertEqual(agent.properties["int"]["value"], 1)

        agent.set_property_value("str","TEXT")
        self.assertEqual(agent.properties["str"]["value"], "TEXT")

        self.assertRaises(KeyError,agent.set_property_value,name="invalid",value="Str")

        from BPTK_Py.exceptions import WrongTypeException
        self.assertRaises(WrongTypeException,agent.set_property_value,name="str",value=1.0)
        self.assertRaises(WrongTypeException, agent.set_property_value, name="doub", value="hallo")
        self.assertRaises(WrongTypeException, agent.set_property_value, name="int", value="hallo")

        valid_property_dictionary = {"name": {"type" : "Dictionary", "value": "testName"}}

        agent.set_property("name",valid_property_dictionary["name"])
        self.assertRaises(WrongTypeException,agent.set_property_value,name="name",value="string")


    def test_get_property(self):
        model = Model()
        agent = Agent(agent_id=1, model=model, properties={}, agent_type="testAgent")

        self.assertRaises(KeyError,agent.get_property,name="test")

        property = {"name": {"type": "Double", "value": 0.01}}
        agent.set_property("name", property["name"])

        self.assertEqual(agent.get_property("name"),property["name"])

    def test_get_property_value(self):
        model = Model()
        agent = Agent(agent_id=1, model=model, properties={}, agent_type="testAgent")

        self.assertRaises(AttributeError,agent.get_property_value,name="test")

        property = {"name": {"type": "Double", "value": 0.01}}
        agent.set_property("name",property["name"])

        self.assertEqual(agent.get_property_value("name"),property["name"]["value"])

    def test_get_attr(self):
        model = Model()
        agent = Agent(agent_id=1, model=model, properties={}, agent_type="testAgent")

        self.assertEqual(agent.__getattr__("id"),agent.id)
        self.assertEqual(agent.__getattr__("id"), 1)

        self.assertRaises(AttributeError,agent.__getattr__,name="name")

        property = {"name": {"type": "Double", "value": 0.01}}
        agent.set_property("name", property["name"])

        self.assertEqual(agent.__getattr__(name="name"),0.01)
        self.assertEqual(id(agent.__getattr__(name="name")), id(property["name"]["value"]))


    def test_set_attr(self):
        model = Model()
        agent = Agent(agent_id=1, model=model, properties={}, agent_type="testAgent")

        agent.set_property("name",{"type":"String","value":"text"})

        agent.__setattr__("name","newtext")
        self.assertEqual(agent.properties["name"]["value"],"newtext")

        agent.__setattr__("id",2)
        self.assertEqual(agent.id,2)
        self.assertNotIn("id",agent.properties.keys())

    def test_receive_instantaneous_event(self):
        model = Model()
        agent = Agent(agent_id=1, model=model, properties={}, agent_type="testAgent")

        from BPTK_Py import Event
        invalid_event = Event(name="test", sender_id=1, receiver_id=0, data=[0])
        valid_event = Event(name="event",sender_id=1,receiver_id=0,data=[0])

        handler = lambda event : 1
        agent.eventHandlers["active"] = {}
        agent.eventHandlers["active"]["event"] = handler

        self.assertRaises(KeyError,agent.receive_instantaneous_event, event=invalid_event)

        self.assertEqual(agent.receive_instantaneous_event(valid_event),1)       

    def test_handle_events(self):
        model = Model()
        agent1 = Agent(agent_id=1, model=model, properties={},agent_type="testAgent1")
        agent2 = Agent(agent_id=2, model=model, properties={},agent_type="testAgent1")
        event = Event(name="testEvent",receiver_id=1,sender_id=2)

        handler = lambda event : None

        agent1.register_event_handler(states=["active"],event="testEvent",handler=handler)
        agent1.receive_event(event=event)
        agent1.handle_events(time=1,sim_round=1,step=1)
        self.assertEqual(agent1.events,[])

        agent2.register_event_handler(states=["active"],event="testEventDifferent",handler=handler)
        agent2.receive_event(event=event)
        agent2.handle_events(time=1,sim_round=1,step=1)
        self.assertEqual(agent2.events,[])

    def test_reset_cache(self):
        model = Model()
        agent = Agent(agent_id=1, model=model, properties={}, agent_type="testAgent")   

        result = agent.reset_cache()

        self.assertIsNone(result)

    def test_begin_episode(self):
        model = Model()
        agent = Agent(agent_id=1, model=model, properties={}, agent_type="testAgent")   

        result = agent.begin_episode(1)

        self.assertIsNone(result)  

    def test_end_episode(self):
        model = Model()
        agent = Agent(agent_id=1, model=model, properties={}, agent_type="testAgent")   

        result = agent.end_episode(1)

        self.assertIsNone(result)   

    @patch('random.random')
    def test_is_event_relevant_true(self,mock_random):
        model = Model()
        agent = Agent(agent_id=1, model=model, properties={}, agent_type="testAgent")  

        mock_random.return_value = 0.3
        treshold_value = 0.5

        self.assertTrue(agent.is_event_relevant(treshold_value))            

    @patch('random.random')
    def test_is_event_relevant_false(self,mock_random):
        model = Model()
        agent = Agent(agent_id=1, model=model, properties={}, agent_type="testAgent")  

        mock_random.return_value = 0.7
        treshold_value = 0.5

        self.assertFalse(agent.is_event_relevant(treshold_value))  

if __name__ == '__main__':
    unittest.main()

