from BPTK_Py import Agent

from BPTK_Py import Model

from BPTK_Py import Event

model = Model()
agent = Agent(agent_id=1, model=model, properties={},agent_type="testAgent")

event1 = Event(name="eventName1", sender_id=1, receiver_id=2)
event2 = Event(name="eventName2", sender_id=3, receiver_id=4)

agent.receive_event(event1)
agent.receive_event(event2)

handler = lambda event1 : None

agent.register_event_handler(["inactive"],"event1",handler)

for handler in agent.eventHandlers():
    handler.

#print(agent.eventHandlers)
#print('--')
#print(agent.events)
#print('--')
#print(agent.state)
#print('-.-----')


agent.handle_events(1,2,3)

#print(agent.events)

#print(agent.eventHandlers)