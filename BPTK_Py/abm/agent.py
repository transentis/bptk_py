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
import copy



#################
## AGENT CLASS ##
#################

class Agent:
    """
    Agent for agent based simulation. A simulation requires the implementation of at least one inheriting class
    An agent does things in the simulation and interacts with others
    """

    def __init__(self, agent_id, model, properties,agent_type="agent"):
        """
        Initializes the agent and sets its id, model and properties.
         :param agent_id: id of agent. Model should manage this. Do use agent factories!
         :param model: Model instance
         :param properties: Dictionary of agent properties
        """

        from .model import Model
        if not isinstance(model,Model):
            raise ValueError("model parameter is not subclass of BPTK_Py.Model")

        if type(agent_id) not in [float,int]:
            raise ValueError("agent_id is not of type float or int")

        if type(agent_type) not in [str]:
            raise ValueError("agent_type is not of type String")

        if not properties:
            properties = {}

        if type(properties) not in [dict]:
            raise ValueError("properties is not of type dict")

        self.model = model
        self.events = []

        self.id = agent_id
        self.state = "active"
        self.agent_type = agent_type
        self.properties = copy.deepcopy(properties)
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

        if type(states) not in [list]:
            raise ValueError("states is not of type list")

        if type(event) not in [str]:
            raise ValueError("event is not of type string")


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
        from BPTK_Py import Event
        if not isinstance(event,Event):
            raise ValueError("event param is not an instance of BPTK_Py.Event. Can only handle instances of Event, including subclasses")
        self.events.append(event)

    def initialize(self):
        """
        Initialize the agent - called by the framework directly after the agent is instantiated, useful for any kind of initialization code.
         :return: None
        """
        pass

    def set_property(self, name, data):
        """
        Configure an agent property by passing a dictionary specifying the property.
         :param name: The name of the property whose data is being set.
         :param data: Specification of property (dictionary)
         :return:
        """


        if not type(name) in [str]:
            raise ValueError("name param has to be a string")

        try:
            prop_type = data["type"]
            if prop_type not in ["Double","String","Integer","Lookup","Dictionary","Boolean","Agent"]:
                raise ValueError("prop type {} is wrong. Supported types: String, Integer, Double, Lookup".format(prop_type))
        except KeyError as e:
            raise e
        except ValueError as e:
            raise e

        try:
            from BPTK_Py.exceptions import WrongTypeException
            value = data["value"]
            if prop_type == "Double":
                try:
                    value = float(value)
                except:
                    raise WrongTypeException(
                        "property type for {} says Double but {} is not a floating point number.".format(name, value))
            if prop_type == "String" and not type(value) == str:
                raise WrongTypeException("property type for {} says String but {} is not a String.".format(name, value))
            if prop_type == "Integer":
                try:
                    value = int(value)
                except:
                    raise WrongTypeException(
                        "property type for {} says Integer but {} is not an Integer.".format(name, value))
        except KeyError as e:
            raise e


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

        if name not in self.properties.keys():
            raise KeyError("property {} does not exist".format(name))

        prop_type = self.properties[name]["type"]

        from BPTK_Py.exceptions import WrongTypeException
        prop_value = value
        if prop_type == "Double":
            try:
                value = float(value)
            except:
                raise WrongTypeException("property type for {} says Double but {} is not a floating point number.".format(name,value))
        if prop_type == "String" and not type(prop_value) == str:
            raise WrongTypeException("property type for {} says String but {} is not a String.".format(name,value))
        if prop_type == "Dictionary" and not type(prop_value) == dict:
            raise WrongTypeException("property type for {} says Dictionary but {} is not a Dictionary.".format(name, value))
        if prop_type == "Integer":
            try:
                value = int(value)
            except:
                raise WrongTypeException("property type for {} says Integer but {} is not an Integer.".format(name,value))

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
            raise e

    def get_property_value(self, name):
        """
        Retrieves the value of a property.
         :param name: The name of the property whose value is to be retrieved.
         :return: The value of the property.
        """

        if name not in self.properties.keys():
            raise AttributeError("{} is not a valid property".format(name))

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
        else:
            super.__setattr__(self, name, value)

    def receive_instantaneous_event(self, event):
        """
        Handle an event immediately, do not wait for another round
         :param event: event instance
         :return: None
        """

        try:
            return self.eventHandlers[self.state][event.name](event)
        except KeyError as e:
            raise e

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
        pass

    def begin_episode(self, episode_no):
        """
        This method is called by the simulation at the beginning of an episode, e.g. to allow a soft reset of the agent. The default implementation does nothing.

            :param episode_no: the number of the episode
            :return: None
        """
        pass


    def end_episode(self, episode_no):
        """
        This method is called by the simulation at the end of an epsiode, to allow tidy up if necessary. The default implementation does nothing.

            :param episode_no: the number of the episode
            :return: None
        """
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
        Function to differentiate relevant and irrelevant events. It generates a random number – if this is smaller than the threshold, the event is deemed relevant.
         :param threshold: Threshold for relevance
         :return: Boolean
        """
        return random.random() < threshold


