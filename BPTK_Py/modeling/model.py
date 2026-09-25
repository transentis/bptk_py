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
import threading

import numpy as np
import math
from scipy.interpolate import interp1d

from ..util import floating_point as fp

# Which thread is already inside an evaluation. A cold evaluation deep into a run
# recurses once per timestep and can exhaust the stack; the outermost call answers that
# by computing forward instead, and the calls it makes itself must not each try the same.
# Module level rather than an attribute, so that nothing about a Model has to be copied
# or serialized for it, and thread-local because the schedulers evaluate in parallel.
_evaluation = threading.local()

# Set while a user-defined function is running inside the Rust engine. Such a function may
# not evaluate the model: the engine is mid-step, and the Python evaluator it would reach
# is a second, independent one - it knows nothing of the constants or runspecs set on the
# loaded engine model, so the answer would be quietly computed from a different model.
_rust_callback = threading.local()


from .agent import Agent
from .event import Event
from ..logger import log
from ..exceptions import rust_backend_error
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


    def __init__(self, starttime=0.0, stoptime=0.0, dt=1.0,name="", scheduler=None,data_collector=None):

        self._caching_on = False

        # for ABM models
        self.properties = {}
        self.agents = []
        self.next_agent_id=0
        self.name = name
        self.agent_type_map = {}
        self.data_collector = data_collector
        self.scheduler = scheduler
        self.events = []

        # Global Model variables (for SD as well as ABM)
        self.starttime = starttime*1.0
        self.stoptime = stoptime*1.0
        self.dt = dt*1.0
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


    def to_json(self) -> str:
        """Serialize this SD model to the JSON format used by the Rust engine.

        Returns a JSON string that can be loaded by ``RustSdEngine.load_model()``.

        Arrayed elements are supported: every sub-element becomes an entity of its own,
        named with brackets (``headcount[junior]``, ``allocation[0][1]``), the parent is
        skipped because it holds no equation, and the aggregations become ``arr_*``
        calls. ``dot`` is expanded into a sum of products.

        A user-defined function becomes a node carrying its name, which the engine
        answers by calling back into Python; the callable itself is never serialized.

        Raises ``ValueError`` if the model uses a feature the Rust engine cannot
        express, such as a user-defined function registered with ``elementwise=False``,
        which is handed a whole array and answers once.
        """
        from ..sddsl.json_serializer import model_to_json
        return model_to_json(self)

    def register_rust_functions(self, rust_model):
        """Hand a loaded Rust model the callables for the functions it calls.

        The loaded model is asked what it needs rather than being told what the
        serializer emitted: the names live in the JSON, so a model that was never
        serialized here - one loaded from a file - is handled the same way.

        The model is bound to each callable before it crosses over, so the engine holds
        something it can call with a time and numbers and knows nothing about BPTK.
        """
        needed = rust_model.required_functions()
        for name in needed:
            fn = self.fn.get(name)
            if fn is None:
                raise ValueError(
                    "The model calls a function named '{}', but nothing is registered "
                    "for it. Register it with Model.function().".format(name))
            rust_model.register_function(name, self._bind_for_engine(fn))

        if needed:
            # Said out loud because it is not what was asked for: the run is on the Rust
            # engine, but these nodes are evaluated in Python, once per node and timestep.
            # Nothing is wrong - the results are the same - so this warns and does not
            # stop anything.
            log("[WARN] This model calls {} user-defined Python function(s) ({}). Those "
                "nodes are evaluated in Python while the rest of the model runs on the "
                "Rust engine.".format(len(needed), ", ".join(sorted(needed))))

    def _bind_for_engine(self, fn):
        """Bind this model into `fn` and mark the model while the engine runs it.

        The engine calls what it is given with the time and the argument values; the
        model is bound here so that nothing of BPTK crosses over. The mark is what makes
        an evaluation from inside such a function fail loudly instead of quietly
        answering from a second model - see `memoize`.
        """
        model = self

        def call(t, *args):
            _rust_callback.active = True
            try:
                return fn(model, t, *args)
            finally:
                _rust_callback.active = False

        return call

    def simulate(self, equations: list, backend: str = "python"):
        """Run simulation and return results as a Pandas DataFrame.

        Args:
            equations: List of equation names to include in results.
            backend: ``"python"`` (default) or ``"rust"``.

        Returns:
            Pandas DataFrame with time as index (named ``"t"``) and equations as columns.

        Raises:
            RustBackendError: if ``backend="rust"`` was asked for and this model cannot
                run on the engine. It is not computed on the Python engine instead -
                that would look exactly like a run that had used the engine.
        """
        if backend == "rust":
            try:
                return self._simulate_rust(equations)
            except (ValueError, AttributeError, ImportError) as error:
                raise rust_backend_error(error) from error
        else:
            return self._simulate_python(equations)

    def _simulate_rust(self, equations: list):
        import pandas as pd
        from BPTK_Py._rust_engine import RustSdEngine

        json_str = self.to_json()
        engine = RustSdEngine()
        rust_model = engine.load_model(json_str)
        self.register_rust_functions(rust_model)

        raw = rust_model.simulate(equations)
        # Convert string time keys to float
        converted = {}
        for eq_name, time_series in raw.items():
            converted[eq_name] = {float(t): v for t, v in time_series.items()}

        df = pd.DataFrame(converted)
        df.index.name = "t"
        df = df.sort_index()
        return df

    def _simulate_python(self, equations: list):
        import pandas as pd
        from ..util import timerange

        self.reset_cache()
        results = {}
        for eq in equations:
            results[eq] = {}
            for t in timerange(self.starttime, self.stoptime + self.dt, self.dt):
                results[eq][t] = self.equation(eq, t)

        df = pd.DataFrame(results)
        df.index.name = "t"
        return df

    def reset(self):
        """Reset the model.
        Cleara out all agents, agent and event statistics and resets the cache of SD equations. Keeps the agent factories though, so you could directly reconfigure the model using the configure method.
        """
        for agent_type in self.agent_type_map:
            self.agent_type_map[agent_type] = []

        self.agents = []
        # With the agent list emptied, the id counter has to start over with it. Left
        # running, the next agent got id 10 while `agents` was a fresh list of ten, so
        # `model.agents[event.receiver_id]` in the scheduler raised IndexError - and the
        # docstring above promises exactly the reconfiguration that did not work.
        self.next_agent_id = 0

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
        
        Retrieve an agent by its ID

        Args:
            agent_id: Integer.
                ID of agent that is to be retrieved.
        
        Returns:
            Agent object
        """
        for agent in self.agents:
            if agent.id==agent_id:
                return agent

        return None
    

    def create_agents(self, agent_spec):
        """Create agents according to the agent specification.
        
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

        agent = self.agent_factories[agent_type](self.next_agent_id, self, agent_properties)

        self.next_agent_id += 1

        if not isinstance(agent,Agent):
            raise NotAnAgentException("{} is not an instance of BPTK_Py.Agent. Please only use subclasses of Agent".format(agent))

        agent.initialize()
        self.agents.append(agent)
        self.agent_type_map[agent_type].append(agent.id)
        return agent

    def delete_agent(self,agent_id):
        self.delete_agents([agent_id])

    def delete_agents(self,agent_ids):
        temp_agents=[]
        agent_types=[]

        for agent in self.agents:
            if agent.id not in agent_ids:
                temp_agents.append(agent)
            else:
                agent_types.append(agent.agent_type)

        self.agents=temp_agents

        for agent_type in agent_types:
            self.agent_type_map[agent_type]=[]
            for agent in self.agents:
                if agent.agent_type == agent_type:
                    self.agent_type_map[agent_type].append(agent.id)
            
        
                    

    def set_property(self, name, property_spec):
        """Configure a property of the model itself, as opposed to the properties of individual agents.

        Properties set via this mechanism are stored internally in a dictionary of properties, the value of the property directly can be access directly as an object attribute, i.e. as self.<name of property>.

        A property set this way is not collected by the standard data collector and cannot be plotted directly - `collect_agent_statistics` sees the agents, not the model. Reading it back through `get_property`, or as an attribute, is what it is for.

        Args:
            name: String.
                Name of the property to set.
            property_spec: Dict.
                Specification of property: {"type":<type of property, free form string>,"value":<value of property>}. In principle the property can store any kind of value, the type is currently not evaluated by the framework.
        """
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
                If True, shows a progress bar. Since 3.0.0 this is tqdm-backed and
                renders in the terminal, in marimo and in Jupyter alike.
            collect_data: Boolean (Default=True).
                If True, data is automatically collected in the models DataCollector, e.g. for plotting the model behaviour. If you are training the model e.g. using reinforcement learning, it might be useful to turn data collection of.

        """
        if show_progress_widget:
            from ..util import ProgressBar

            with ProgressBar(description='Running {}'.format(self.name)) as progress_widget:
                self.scheduler.run(self, progress_widget, collect_data)
        else:
            self.scheduler.run(self, None, collect_data)


    def run_step(self, step, show_progress_widget=False, collect_data=True):
        """Run a simulation step.
        
        This esssentially just calls the run method of the models scheduler.
        
        Args:
            step: Int.
                The step to run
            show_progress_widget: Boolean (Default=False).
                If True, shows a progress bar. Since 3.0.0 this is tqdm-backed and
                renders in the terminal, in marimo and in Jupyter alike.
            collect_data: Boolean (Default=True).
                If True, data is automatically collected in the models DataCollector, e.g. for plotting the model behaviour. If you are training the model e.g. using reinforcement learning, it might be useful to turn data collection of.

        """
        if show_progress_widget:
            from ..util import ProgressBar

            with ProgressBar(description='Running {}'.format(self.name)) as progress_widget:
                return self.scheduler.run_step(self, 0, step, progress_widget, collect_data)

        return self.scheduler.run_step(self, 0, step, None, collect_data)
        

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
        """Retrieve a number of random agents

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
            event_factory: Function.
                The factory (typicalla a lambda function) that generates the desired event for a given target agent type. The function receives the agent_id as its parameter.
        """

        if not type(agent_type) == str:
            from BPTK_Py.exceptions import  WrongTypeException
            raise WrongTypeException("param {} for agent_type is not of type str".format(agent_type))

        for agent_id in self.agent_type_map[agent_type]:
            self.enqueue_event(event_factory(agent_id))

    def configure_properties(self,properties):
        """
        Called to configure model proerties using a dictionary. 
        Args:
            config: Dict.
                Dictionary containing the config: {"runspecs":<dictionary of runspecs>,"properties":<dictionary of properties>,"agents":<list of agent-specs>}.
        """
         
        for name, property in properties.items():
            self.set_property(name, property)

            #Lookup properties need to be added to the point dictionary also, for compatibilty with SD models

            if property["type"] == "Lookup":
                self.points[name] = property["value"]


    def configure_agents(self,config):
        """
        Called to configure agent proerties using a dictionary. This removes all agents first.1 
        Args:
            config: Dict.
                Dictionary containing the config: {"runspecs":<dictionary of runspecs>,"properties":<dictionary of properties>,"agents":<list of agent-specs>}.
        """

        for agent_type in self.agent_type_map:
            self.agent_type_map[agent_type] = []

        self.agents = []
        
        for agent in config:
            self.create_agents(agent)
        
         
    def configure(self, config):
        """
        Called to configure the model using a dictionary. This method is called by the framework if you instantiate models from scenario files. But you can also call the method directly.

        Args:
            config: Dict.
                Dictionary containing the config: {"runspecs":<dictionary of runspecs>,"properties":<dictionary of properties>,"agents":<list of agent-specs>}.
        """
        self.run_specs(config["runspecs"]["starttime"], config["runspecs"]["stoptime"], config["runspecs"]["dt"])

        properties = config["properties"]

        self.configure_properties(properties)

        agents = config["agents"]

        self.configure_agents(agents)

       

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


    def plot_lookup(self,lookup_names,config=None,format="plot",matplotlib_rc_settings=None):
        """
        Plots lookup functions for the given list of lookup names

        Args:
            lookup_names: String or List.
                A name or list of names of lookup functions. The list can be passed as a Python list or a comma separated string.
            format: String (Default "plot").
                What to return: "plot" draws the diagram and returns nothing, "axes" returns the
                matplotlib Axes, "df" returns the underlying dataframe. Same values as
                bptk.plot_lookup() and Element.plot().
            matplotlib_rc_settings: Dict (Default None).
                matplotlib settings for this one plot, laid over the central plotting
                configuration rather than replacing it.

        Returns:
            Nothing for format="plot", the matplotlib Axes for format="axes", or a Pandas dataframe
            for format="df".

        Note:
            format="plot" relies on the notebook displaying the figure as a side effect, which only
            Jupyter's inline backend does. In marimo, and in a plain script, use format="axes".
        """
        from ..util import lookup_data
        from ..visualizations import visualizer

        if not config:
            from ..config import config

        lookup_names = lookup_names if type(lookup_names) is list else lookup_names.split(",")

        df = lookup_data(self, lookup_names)


        return visualizer(config).plot(df=df,
                                    return_df=False,
                                    format=format,
                                    visualize_from_period=0,
                                    visualize_to_period=0,
                                    # Left as None so visualizer.plot falls back to the
                                    # central plotting configuration - passing the module
                                    # defaults here bypassed it.
                                    stacked=None,
                                    kind=None,
                                    title=str(lookup_names).replace("[","").replace("]","").replace("\'",""),
                                    alpha=None,
                                    x_label="",
                                    y_label="",
                                    start_date="",
                                    freq="",
                                    series_names=None,
                                    matplotlib_rc_settings=matplotlib_rc_settings)





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
        # The same thing `evaluate_equation` does, deliberately kept as a second name:
        # this is what compiled XMILE models call, once per equation per timestep, and
        # it is the hottest path in the Python engine. Routing it through the other
        # method would buy tidiness with an extra call in that loop.
        return self.memoize(equation,t)

    def memoize(self, equation, arg):
        # Public despite the look of it: every compiled XMILE model calls
        # `self.memoize('name', t)` - see sdcompiler/generator/py/py.py - so the name is
        # part of the contract with generated code and cannot move behind an underscore.

        if getattr(_rust_callback, "active", False):
            raise RuntimeError(
                "A user-defined function asked the model for the equation '{}' while the "
                "Rust engine was calling it. That is not supported: the engine is in the "
                "middle of a step, and the Python evaluator this would reach is a second "
                "model that knows nothing about the constants and runspecs the engine is "
                "running with, so the answer would come from somewhere else. A function "
                "that needs a model value takes it as an argument.".format(equation))

        #normalize the arg

        normalized_arg= fp.normalize(arg, self.dt, self.starttime, max(fp.scale(self.starttime), fp.scale(self.dt)))
        try:
            mymemo = self.memo[equation]
        except:
            # In case the equation does not exist in memo
            self.memo[equation] = {}
            mymemo = self.memo[equation]
        if normalized_arg in mymemo.keys():
            return mymemo[normalized_arg]

        # Already inside an evaluation: this call is one link of the chain the outermost
        # one started, and it is that one which retries if the chain grows too long.
        if getattr(_evaluation, "active", False):
            result = self.equations[equation](normalized_arg)
            mymemo[normalized_arg] = result
            return result

        _evaluation.active = True
        try:
            result = self.equations[equation](normalized_arg)
        except RecursionError:
            # A stock asks for the step before it, which asks for the step before that:
            # a cold evaluation at a late step is a chain as long as the run, and Python
            # runs out of stack at about 330 steps - counted in steps, so a fine `dt`
            # reaches it early in model time. Computing forward keeps every step shallow,
            # because each one finds its predecessor already here.
            result = self._evaluate_forward(equation, normalized_arg)
        finally:
            _evaluation.active = False

        mymemo[normalized_arg] = result
        return result

    def _evaluate_forward(self, equation, target):
        """Evaluate `equation` from `starttime` up to `target`, keeping each step shallow.

        Whatever is in the memo already is kept: only the gaps are filled.
        """
        mymemo = self.memo[equation]
        precision = max(fp.scale(self.starttime), fp.scale(self.dt))
        t = self.starttime
        result = None

        try:
            while t <= target:
                if t in mymemo:
                    result = mymemo[t]
                else:
                    result = self.equations[equation](t)
                    mymemo[t] = result
                t = fp.normalize(t + self.dt, self.dt, self.starttime, precision)
        except RecursionError:
            # Not the timestep chain then, but one evaluation that is itself too deep -
            # a long chain of elements referring to one another. Nothing here can help
            # with that, so say what happened instead of repeating the bare error.
            raise RecursionError(
                "'{}' cannot be evaluated at t={}: even computing from {} upwards, a "
                "single timestep goes deeper than Python's recursion limit. This is a "
                "chain of elements referring to one another rather than a long run - "
                "shorten it, or raise sys.setrecursionlimit().".format(
                    equation, target, self.starttime)
            ) from None

        return result

    def add_equation(self, equation, lambda_method):
        # Public for the same reason as `memoize`: compiled models and hand-written
        # hybrid models both call it.
        
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

    def function(self, name, fn, elementwise=True):
        """Create a user defined function for System Dynamics.

        Args:
            name:  String.
                Name of the function.
            fn: The callable, which receives the model and the current time followed by
                the arguments of the call site.
            elementwise: Boolean (Default=True).
                What an arrayed argument means. True calls the function once per index,
                so the result is an array of the same shape - the rule every operator
                follows. False hands the whole array over instead: a list for an unnamed
                array, a dict keyed by the labels for a named one, nested for a matrix,
                and the result is a single value.

        Returns: 
        A function which wraps the user defined function for use within System Dynamics.
        """

        if name not in self.functions:
            self.functions[name] = lambda *args: NaryOperator(name, *args, elementwise=elementwise)
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
        """Reset cache of all System Dynamics equations and of the ABM data collector
        """
        if self.data_collector:
            self.data_collector.reset()

        for agent in self.agents:
            agent.reset_cache()

        for equation in self.memo:
            self.memo[equation] = {}






