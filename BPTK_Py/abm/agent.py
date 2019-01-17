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

    def __init__(self, agent_id, model, properties):
        """

        :param agent_id: id of agent. Model should manage this. Do use agent factories!
        :param model: Model instance
        :param properties: Dictionary of agent properties
        """
        self.model = model
        self.events = []
        self.id = agent_id
        self.state = "active"
        self.agent_type = "agent"
        self.properties = properties
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

    def set_property(self, name, data):
        """
        Configure an agent property
        :param property_spec: Specification of property (dictionary)
        :return:
        """
        if not self.properties:
            self.properties = dict()

        self.properties[name] = data

    def set_property_value(self, name, value):
        self.properties[name]["value"] = value

    def get_property(self, name):
        """
        Get one property
        :param name: Name of property
        :return: Dictionary for property
        """
        if name not in self.properties:
            log("[ERROR] agent.get_property: property unknown")

        try:
            data = self.properties[name]
            return data
        except KeyError as e:
            log("[ERROR] agent.get_property: property unknown")
            return None

    def get_property_value(self, name):
        return self.properties[name]["value"]

    # overriding getattr and setattr to ensure that properties in self.properties can be accessed as object attributes

    def __getattr__(self, name):
        if self.__dict__.get("properties") and name in self.__dict__.get("properties"):
            return self.get_property_value(name)
        else:
            if self.__dict__.get(name):
                return self.__dict__.get(name)
            else:
                raise AttributeError('{0}.{1} is invalid.'.format(self.__class__.__name__, name))


    def __setattr__(self, name, value):
        if self.__dict__.get("properties") and name in self.__dict__.get("properties"):
            self.set_property_value(name, value)

        super.__setattr__(self, name, value)

    def receive_instantaneous_event(self, event):
        """
        Handle an event immediately, do not wait for another round
        :param event: event instance
        :return: None
        """

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


