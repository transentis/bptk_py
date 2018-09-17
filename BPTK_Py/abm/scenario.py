import math
import random
from BPTK_Py.logger.logger import log
import threading
from IPython.display import display
import ipywidgets as widgets


class Scenario:

    def __init__(self, model, scheduler, data_collector=None):

        self.model = model
        self.properties = {}
        self.agents = []
        self.agent_type_map = {}
        self.data_collector = data_collector
        self.scheduler = scheduler
        self.events = []
        self.start_time = 0
        self.stop_time = 0
        self.step = 1


        for agent_type in self.model.agent_factories:
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
        agent = self.model.agent_factories[agent_type](len(self.agents), self)
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
            agent_ids.append(agent_map[Scenario.get_random_integer(0, num_agents_in_map - 1)])

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
    def lookup(x, min_x, max_x, y_values):

        step_size = (max_x - min_x) / (len(y_values) - 1)
        lookup_value = 0

        if max_x > x > min_x:

            x1 = math.floor((x - min_x) / step_size)
            y1 = y_values[x1]

            if x1 == (x - min_x) / step_size:
                lookup_value = y1
            else:
                x2 = x1 + 1

                y2 = y_values[x2]
                gradient = (y2 - y1) / ((x2 - x1) * step_size)

                lookup_value = (y1 + gradient * (x - (min_x + x1 * step_size)))

        elif x <= min_x:
            lookup_value = y_values[0]

        elif x >= max_x:
            lookup_value = y_values[len(y_values) - 1]

        return lookup_value
