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
from ..systemdynamics import Constant, Converter, Flow, Biflow, NaryOperator, Stock


###################
## MODEL CLASS ##
###################


class Model:
    """
    This is the main agent base / System dynamics / Hybrid model class
    It can run manually generated SD models, AB Models or define hybrid models.
    """


    def __init__(self, starttime=0, stoptime=0, dt=1,name="", scheduler=None,data_collector=None):
        """

        :param name: Name as string
        :param scheduler: Implemented instance of scheduler (e.g. simultaneousScheduler)
        :param data_collector: Instance of DataCollector)
        """

        self._caching_on = False

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
        """
        Set the scenario manager name
            :param scenario_manager: String
            :return: None
        """

        if not type(scenario_manager) == str:
            raise ValueError("Scenario manager name needs to be of type String")

        self.scenario_manager = scenario_manager

    def register_agent_factory(self, agent_type, agent_factory):
        """
        Register an agent factory
            :param agent_type: Type of agent to register
            :param agent_factory: Function (typically lambda, but not limited to). Input: agent_id, model -> Output: Agent of agent_type
            :return: None
        """
        log("[INFO] Registering agent factory for {}".format(agent_type))

        if type(agent_type) not in [str]:
            raise ValueError("agent_type param is not String but {}".format(type(agent_type)))


        self.agent_factories[agent_type] = agent_factory
        self.agent_type_map[agent_type] = []


    def reset(self):
        """
        Reset simulation
            :return:  None
        """

        for agent_type in self.agent_type_map:
            self.agent_type_map[agent_type] = []


        self.agents = []

        self.data_collector.agent_statistics = {}
        self.data_collector.event_statistics = {}

    def agent_ids(self, agent_type):
        """
        Receive agent ids for all agents of agent_type
            :param agent_type: agent type to get ids for
            :return: List
        """

        return self.agent_type_map[agent_type]

    def agent(self, agent_id):
        """
        Receive one agent by ID
            :param agent_id: ID of agent (int)
            :return: Agent object
        """

        return self.agents[agent_id]

    def create_agents(self, agent_spec):
        """
        Create agents
            :param agent_spec: Specification of Agent (dictionary)
            :return: None
        """
        log("[INFO] Creating {} agents of type {}".format(agent_spec["count"], agent_spec["name"]))

        for _ in range(agent_spec["count"]):
            self.create_agent(agent_spec["name"], agent_spec.get("properties"))

    def create_agent(self, agent_type, agent_properties):
        """
        Create one agent
            :param agent_type: Type of agent
            :return: None
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
        """
        Configure a property of the simulation
            :param property_spec: Specification of property (dictionary)
            :return:
        """
        self.properties[name] = property_spec

    def get_property(self, name):
        """
        Get one property
            :param name: Name of property
            :return: Dictionary for property
        """

        try:
            return_val = self.properties[name]
            return return_val
        except KeyError as e:
            return None

    def set_property_value(self, name, value):
        self.properties[name]["value"] = value

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

            # Lookup properties need to be added to the point dictionary also, for compatibility with SD models
            # this should be reworked once lookup handling is harmonized between sd and abm

            if self.properties[name]["type"] == "Lookup":
                self.points[name] = value


        super.__setattr__(self, name, value)

    def run_specs(self, starttime, stoptime, dt):
        """
        Configure the runspecs of the model.
            :param starttime: The starttime of the model.
            :param stoptime: The stoptime of the model.
            :param dt: The dt of the model.
            :return: None
        """

        log("[INFO] Setting starttime to {}, stoptime to {} and step to {}".format(starttime, stoptime, dt))
        self.starttime = starttime
        self.stoptime = stoptime
        self.dt = dt

    def run(self, show_progress_widget=False, collect_data=True):
        """
        Initiate simulation - this esssentially just calls the run method of the models scheduler.
            :param show_progress_widget: Boolean: If true, shows a progress widget (only in Jupyter environment!)
            :return: None
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
         """
        Should be called by a scheduler at the beginning of each round, before the agents act methods are called. Add any logic here that is needed to update dynamic properties.

            :param time: t
            :param sim_round: round number
            :param step: step number of round
            :return: None
        """

    def end_round(self, time, sim_round, step):
         """
        Should be called by a scheduler at the end of each round, before the agents act methods are called. Add any logic here that is needed to update dynamic properties.

            :param time: t
            :param sim_round: round number
            :param step: step number of round
            :return: None
        """
    def begin_episode(self, episode_no):
        """
        When running a simulation repeatedly in episodes, this method is called by the framework to allow tidy up at the beginning of an episode, e.g. a "soft" reset of the simulation. The default implementation calls begin_episode on each agent.

            :param episode_no: the number of the episode
            :return: None
        """
        for agent in self.agents:
            agent.begin_episode(episode_no)

    def end_episode(self, episode_no):
        """
        When running a simulation repeatedly in episodes, this method is called by the framework to allow tidy up at the end of an episode. The default implementation calls end_episode on each agent.
            :param episode_no: the number of the episode
            :return: None
        """

        for agent in self.agents:
            agent.end_episode(episode_no)

    def instantiate_model(self):
        """
        Instantiate model stub. Called directly after the model is instantiated. Implement this method in your model to perform any kind of initialization you may need.
            :return: None
        """

    def enqueue_event(self, event):
        """
        Called by the framework to enqueue events. In general you don't need to override this method.
            :param event: Event instance
            :return: None
        """

        if isinstance(event, Event):
            self.events.append(event)
        else:
            from BPTK_Py.exceptions import WrongTypeException
            raise WrongTypeException("{} is not an instance of BPTK_Py.Event".format(event))

    def next_agent(self, agent_type, state):
        """
        Get the next agent by type and state.
            :param agent_type: Agent type
            :param state: State the agent is in
            :return: Agent object
        """

        for agent in self.agents:

            if agent.agent_type == agent_type and agent.state == state:
                return agent

    def random_agents(self, agent_type, num_agents):
        """
        Receive a number of random agents
            :param agent_type: Type of agent
            :param num_agents:  Number of agents to receive
            :return: Agent IDs list
        """

        agent_map = self.agent_type_map[agent_type]

        num_agents_in_map = len(agent_map)

        actual_num_agents = min(num_agents, num_agents_in_map)

        agent_ids = []

        for _ in range(actual_num_agents):
            agent_ids.append(agent_map[Model.get_random_integer(0, num_agents_in_map - 1)])

        return agent_ids

    def random_events(self, agent_type, num_agents, event_factory):
        """
        Distribute a number of random events
            :param agent_type: Agent types supposed to receive events
            :param num_agents: Number of random agents
            :param event_factory: event factory (function) that creates an appropriate event for a given target agent_id
            :return: None.
        """
        agent_ids = self.random_agents(agent_type, num_agents)

        for agent_id in agent_ids:
            self.enqueue_event(event_factory(agent_id))

    def broadcast_event(self, agent_type, event_factory):
        """
        Broadcast an event to all agents of a particular agent_type
            :param agent_type: Agent types that are to receive the event
            :param event_factory: event factory (function) that creates an appropriate event for a given target agent_id
            :return:
        """

        if not type(agent_type) == str:
            from BPTK_Py.exceptions import  WrongTypeException
            raise WrongTypeException("param {} for agent_type is not of type str".format(agent_type))

        for agent_id in self.agent_type_map[agent_type]:
            self.enqueue_event(event_factory(agent_id))


    def configure(self, config):
        """
        Called to configure the model using a dictionary, which itself typically comes from a config file.
            :param config: Configuration dictionary
            :return: None
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
        """
        Get number of agents
            :param agent_type: Agent type to get count for
            :return: Number of agents (int)
        """
        return len(self.agent_type_map[agent_type])

    def agent_count_per_state(self, agent_type, state):
        """
        Get number of agents in a specific state
            :param agent_type: Agent type to get count for
            :param state: state of agents to get count for
            :return: Integer
        """
        agent_count = 0
        agent_ids = self.agent_type_map[agent_type]

        for agent_id in agent_ids:
            if self.agents[agent_id].state == state:
                agent_count += 1

        return agent_count

    def statistics(self):
        """
        Get statistics from DataCollector
            :return: None
        """

        try:
            return self.data_collector.statistics()
        except AttributeError as e:
            log("[ERROR] Tried to obtain Agent statistics but no data Collector available!")


    @staticmethod
    def get_random_integer(min_value, max_value):
        """
        Just compute a random integer within bounds
            :param min_value: min value for random integer
            :param max_value: max value for random integer
            :return: Integer
        """
        return round(random.random() * (max_value - min_value) + min_value)


    def lookup(self,x, points):
        """
        Lookup function: Interpolate between set of points. E.g. for "graphical functions" as known from SD
            :param x: x-value to find the y value for
            :param points:
            :return:
        """

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
        """
        An id that is unique within this model that can be used to generate unique equation names
        :return:
        """
        self.equation_id += 1
        return "bptk_"+str(self.equation_id)+"_"

    def equation(self,equation, arg):
        """
        This method only exists for making SD-DSL models compatible with the new SDModel equation API.
        In later steps, we might want to extend this method to allow for arrayed equations as well! However, first the DSL needs to support arrays as well!

            :param equation: equaiton name
            :param arg: t
        """
        return self.memoize(equation,arg)

    def memoize(self, equation, arg):
        """
        Memoize method - used by the system dynamics equations to remember values that have already been calculated.
            :param equation: name of equation
            :param arg: argument (t)
            :return: result of equation
        """
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
        """
        Add an equation. ALWAYS use this method to configure equations! Configures the memo as well!
            :param equation: Name of the equation
            :param lambda_method: A lambda function we can insert into the set of equations
            :return: None
        """
        if equation in self.equations.keys():
            log("[WARN] Hybrid Model {}: Overwriting equation {} ".format(str(self.name), str(equation)))

        self.equations[equation] = lambda_method

        # Initialize memo for equation
        self.memo[equation] = {}

    def stock(self, name):
        """
        Create a SD stock
            :param name: name of the stock
            :return: Stock object
        """
        if name in self.stocks:
            return self.stocks[name]
        else:
            stock = Stock(self, name)
            self.stocks[name] = stock
            return stock

    def function(self, name, fn):
        """
        Create a user defined function for SD models.
        :param name:  name of the function
        :param fn: returns
        :return: a nary function that creates a NaryFunction class
        """

        if name not in self.functions:
            self.functions[name] = lambda *args: NaryOperator(name, *args)
            self.fn[name] = fn

        return self.functions[name]

    def biflow(self, name):
        """
        Create a SD biflow
            :param name: Name of the biflow
            :return: Biflow object
        """
        if name in self.biflows:
            return self.biflows[name]
        else:
            flow = Biflow(self, name)
            self.biflows[name] = flow
            return flow

    def flow(self, name):
        """
        Create a SD flow
            :param name: Name of the flow
            :return: Flow object
        """
        if name in self.flows:
            return self.flows[name]
        else:
            flow = Flow(self, name)
            self.flows[name] = flow
            return flow

    def constant(self, name):
        """
        Create a SD constant
            :param name: Name of the constant
            :return: Constant object
        """
        if name in self.constants:
            return self.constants[name]
        else:
            constant = Constant(self, name)
            self.constants[name] = constant
            return constant

    def converter(self, name):
        """
        Create a converter
            :param name: Name of the converter
            :return: Converter object
        """
        if name in self.converters:
            return self.converters[name]
        else:
            converter = Converter(self, name)
            self.converters[name] = converter
            return converter

    def evaluate_equation(self, name, t):
        """
        Evaluate an element's equation
            :param name: Name of the equation
            :param t: timestep to evaluate for
            :return: float of simulation result
        """
        return self.memoize(name,t)

    def reset_cache(self):
        """
        Reset memo of all equations
            :return: None
        """
        for equation in self.memo:
            self.memo[equation] = {}






