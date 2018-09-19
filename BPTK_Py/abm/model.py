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
import threading

import ipywidgets as widgets
import numpy as np
from IPython.display import display
from scipy.interpolate import interp1d

from ..logger import log


###################
## ABMODEL CLASS ##
###################


class ABModel:
    """
    This is the main agent base model
    """

    def __init__(self, name, scheduler, data_collector=None):
        """

        :param name: Name as string
        :param scheduler: Implemented instance of scheduler (e.g. simultaneousScheduler)
        :param data_collector: Instance of DataCollector)
        """

        self.properties = {}
        self.agents = []
        self.name = name
        self.agent_type_map = {}
        self.data_collector = data_collector
        self.scheduler = scheduler
        self.events = []

        # Global Model variables (for SD as well as ABM)
        self.starttime = 0
        self.stoptime = 0
        self.dt = 1
        self.scenario_manager = ""
        self.memo = {}

        # This is a placeholder. You may define SD model equations in your own 'instantiate_model' method and use them to generate hybrid models
        self.equations = {}

        self.agent_factories = {}

        for agent_type in self.agent_factories:
            self.agent_type_map[agent_type] = []

    def set_scenario_manager(self, scenario_manager):
        """
        Set the scenario manager name
        :param scenario_manager: String
        :return: None
        """
        self.scenario_manager = scenario_manager

    def register_agent_factory(self, agent_type, agent_factory):
        """
        Register an agent factory
        :param agent_type: Type of agent to register
        :param agent_factory: Function (typically lambda, but not limited to). Input: agent_id, model -> Output: Agent of agent_type
        :return: None
        """
        log("[INFO] Registering agent factory for {}".format(agent_type))

        self.agent_factories[agent_type] = agent_factory
        self.agent_type_map[agent_type] = []

    def reset(self):
        """
        Reset simulation
        :return:  None
        """

        for agent_type in self.agent_type_map:
            self.agent_type_map[agent_type] = []

        # all else can be changed

        self.properties = {}
        self.agents = []

        self.starttime = 0
        self.stoptime = 0
        self.dt = 1

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
            self.create_agent(agent_spec["name"])

    def create_agent(self, agent_type):
        """
        Create one agent
        :param agent_type: Type of agent
        :return: None
        """
        agent = self.agent_factories[agent_type](len(self.agents), self)
        agent.initialize()
        self.agents.append(agent)
        self.agent_type_map[agent_type].append(agent.id)

    def set_property(self, property_spec):
        """
        Configure a property of the simulaiton
        :param property_spec: Specification of property (dictionary)
        :return:
        """
        self.properties[property_spec["name"]] = property_spec

    def get_property(self, name):
        """
        Get one property
        :param name: Name of property
        :return: Dictionary for property
        """
        if name not in self.properties:
            log("[ERROR] sim.getProperty: property unknown")

        try:
            return_val = self.properties[name]
            return return_val
        except KeyError as e:
            log("[ERROR] sim.getProperty: property unknown")
            return None



    def run_specs(self, starttime, stoptime, dt):
        """
        Configure
        :param starttime:
        :param stoptime:
        :param dt:
        :return:
        """

        log("[INFO] Setting starttime to {}, stoptime to {} and step to {}".format(starttime, stoptime, dt))
        self.starttime = starttime
        self.stoptime = stoptime
        self.dt = dt

    def run(self, show_progress_widget=False):
        """
        Initiate simulation
        :param show_progress_widget: Boolean: If true, shows a progress widget (only in Jupyter environment!)
        :return: None
        """

        if show_progress_widget:
            progress_widget = widgets.FloatProgress(
                value=0.0,
                min=0.0,
                max=1.0,
                description='Running',
                bar_style='info',
                orientation='horizontal'
            )

            thread = threading.Thread(target=self.scheduler.run, args=(self, progress_widget,))
            display(progress_widget)
            thread.start()
            thread.join()
        else:
            self.scheduler.run(self, None)

    def instantiate_model(self):
        """
        Instantiate model stub. Implement this method in your model!
        :return: None
        """
        print("IMPLEMENT THIS METHOD IN AN INHERITING CLASS!")

    def enqueue_event(self, event):
        """
        Add one event
        :param event: Event instance
        :return: None
        """
        self.events.append(event)

    def next_agent(self, agent_type, state):
        """
        Get the next agent by type and state
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
            agent_ids.append(agent_map[ABModel.get_random_integer(0, num_agents_in_map - 1)])

        return agent_ids

    def random_events(self, agent_type, num_agents, event_factory):
        """
        Distribute a number of random events
        :param agent_type: Agent types supposed to receive events
        :param num_agents: Number of random agents
        :param event_factory: Agent factory that creates the events (function)
        :return:
        """
        agent_ids = self.random_agents(agent_type, num_agents)

        for agent_id in agent_ids:
            self.enqueue_event(event_factory(agent_id))

    def configure(self, config):
        """
        Configure the model using a dictionary
        :param config: Configuration dictionary
        :return: None
        """

        self.run_specs(config["runspecs"]["starttime"], config["runspecs"]["stoptime"], config["runspecs"]["dt"])

        properties = config["properties"]

        for sim_property in properties:
            self.set_property(sim_property)

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
            return_val = self.data_collector.statistics()
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

    @staticmethod
    def lookup(x, points):
        """
        Lookup function: Interpolate between set of points. E.g. for "graphical functions" as known from SD
        :param x: x-value to find the y value for
        :param points:
        :return:
        """
        x_vals = np.array([x[0] for x in points])
        y_vals = np.array([x[1] for x in points])

        if x <= x_vals[0]:
            return y_vals[0]

        if x >= x_vals[len(x_vals) - 1]:
            return y_vals[len(x_vals) - 1]

        f = interp1d(x_vals, y_vals)
        return float(f(x))

    ### Hybrid Simulation handling. Use the following methods for Hybrid models: Agent based models that use SD equations

    def memoize(self, equation, arg):
        """
        Memoize method
        :param equation: name of equation
        :param arg: argument (t)
        :return: result of equation
        """
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
