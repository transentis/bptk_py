#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018 transentis labs GmbH
# MIT License



import random

from ..logger import log


#################
## AGENT CLASS ##
#################

class Agent:
    """
    Agent for agent based simulation. A simulation requires the implementation of at least one inheriting class
    An agent does things in the simulation and interacts with others
    """

    def __init__(self, agent_id, simulation):
        """

        :param agent_id: id of agent. Model should manage this. Do use agent factories!
        :param simulation: Model instance
        """
        self.sim = simulation
        self.events = []
        self.id = agent_id
        self.state = "state not set yet"
        self.agent_type = "agent"
        self.eventHandlers = {}

    def serialize(self):
        """
        Serialize the agent
        :return:
        """
        return {
            "id": self.id,
            "state": self.state,
            "type": self.agent_type
        }

    def register_event_handler(self, states, event, handler):
        """
        Register an event handler
        :param states: States for which the event handler is valid
        :param event: event instance
        :param handler: Actual handler
        :return: None
        """
        for state in states:
            if state not in self.eventHandlers:
                self.eventHandlers[state] = {}

            self.eventHandlers[state][event] = handler

    def receive_event(self, event):
        """
        Receive an event
        :param event: Event instance
        :return: None
        """
        self.events.append(event)

    def initialize(self):
        """
        Initialize. Implement this method!
        :return: None
        """
        log("[ERROR] agent.initialize should be called from subclass")

    def receive_instantaneous_event(self, event):
        """
        Handle an event immediately, do not wait for another round
        :param event: event instance
        :return: None
        """

        #if self.state in self.eventHandlers:
            #if event.name in self.eventHandlers[self.state]:
        try:
            self.eventHandlers[self.state][event.name](event)
        except KeyError as e:
            pass

    def act(self, time, sim_round, step):
        """
        Actual play method. Triggered by scheduler. Makes the agent progress by one step
        :param time: t
        :param sim_round: round number
        :param step: step number of round
        :return: None
        """


        try:
            handlers = self.eventHandlers[self.state]

            while len(self.events) > 0:
                event = self.events.pop()

                try:
                    handlers[event.name](event)
                except KeyError as e:
                    pass
        except KeyError as e:
            pass

    def to_string(self):
        """
        ToString method
        :return: current state
        """
        return self.state

    @staticmethod
    def is_event_relevant(threshold):
        """
        Function to differentiate relevant and irrelevant methods. Currently uses random number
        :param threshold: Threshold for relevance
        :return: Boolean
        """
        return random.random() < threshold


