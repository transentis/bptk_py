import unittest

from BPTK_Py.abm.model import Model

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

if __name__ == '__main__':
    unittest.main()
