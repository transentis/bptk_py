import random
from BPTK_Py.logger.logger import log


class Agent:

    def __init__(self, agent_id, simulation):
        self.sim = simulation
        self.events = []
        self.id = agent_id
        self.state = "state not set yet"
        self.agent_type = "agent"
        self.eventHandlers = {}

    def serialize(self):
        return {
            "id": self.id,
            "state": self.state,
            "type": self.agent_type
        }

    def register_event_handler(self, states, event, handler):
        for state in states:
            if state not in self.eventHandlers:
                self.eventHandlers[state] = {}

            self.eventHandlers[state][event] = handler

    def receive_event(self, event):
        self.events.append(event)

    def initialize(self):
        log("[ERROR] agent.initialize should be called from subclass")

    def receive_instantaneous_event(self, event):

        if self.state in self.eventHandlers:
            if event.name in self.eventHandlers[self. state]:
                self.eventHandlers[self.state][event.name](event)

    def act(self, time, sim_round, step):
        if self.state in self.eventHandlers:

            handlers = self.eventHandlers[self.state]

            while len(self.events) > 0:
                event = self.events.pop()

                if event.name in handlers:
                    handlers[event.name](event)

    def to_string(self):
        return self.state

    @staticmethod
    def is_event_relevant(threshold):
        return random.random() < threshold
