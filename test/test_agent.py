import unittest

from BPTK_Py import Agent

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

        self.assertRaises(ValueError,Agent,agent_id=1, model="model", properties={}, agent_type="testAgent")
        self.assertRaises(ValueError, Agent, agent_id="1", model=model, properties={}, agent_type="testAgent")
        self.assertRaises(ValueError, Agent, agent_id=1, model=model, properties={}, agent_type=1)
        self.assertRaises(ValueError, Agent, agent_id=1, model=model, properties="DICT", agent_type=1)

    def testAgentSerialize(self):
        model = Model()
        self.assertEqual(Agent(agent_id=1, model=model, properties={}, agent_type="testAgent").serialize(), {'id': 1, 'state': 'active', 'type': 'testAgent'})

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


if __name__ == '__main__':
    unittest.main()

