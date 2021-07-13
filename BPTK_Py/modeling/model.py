#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2019 transentis labs GmbH
# MIT License


import random

import ipywidgets as widgets
import numpy as np
import math
from IPython.display import display
from scipy.interpolate import interp1d

from .agent import Agent
from .event import Event
from ..logger import log
from ..sddsl import Constant, Converter, Flow, Biflow, NaryOperator, Stock


class Model:
    """This is the main agent base / System dynamics / Hybrid model class

    It can run manually generated SD models, AB Models or define hybrid models.

    Args:
        name: String.
            Name of the model.
        scheduler: Scheduler.
            Scheduler object (e.g. simultaneousScheduler). This is configurable, so that you can add your own scheduling algorithms.
        data_collector: DataCollector
            Instance of DataCollector. This is configurable, so that you can add your own data collection algorithms.

    """


    def __init__(self, starttime=0, stoptime=0, dt=1,name="", scheduler=None,data_collector=None):

        self._caching_on = False

        # for ABM models
        self.properties = {}
        self.agents = []
        self.name = name
        self.agent_type_map = {}
        self.data_collector = data_collector
        self.scheduler = scheduler
        self.events = []

        # Global Model variables (for SD as well as ABM)
        self.starttime = starttime
        self.stoptime = stoptime
        self.dt = dt
        self.scenario_manager = ""


        ## For Hybrid Models (SD and AB)
        self.memo = {}
        self.equations = {}
        self.stocks = {}
        self.flows = {}
        self.biflows = {}
        self.converters = {}
        self.constants = {}
        self.points = {}
        self.functions = {}
        self.fn = {}
        self.equation_id = 0  # unique id used for internally generated functions

        # This is a placeholder. You may define SD model equations in your own 'instantiate_model' method and use them to generate hybrid models
        self.equations = {}

        self.agent_factories = {}

        for agent_type in self.agent_factories:
            self.agent_type_map[agent_type] = []

    @property
    def model(self):
        return self

    def set_scenario_manager(self, scenario_manager):
        """Set the name of the scenario manager that is handling this model. Used by bptk during scenario registration.
        
        Args:
            scenario_manager: String.
                Name of the scenario manager.
        """

        if not type(scenario_manager) == str:
            raise ValueError("Scenario manager name needs to be of type String")

        self.scenario_manager = scenario_manager

    def register_agent_factory(self, agent_type, agent_factory):
        """Register an agent factory.
        
        Agent factories are used at run-time to populate the model with agents. This method is used to register an agent factory, which is typically just a lambda function which returns an agent.
        
        Args:
            agent_type: String.
                Type of agent to register
            agent_factory: Function.
                Function that returns an agent given an id and the model. Typically a lambda, but not limited to that. Input: agent_id, model -> Output: Agent of agent_type
        """
        log("[INFO] Registering agent factory for {}".format(agent_type))

        if type(agent_type) not in [str]:
            raise ValueError("agent_type param is not String but {}".format(type(agent_type)))


        self.agent_factories[agent_type] = agent_factory
        self.agent_type_map[agent_type] = []


    def reset(self):
        """Reset the model.
        Cleara out all agents, agent and event statistics and resets the cache of SD equations. Keeps the agent factories though, so you could directly reconfigure the model using the configure method.
        """
        for agent_type in self.agent_type_map:
            self.agent_type_map[agent_type] = []

        self.agents = []

        self.data_collector.agent_statistics = {}
        self.data_collector.event_statistics = {}

        self.reset_cache()

    def agent_ids(self, agent_type):
        """Get agent IDs.
        
        Retrieve agent IDs for all agents of type agent_type.

        Args:
            agent_type: String.
                Agent type to get IDs for
        
        Returns:
            List of IDs 
        """

        return self.agent_type_map[agent_type]

    def agent(self, agent_id):
        """Get an agent by ID.
        
        Retrieve one agent by its ID

        Args:
            agent_id: Integer.
                ID of agent that is to be retrieved.
        
        Returns:
            Agent object
        """

        return self.agents[agent_id]

    def create_agents(self, agent_spec):
        """Create agents according to the agent specificaction.
        
        The agent specification is a dictionary containing the agent name and properties. Internally, this method then uses the registered agent factories to actually create the agents.
        
        Args:
            agent_spec: Dict.
                Specification of an agent using a dictionary with format {"name":<agent name>, "count": <initial count>}
        """
        log("[INFO] Creating {} agents of type {}".format(agent_spec["count"], agent_spec["name"]))

        for _ in range(agent_spec["count"]):
            self.create_agent(agent_spec["name"], agent_spec.get("properties"))

    def create_agent(self, agent_type, agent_properties):
        """Create one agent of the given type and with the given properties.
        
        Internally this method then uses the registered agent factories to actually create an agent.

        Args:
            agent_type: String.
                Type of agent
            agent_properties: Dict.
                The properties to initialize the agent with.
        """

        class NotAnAgentException(Exception):
            pass

        agent = self.agent_factories[agent_type](len(self.agents), self, agent_properties)

        if not isinstance(agent,Agent):
            raise NotAnAgentException("{} is not an instance of BPTK_Py.Agent. Please only use subclasses of Agent".format(agent))

        agent.initialize()
        self.agents.append(agent)
        self.agent_type_map[agent_type].append(agent.id)
        return agent

    def set_property(self, name, property_spec):
        """Configure a property of the model itself, as opposed to the properties of individual agents.

        Properties set via this mechanism are stored internally in a dictionary of properties, the value of the property directly can be access directly as an object attribute, i.e. as self.<name of property>.

        The key point about keeping properties in this way is that they can then easily be collected in a data collector.

        Args:
            name: String.
                Name of the property to set.
            property_spec: Dict.
                Specification of property: {"type":<type of property, free form string>,"value":<value of property>}. In principle the property can store any kind of value, the type is currently not evaluated by the framework.
        """
        #TODO: Currently model properties are not collected by the standard data collector and they are also not directly plotable. This might be a useful extension.
        self.properties[name] = property_spec

    def get_property(self, name):
        """
        Get a property of the model by name.
        
        The value of the model properties can also be accessed directly as a model attribute, i.e. as self.<name of property>

        Args:
            name: String.
                Name of property

        Returns:
            Dictionary for property
        """

        try:
            return_val = self.properties[name]
            return return_val
        except KeyError as e:
            return None

    def set_property_value(self, name, value):
        """Set the value of a model property by name.
        
        Model properties can also be set directly via the model attributes, i.e. as self.<nname of property>=<value of property>

        Args:
            name: String.
                Name of property.
            value: Any.
                Value of the property to set.
        """
        self.properties[name]["value"] = value

    def get_property_value(self, name):
        """
        Get a property of the model by name.
        
        The value of the model properties can also be accessed directly as a model attribute, i.e. as self.<name of property>

        Args:
            name: String.
                Name of property

        Returns:
            Value of the property.
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

            # Lookup properties need to be added to the point dictionary also, for compatibility with SD models
            # this should be reworked once lookup handling is harmonized between sd and abm

            #TODO Harmonize lookup handling between sd and abm
            if self.properties[name]["type"] == "Lookup":
                self.points[name] = value


        super.__setattr__(self, name, value)

    def run_specs(self, starttime, stoptime, dt):
        """Configure the runspecs of the model.

        Args:
            starttime: Integer.
                The starttime of the model.
            stoptime: Integer.
                The stoptime of the model.
            dt:
                The dt of the model.
        """

        log("[INFO] Setting starttime to {}, stoptime to {} and step to {}".format(starttime, stoptime, dt))
        self.starttime = starttime
        self.stoptime = stoptime
        self.dt = dt

    def run(self, show_progress_widget=False, collect_data=True):
        """Run the simulation.
        
        This esssentially just calls the run method of the models scheduler.
        
        Args:
            show_progress_widget: Boolean (Default=False).
                If True, shows a progress widget (only in Jupyter environment!)
            collect_data: Boolean (Default=True).
                If True, data is automatically collected in the models DataCollector, e.g. for plotting the model behaviour. If you are training the model e.g. using reinforcement learning, it might be useful to turn data collection of.

        """

        if show_progress_widget:
            progress_widget = widgets.FloatProgress(
                value=0.0,
                min=0.0,
                max=1.0,
                description='Running {}'.format(self.name),
                bar_style='info',
                orientation='horizontal',
                style = {'description_width': 'initial'}
            )

            out = widgets.Output()
            display(out)

            with out:
                display(progress_widget)

            self.scheduler.run(self,progress_widget,collect_data)
            out.clear_output()


        else:
            self.scheduler.run(self, None, collect_data)


    def begin_round(self, time, sim_round, step):
         """Called at the beginning of a simulation round.

        Should be called by the Scheduler at the beginning of each round, before the agents act methods are called. Add any logic here that is needed to update dynamic properties.

        Args:
            time: Integer.
                The current timestep of the simulation, i.e.(round+step*dt)
            sim_round: Integer
                The current round of the simulation.
            step:  Integer.
                The step number of round
        """

    def end_round(self, time, sim_round, step):
         """Called at end of a simulation round.

        Should be called by the Scheduler at the end of each round, before the agents act methods are called. Add any logic here that is needed to update dynamic properties.
        
        Args:
            time: Integer.
                The current timestep of the simulation, i.e.(round+step*dt)
            sim_round: Integer
                The current round of the simulation.
            step:  Integer.
                The step number of round

        """
    def begin_episode(self, episode_no):
        """Called at beginning of an episode.

        When running a simulation repeatedly in episodes (e.g. because you are training the model using reinforcement learning), this method is called by the framework to allow tidy up at the beginning of an episode, e.g. a "soft" reset of the simulation.
        
        The default implementation calls begin_episode on each agent.
        
        Args:
            episode_no: Integer.
                The number of the episode
        """

        for agent in self.agents:
            agent.begin_episode(episode_no)

    def end_episode(self, episode_no):
        """Called at the end of an episode.

        When running a simulation repeatedly in episodes, this method is called by the framework to allow tidy up at the end of an episode.
        
        The default implementation calls end_episode on each agent.

        Args:
            episode_no: Integer.
                The number of the episode
        """

        for agent in self.agents:
            agent.end_episode(episode_no)

    def instantiate_model(self):
        """Set properties during model initialization.

        This method does nothing in the parent class and can be overriden in child classes. It is called by the frame directly after the model is instantiated.
        
        Implement this method in your model to perform any kind of initialization you may need. Typically you would register your agent factories hier and set up model properties.
        """
        pass

    def enqueue_event(self, event):
        """Called by the framework to enqueue events.
        
        In general you don't need to override this method or call it directly.

        Args:
            event: Event.
                Instance of the event.
        """

        if isinstance(event, Event):
            self.events.append(event)
        else:
            from BPTK_Py.exceptions import WrongTypeException
            raise WrongTypeException("{} is not an instance of BPTK_Py.Event".format(event))

    def next_agent(self, agent_type, state):
        """Get the next agent by type and state.

        Runs through the internal agent store and retrieves the first agent that matches in type and state.

        Args:
            agent_type: String.
                Agent type
            state: String.
                State the agent is in

        Returns:
            The first agent object that matches the criterian None otherwise.
        """

        for agent in self.agents:

            if agent.agent_type == agent_type and agent.state == state:
                return agent

        return None

    def random_agents(self, agent_type, num_agents):
        """Retreive a number of random agents

        Args:
            agent_type: String.
                Type of agent to retrieve.
            num_agents:
                Number of agents of this type to retreive. 

        Returns:
            List of agent IDs. The number of IDs might be less then num_agents if fewer agents are available.
        """

        agent_map = self.agent_type_map[agent_type]

        num_agents_in_map = len(agent_map)

        actual_num_agents = min(num_agents, num_agents_in_map)

        agent_ids = []

        for _ in range(actual_num_agents):
            agent_ids.append(agent_map[Model.get_random_integer(0, num_agents_in_map - 1)])

        return agent_ids

    def random_events(self, agent_type, num_agents, event_factory):
        """Distribute events to a number of random agents

        Args:
            agent_type: String.
                Agent type that is to receive the event
            num_agents: Integer.
                Number of random agents that should receive the event
            event_factory: Function.
                The factory (typicalla a lambda function) that generates the desired event for a given target agent type. The function receives the agent_id as its parameter.
        """
        agent_ids = self.random_agents(agent_type, num_agents)

        for agent_id in agent_ids:
            self.enqueue_event(event_factory(agent_id))

    def broadcast_event(self, agent_type, event_factory):
        """
        Broadcast an event to all agents of a particular agent_type

        Args:
            agent_type: String.
                Agent type that is to receive the event
            num_agents: Integer.
                Number of random agents that should receive the event
            event_factory: Function.
                The factory (typicalla a lambda function) that generates the desired event for a given target agent type. The function receives the agent_id as its parameter.
        """

        if not type(agent_type) == str:
            from BPTK_Py.exceptions import  WrongTypeException
            raise WrongTypeException("param {} for agent_type is not of type str".format(agent_type))

        for agent_id in self.agent_type_map[agent_type]:
            self.enqueue_event(event_factory(agent_id))


    def configure(self, config):
        """
        Called to configure the model using a dictionary. This method is called by the framework if you instantiate models from scenario files. But you can also call the method directly.

        Args:
            config: Dict.
                Dictionary containing the config: {"runspecs":<dictionary of runspecs>,"properties":<dictionary of properties>,"agents":<list of agent-specs>}.
        """
        self.run_specs(config["runspecs"]["starttime"], config["runspecs"]["stoptime"], config["runspecs"]["dt"])

        properties = config["properties"]

        if type(properties) == list:
            for property in properties:
                try:
                    prop_name = property["name"]
                    prop_val = property["value"]
                    prop_type = property["type"]
                except KeyError as e:
                    prop_name = list(property.keys())[0]
                    prop_val = property[prop_name]["value"]
                    prop_type = property[prop_name]["type"]

                self.set_property(prop_name,prop_val)

                if prop_type == "Lookup":
                    self.points[prop_name] = prop_val

        else:
            for name, property in properties.items():

                self.set_property(name, property)

                #Lookup properties need to be added to the point dictionary also, for compatibilty with SD models

                if property["type"] == "Lookup":
                    self.points[name] = property["value"]

        agents = config["agents"]

        for agent in agents:
            self.create_agents(agent)

    def agent_count(self, agent_type):
        """Get count of agents of a given type.

        Args:
            agent_type: String.
                Agent type to get count for
        
        Returns:
            Integer. Number of agents (Integer)
        """
        return len(self.agent_type_map[agent_type])

    def agent_count_per_state(self, agent_type, state):
        """
        Get number of agents in a specific state
         
        Args:
            agent_type: String.
                Agent type to get count for
            state: String.
                The state of agents to get count for
        
        Returns:
            Integer.

        """
        agent_count = 0
        agent_ids = self.agent_type_map[agent_type]

        for agent_id in agent_ids:
            if self.agents[agent_id].state == state:
                agent_count += 1

        return agent_count

    def statistics(self):
        """Get statistics from DataCollector
        
        Returns: 
            The DataCollector used to collect the simulation statistics.
        """

        try:
            return self.data_collector.statistics()
        except AttributeError as e:
            log("[ERROR] Tried to obtain Agent statistics but no data Collector available!")


    @staticmethod
    def get_random_integer(min_value, max_value):
        """A random integer within bounds

        This method is useful for simulating random behaviour.

        Args:
            min_value: Integer.
                Min value for random integer
            max_value: Integer.
                max value for random integer
        
        Returns:
            Random integer.
        """
        return round(random.random() * (max_value - min_value) + min_value)


    def _lookup(self,x, points):
        """Define a lookup function.
        
        Function that interpolate between set of points. This is used by the SD DSL lookup function.
        
        Args:
            x: Value.
                x-value to find the y value for
            points: List.
                List of coordinates.
        
        Returns: Float.
            Returns the value that has been looked up.
        """

        #This is used internally by SD DSL lookup function / the Lookup operator.

        if type(points) is str:
            points = self.points[points]


        x_vals = np.array([x[0] for x in points])
        y_vals = np.array([x[1] for x in points])

        if x <= x_vals[0]:
            return y_vals[0]

        if x >= x_vals[len(x_vals) - 1]:
            return y_vals[len(x_vals) - 1]

        f = interp1d(x_vals, y_vals)
        return float(f(x))


    def plot_lookup(self,lookup_names,config=None):
        """
        Plots lookup functions for the given list of lookup names

        Args:
            lookup_names: String or List.
                A name or list of names of lookup functions. The list can be passed as a Python list or a comma separated string.
        """
        #TODO write test for plot_lookup
        from ..util import lookup_data
        from ..visualizations import visualizer

        if not config:
            from ..config import config

        lookup_names = lookup_names if type(lookup_names) is list else lookup_names.split(",")

        df = lookup_data(self, lookup_names)


        return visualizer(config).plot(df=df,
                                    return_df=False,
                                    visualize_from_period=0,
                                    visualize_to_period=0,
                                    stacked=config.configuration["stacked"],
                                    kind=config.configuration["kind"],
                                    title=str(lookup_names).replace("[","").replace("]","").replace("\'",""),
                                    alpha=config.configuration["alpha"],
                                    x_label="",
                                    y_label="",
                                    start_date="",
                                    freq="",
                                    series_names={})





    ################################################################################################################################################
    ### System Dynamics (SD) / Hybrid Simulation handling. Use the following methods for Hybrid models: Agent based models that use SD equations  ##
    ################################################################################################################################################

    @property
    def equation_prefix(self):
        """An id that is unique within this model that can be used to generate unique equation names
        
        Returns: 
            Integer. An id that is unique within the model.
        """
        self.equation_id += 1
        return "bptk_"+str(self.equation_id)+"_"

    def equation(self,equation, t):
        #TODO this is the same as the evaluate_equation method. Replace it.
        return self.memoize(equation,t)

    def memoize(self, equation, arg):
        
        #TODO: consider making this into an internal method

        try:
            mymemo = self.memo[equation]
        except:
            # In case the equation does not exist in memo
            self.memo[equation] = {}
            mymemo = self.memo[equation]
        if arg in mymemo.keys():
            return mymemo[arg]
        else:
            result = self.equations[equation](arg)
            mymemo[arg] = result

        return result

    def add_equation(self, equation, lambda_method):

        #TODO Consider making this an internal method.
        
        if equation in self.equations.keys():
            log("[WARN] Hybrid Model {}: Overwriting equation {} ".format(str(self.name), str(equation)))

        self.equations[equation] = lambda_method

        # Initialize memo for equation
        self.memo[equation] = {}

    def stock(self, name):
        """Create a System Dynamics stock

        Args:
            name: String.
                Name of the stock.

        Returns: 
            The stock object.
        """
        if name in self.stocks:
            return self.stocks[name]
        else:
            stock = Stock(self, name)
            self.stocks[name] = stock
            return stock

    def function(self, name, fn):
        """Create a user defined function for System Dynamics.

        Args:
            name:  String.
                Name of the function.
            fn: returns

        Returns: 
        A function which wraps the user defined function for use within System Dynamics.
        """

        if name not in self.functions:
            self.functions[name] = lambda *args: NaryOperator(name, *args)
            self.fn[name] = fn

        return self.functions[name]

    def biflow(self, name):
        """Create a System Dynamics biflow

        Args:
            name: String.
                Name of the biflow
        Returns: 
            A Biflow object
        """
        if name in self.biflows:
            return self.biflows[name]
        else:
            flow = Biflow(self, name)
            self.biflows[name] = flow
            return flow

    def flow(self, name):
        """Create a System Dynamics flow

        Args:
            name: String.
                Name of the flow
        Returns:
            A Flow object
        """
        if name in self.flows:
            return self.flows[name]
        else:
            flow = Flow(self, name)
            self.flows[name] = flow
            return flow

    def constant(self, name):
        """Create a System Dynamics constant

        Args:
            name: String.
                Name of the constant
        
        Returns: Constant.
            A Constant object
        """
        if name in self.constants:
            return self.constants[name]
        else:
            constant = Constant(self, name)
            self.constants[name] = constant
            return constant

    def converter(self, name):
        """Create a System Dynamics converter

        Args:
            name: String.
                Name of the converter

        Returns: 
            A Converter object
        """
        if name in self.converters:
            return self.converters[name]
        else:
            converter = Converter(self, name)
            self.converters[name] = converter
            return converter

    def evaluate_equation(self, name, t):
        """Evaluate an System Dynamics element's equation at timestep t.

        Args:
            name: String.
                Name of the equation.
            t: Float.
                Timestep to evaluate for
        
        Return: Float
            The value of the equation at time t.
        """
        return self.memoize(name,t)

    def reset_cache(self):
        """Reset cache of all System Dynamics equations.
        """
        for equation in self.memo:
            self.memo[equation] = {}






