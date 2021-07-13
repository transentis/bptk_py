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
    """Agent for agent based simulation.
    Your agents must inherit from this class if they are to be part of an agent-based simulation.

    Args:
        agent_id: Integer.
            Id of agent. Model should manage this. Do use agent factories!
        model: Model instance
            The agent-based model this agent will be part of.
        properties: Dictionary of agent properties. These properties will be available as object attributes (i.e. via self.<name of property>)
    """

    def __init__(self, agent_id, model, properties,agent_type="agent"):

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
        """Serialize the agent.

        Returns:
            Returns a dictionary containing all relevant agent data: id, state, type and all properties.
        """

        output = {}
        for key, value in self.properties.items():
            output[key] = self.properties[value]['value']

        output['id'] = self.id
        output['state'] = self.state
        output['type'] = self.agent_type

        return output

    def register_event_handler(self, states, event, handler):
        """Register an event handler.

        The event handler is called by the framework if a relevant event occurs. The event handler is registered for all relevant state.

        Args:
            states: List.
                List of states (String) for which the event handler is valid
            event: String
                The type of event the handler reacts to.
            handler: Function.
                The actual event handler. This must be a function that accept the event as its parameter. Typically this will be a method of the agent class.
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
        Receive an event.

        Parameters:
         event: Event instance.
            The event that the agent receives.
        """
        from BPTK_Py import Event
        if not isinstance(event,Event):
            raise ValueError("event param is not an instance of BPTK_Py.Event. Can only handle instances of Event, including subclasses")
        self.events.append(event)

    def initialize(self):
        """Initialize the agent.
        
        Called by the framework directly after the agent is instantiated, useful for any kind of initialization code such as setting the agent type, current state and registering event handlers.
        """
        pass

    def set_property(self, name, data):
        """
        Configure an agent property by passing a dictionary specifying the property.

        Parameters:
            name: String.
                The name of the property whose data is being set.
            data: Dictionary.
                Specification of property in dictionary with keys type and values. Currently the types Double, String, Integer, Lookup, Dictionary, Boolean and Agent are supported.
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

        Parameters:
            name: String.
                The name of the property to set.
            value: (Agent|Dictionary|Double|Integer|String|Array of Points). 
                The value of the property to set.
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
        Get the settings of a property.

        Parameters:
            name: String.
                Name of property

        Returns:
            Dictionary with keys type and value.
        """

        try:
            data = self.properties[name]
            return data
        except KeyError as e:
            raise e

    def get_property_value(self, name):
        """
        Retrieves the value of a property.

        Parameters:
            name: String.
                The name of the property whose value is to be retrieved.
        Returns:
            The value of the property.
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
        """Handle an event immediately, do not wait for the next round.

        Parameters:
            event: event instance.
                Event that the agent receives.
        """

        try:
            return self.eventHandlers[self.state][event.name](event)
        except KeyError as e:
            raise e

    def handle_events(self, time, sim_round, step):
        """Called by the framework to handle events.

        This method then calls the registered event handlers.

        Args:
            time: Float.
                The current simulation time (sim_round+dt*step)
            sim_round: Integer.
                The current simulation round.
            step: Integer. 
                The current simulation step (within the round).
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

    def act(self, time, round_no, step_no):
        """Called by the scheduler every timestep.
        
        Does nothing in the base class, typically agents will implement most of their action logic in this method (and in the event handlers).

        Args:
            time: Float.
                This is the current simulation time (equivalent to round_no+step_no*dt)
            round_no: Integer.
                The current round.
            step_no: Integer.
                The current step (within the round)
        """
        pass

    def begin_episode(self, episode_no):
        """Called by the framework at the beginning of each episode.
        
        Useful to allow a soft reset of the agent, e.g. when training a model for reinforcement learning.
        
        The default implementation does nothing.

        Args:
            episode_no: Integer.
                The number of the episode.
        """
        pass


    def end_episode(self, episode_no):
        """Called by the framework at the end of each epsiode, to allow tidy up if necessary. The default implementation does nothing.

        Args:
            episode_no: Integer.
                The number of the episode
        """
        pass


    def to_string(self):
        #TODO might want to rename this or just remove it ...
        return self.state

    @staticmethod
    def is_event_relevant(threshold):
        """Helper function used to differentiate relevant and irrelevant events.
        
        The function generates a random number in the range [0.0, 1.0) using Pythons random.random(). If this is smaller than the threshold, the event is deemed relevant.
        
        Args:
            threshold: Float.
                Threshold for relevance, should be in the range [0.0,1.0]
        Returns: 
            Boolean
        """
        return random.random() < threshold


