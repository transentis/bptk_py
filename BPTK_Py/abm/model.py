import math
import random
from BPTK_Py import log
import threading
from IPython.display import display
import ipywidgets as widgets
import numpy as np
from scipy.interpolate import interp1d

class ABModel:
    """
    This is the main agent base model
    """

    def __init__(self,name,  scheduler, data_collector=None):


        self.properties = {}
        self.agents = []
        self.name = name
        self.agent_type_map = {}
        self.data_collector = data_collector
        self.scheduler = scheduler
        self.events = []
        self.start_time = 0
        self.stop_time = 0
        self.step = 1
        self.agent_factories = {}

        # This is placeholder. You may define SD model equations in your own 'instantiate_model' method and use them to generate hybrid models
        self.equations = {}


        for agent_type in self.agent_factories:
            self.agent_type_map[agent_type] = []

    def register_agent_factory(self, agent_type, agent_factory):
        log("[INFO] Registering agent factory for {}".format(agent_type))

        self.agent_factories[agent_type] = agent_factory
        self.agent_type_map[agent_type] = []

    def reset(self):

        for agent_type in self.agent_type_map:
            self.agent_type_map[agent_type] = []

        # all else can be changed

        self.properties = {}
        self.agents = []

        self.start_time = 0
        self.stop_time = 0
        self.step = 1

    def agent_ids(self, agent_type):

        return self.agent_type_map[agent_type]

    def agent(self, agent_id):

        return self.agents[agent_id]

    def create_agents(self, agent_spec):
        log("[INFO] Creating {} agents of type {}".format(agent_spec["count"], agent_spec["name"]))

        for _ in range(agent_spec["count"]):
            self.create_agent(agent_spec["name"])

    def create_agent(self, agent_type):
        agent = self.agent_factories[agent_type](len(self.agents), self)
        agent.initialize()
        self.agents.append(agent)
        self.agent_type_map[agent_type].append(agent.id)

    def set_property(self, property_spec):
        self.properties[property_spec["name"]] = property_spec

    def get_property(self, name):
        if name not in self.properties:
            log("[ERROR] sim.getProperty: property unknown")

        return self.properties[name]

    def run_specs(self, start_time, stop_time, step):

        log("[INFO] Setting starttime to {}, stoptime to {} and step to {}".format(start_time, stop_time, step))
        self.start_time = start_time
        self.stop_time = stop_time
        self.step = step

    def run(self, show_progress_widget=False):

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
        print("IMPLEMENT THIS METHOD IN AN INHERITING CLASS!")


    def enqueue_event(self, event):
        self.events.append(event)

    def next_agent(self, agent_type, state):

        for agent in self.agents:

            if agent.agent_type == agent_type and agent.state == state:

                return agent

    def random_agents(self, agent_type, num_agents):

        agent_map = self.agent_type_map[agent_type]

        num_agents_in_map = len(agent_map)

        actual_num_agents = min(num_agents, num_agents_in_map)

        agent_ids = []

        for _ in range(actual_num_agents):
            agent_ids.append(agent_map[ABMModel.get_random_integer(0, num_agents_in_map - 1)])

        return agent_ids

    def random_events(self, agent_type, num_agents, event_factory):
        agent_ids = self.random_agents(agent_type, num_agents)

        for agent_id in agent_ids:
            self.enqueue_event(event_factory(agent_id))

    def configure(self, config):

        self.run_specs(config["runspecs"]["start"], config["runspecs"]["stop"], config["runspecs"]["step"])

        properties = config["properties"]

        for sim_property in properties:
            self.set_property(sim_property)

        agents = config["agents"]

        for agent in agents:
            self.create_agents(agent)

    def agent_count(self, agent_type):
        return len(self.agent_type_map[agent_type])

    def agent_count_per_state(self, agent_type, state):
        agent_count = 0
        agent_ids = self.agent_type_map[agent_type]

        for agent_id in agent_ids:
            if self.agents[agent_id].state == state:
                agent_count += 1

        return agent_count

    def statistics(self):
        if self.data_collector:
            return self.data_collector.statistics()

    @staticmethod
    def get_random_integer(min_value, max_value):
        return round(random.random() * (max_value - min_value) + min_value)


    @staticmethod
    def lookup(x, points):
        x_vals = np.array([x[0] for x in points])
        y_vals = np.array([x[1] for x in points])

        if x <= x_vals[0]:
            return y_vals[0]

        if x >= x_vals[len(x_vals) - 1]:
            return y_vals[len(x_vals) - 1]

        f = interp1d(x_vals, y_vals)
        return float(f(x))


