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
        Initializes the agent and sets its id, model and properties.
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
        Serialize the agent.
         :return: Returns a dictionary containing the agent state
        """

        output = {}
        for key, value in self.properties.items():
            output[key] = self.properties[value]['value']

        output['id'] = self.id
        output['state'] = self.state
        output['type'] = self.agent_type

        return output

    def register_event_handler(self, states, event, handler):
        """
        Register an event handler.
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
        Initialize the agent - called by the framework directly after the agent is instantiated, useful for any kind of initialization code.
         :return: None
        """

    def set_property(self, name, data):
        """
        Configure an agent property by passing a dictionary specifying the property.
         :param name: The name of the property whose data is being set.
         :param data: Specification of property (dictionary)
         :return:
        """
        if not self.properties:
            self.properties = dict()

        self.properties[name] = data

    def set_property_value(self, name, value):
        """
        Sets the value of a property.
         :param name: The name of the property to set.
         :param value: The value of the property to set.
         :return:
        """
        self.properties[name]["value"] = value

    def get_property(self, name):
        """
        Get one property
         :param name: Name of property
         :return: Dictionary for property
        """

        try:
            data = self.properties[name]
            return data
        except KeyError as e:
            return None

    def get_property_value(self, name):
        """
        Retrieves the value of a property.
         :param name: The name of the property whose value is to be retrieved.
         :return: The value of the property.
        """
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

    def handle_events(self, time, sim_round, step):
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

    def act(self, time, round_no, step_no):
        """
        This method is called by the scheduler every timestep. Agents implement their logic here.
         :param time:     this is the current simulation time (equivalent to round_no+step_no*dt)
         :param round_no: round number
         :param step_no:  step number of round
         :return: None
        """

    def to_string(self):
        """
        ToString method
         :return: current state
        """
        return self.state

    @staticmethod
    def is_event_relevant(threshold):
        """
        Function to differentiate relevant and irrelevant events. It generates a random number – if this is smaller than the threshold, the event is deemed relevant.
         :param threshold: Threshold for relevance
         :return: Boolean
        """
        return random.random() < threshold


