# Front matter the .py format cannot carry; injected on export.
# description: BPTK API Documentation for the Model class
# keywords: agent-based modeling, system dynamics, bptk, bptk-py, python, business prototyping
#
# Not a single code cell on this page - it is prose and signatures. Left reactive it
# still booted Pyodide, some 8 MB, to run nothing at all.
# interactive: false
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Model")


@app.cell
def _():
    import marimo as mo

    return (mo,)




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Model

    ## Model Constructor

    **Model(starttime=0, stoptime=0, dt=1, name='', scheduler=None, data_collector=None)**

    This is the main agent base / System dynamics / Hybrid model class

    It can run manually generated SD models, AB Models or define hybrid models.

    * **Parameters**


        * **name** – String.
        Name of the model.

        * **scheduler** – Scheduler.
        Scheduler object (e.g. simultaneousScheduler). This is configurable, so that you can add your own scheduling algorithms.

        * **data_collector** – DataCollector
        Instance of DataCollector. This is configurable, so that you can add your own data collection algorithms.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.agent

    **agent(agent_id)**

    Get an agent by ID.

    Retrieve one agent by its ID

    * **Parameters**

        **agent_id** – Integer.
        ID of agent that is to be retrieved.

    * **Returns**

        Agent object
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.agent_count
    **agent_count(agent_type)**
    Get count of agents of a given type.

    * **Parameters**

        **agent_type** – String.
        Agent type to get count for

    * **Returns**

        Integer. Number of agents (Integer)
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.agent_count_per_state

    **agent_count_per_state(agent_type, state)**

    Get number of agents in a specific state

    * **Parameters**


        * **agent_type** – String.
        Agent type to get count for

        * **state** – String.
        The state of agents to get count for

    * **Returns**

        Integer.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.agent_ids

    **agent_ids(agent_type)**

    Get agent IDs.

    Retrieve agent IDs for all agents of type agent_type.

    * **Parameters**

        **agent_type** – String.
        Agent type to get IDs for

    * **Returns**

        List of IDs
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.begin_episode

    **begin_episode(episode_no)**

    Called at beginning of an episode.

    When running a simulation repeatedly in episodes (e.g. because you are training the model using reinforcement learning), this method is called by the framework to allow tidy up at the beginning of an episode, e.g. a “soft” reset of the simulation.

    The default implementation calls begin_episode on each agent.

    * **Parameters**

        **episode_no** – Integer.
        The number of the episode
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.begin_round

    **begin_round(time, sim_round, step)**

    Called at the beginning of a simulation round.

    Should be called by the Scheduler at the beginning of each round, before the agents act methods are called. Add any logic here that is needed to update dynamic properties.

    * **Parameters**


        * **time** – Integer.
        The current timestep of the simulation, i.e.(round+step\*dt)

        * **sim_round** – Integer
        The current round of the simulation.

        * **step** – Integer.
        The step number of round
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.biflow

    **biflow(name)**
    Create a System Dynamics biflow

    * **Parameters**

        **name** – String.
        Name of the biflow

    * **Returns**

        A Biflow object
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.broadcast_event

    **broadcast_event(agent_type, event_factory)**

    Broadcast an event to all agents of a particular agent_type

    * **Parameters**


        * **agent_type** – String.
        Agent type that is to receive the event

        * **num_agents** – Integer.
        Number of random agents that should receive the event

        * **event_factory** – Function.
        The factory (typicalla a lambda function) that generates the desired event for a given target agent type. The function receives the agent_id as its parameter.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.configure

    **configure(config)**

    Called to configure the model using a dictionary. This method is called by the framework if you instantiate models from scenario files. But you can also call the method directly.

    * **Parameters**

        **config** – Dict.
        Dictionary containing the config: {“runspecs”:<dictionary of runspecs>,”properties”:<dictionary of properties>,”agents”:<list of agent-specs>}.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.constant

    **constant(name)**

    Returns a [Constant](./api_constant.md) object with the given name - if a Constant with the given name already exists within the model, this one is returned. Else a new Constant object is created, stored and returned.

    * **Parameters**

        **name** – String.
        Name of the constant

    Returns: Constant.

        A Constant object
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.converter

    **converter(name)**

    Returns a [Converter](./api_converter.md) object with the given name - if a Converter with the given name already exists within the model, this one is returned, else a new Converter object is created, stored and returned.

    * **Parameters**

        **name** – String.
        Name of the converter

    * **Returns**

        A Converter object
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.create_agent

    **create_agent(agent_type, agent_properties)**
    Create one agent of the given type and with the given properties.

    Internally this method then uses the registered agent factories to actually create an agent.

    * **Parameters**


        * **agent_type** – String.
        Type of agent

        * **agent_properties** – Dict.
        The properties to initialize the agent with.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.create_agents

    **create_agents(agent_spec)**

    Create agents according to the agent specificaction.

    The agent specification is a dictionary containing the agent name and properties. Internally, this method then uses the registered agent factories to actually create the agents.

    * **Parameters**

        **agent_spec** – Dict.
        Specification of an agent using a dictionary with format {“name”:<agent name>, “count”: <initial count>}
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.end_episode
    **end_episode(episode_no)**

    Called at the end of an episode.

    When running a simulation repeatedly in episodes, this method is called by the framework to allow tidy up at the end of an episode.

    The default implementation calls end_episode on each agent.

    * **Parameters**

        **episode_no** – Integer.
        The number of the episode
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.end_round

    **end_round(time, sim_round, step)**

    Called at end of a simulation round.

    Should be called by the Scheduler at the end of each round, before the agents act methods are called. Add any logic here that is needed to update dynamic properties.

    * **Parameters**


        * **time** – Integer.
        The current timestep of the simulation, i.e.(round+step\*dt)

        * **sim_round** – Integer
        The current round of the simulation.

        * **step** – Integer.
        The step number of round
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.enqueue_event

    **enqueue_event(event)**

    Called by the framework to enqueue events.

    In general you don’t need to override this method or call it directly.

    * **Parameters**

        **event** – Event.
        Instance of the event.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.equation_prefix

    **_property_ equation_prefix()**

    An id that is unique within this model that can be used to generate unique equation names.

    This method is useful when auto-generating equations.

    * **Returns**

        Integer. An id that is unique within the model.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.evaluate_equation

    **evaluate_equation(name, t)**

    Evaluate an System Dynamics element’s equation at timestep t.

    * **Parameters**


        * **name** – String.
        Name of the equation.

        * **t** – Float.
        Timestep to evaluate for

    Return: Float

        The value of the equation at time t.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.flow

    **flow(name)**

    Returns a [Flow](./api_flow.md) object with the given name - if a Flow with the given name already exists within the model, this one is returned, else a new Flow object is created, stored and returned.

    * **Parameters**

        **name** – String.
        Name of the flow

    * **Returns**

        A Flow object
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.function

    **function(name, fn)**

    Returns a Lambda function that wraps the function _fn_.

    The document [User Defined Functions](../sd-dsl/sd_user_defined_functions/sd_user_defined_functions.ipynb) illustrates how such functions can be used.

    * **Parameters**


        * **name** – String.
        Name of the function.

        * **fn** – Function
        A function that will be used within a SD DSL model. The function must accept at least a _model_ parameter and a time _t_ parameter.

    Returns:
    A function which wraps the user defined function for use within SD DSL models.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.get_property

    **get_property(name)**

    Get a property of the model by name.

    The value of the model properties can also be accessed directly as a model attribute, i.e. as self.<name of property>

    * **Parameters**

        **name** – String.
        Name of property

    * **Returns**

        Dictionary for property
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.get_property_value

    **get_property_value(name)**
    Get a property of the model by name.

    The value of the model properties can also be accessed directly as a model attribute, i.e. as self.<name of property>

    * **Parameters**

        **name** – String.
        Name of property

    * **Returns**

        Value of the property.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.get_random_integer

    **_static_ get_random_integer(min_value, max_value)**

    A random integer within bounds

    This method is useful for simulating random behaviour.

    * **Parameters**


        * **min_value** – Integer.
        Min value for random integer

        * **max_value** – Integer.
        max value for random integer

    * **Returns**

        Random integer.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.instantiate_model

    **instantiate_model()**

    Set properties during model initialization.

    This method does nothing in the parent class and can be overriden in child classes. It is called by the frame directly after the model is instantiated.

    Implement this method in your model to perform any kind of initialization you may need. Typically you would register your agent factories hier and set up model properties.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.next_agent

    **next_agent(agent_type, state)**

    Get the next agent by type and state.

    Runs through the internal agent store and retrieves the first agent that matches in type and state.

    * **Parameters**


        * **agent_type** – String.
        Agent type

        * **state** – String.
        State the agent is in

    * **Returns**

        The first agent object that matches the criterian None otherwise.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.plot_lookup

    **plot_lookup(lookup_names, config=None, format="plot")**

    Plots lookup functions for the given list of lookup names.

    * **Parameters**

        **lookup_names** – String or List.
        A name or list of names of lookup functions. The list can be passed as a Python list or a comma separated string.

        **format** – String (Default "plot").
        What to return: "plot" draws the diagram and returns nothing, "axes" returns the
        matplotlib Axes, "df" returns the underlying dataframe. "plot" relies on the notebook
        displaying the figure as a side effect, which only Jupyter's inline backend does —
        in marimo, and in a plain script, use "axes".
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.random_agents

    **random_agents(agent_type, num_agents)**

    Retreive a number of random agents

    * **Parameters**


        * **agent_type** – String.
        Type of agent to retrieve.

        * **num_agents** – Number of agents of this type to retreive.

    * **Returns**

        List of agent IDs. The number of IDs might be less then num_agents if fewer agents are available.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.random_events

    **random_events(agent_type, num_agents, event_factory)**

    Distribute events to a number of random agents

    * **Parameters**


        * **agent_type** – String.
        Agent type that is to receive the event

        * **num_agents** – Integer.
        Number of random agents that should receive the event

        * **event_factory** – Function.
        The factory (typicalla a lambda function) that generates the desired event for a given target agent type. The function receives the agent_id as its parameter.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.register_agent_factory

    **register_agent_factory(agent_type, agent_factory)**

    Register an agent factory.

    Agent factories are used at run-time to populate the model with agents. This method is used to register an agent factory, which is typically just a lambda function which returns an agent.

    * **Parameters**


        * **agent_type** – String.
        Type of agent to register

        * **agent_factory** – Function.
        Function that returns an agent given an id and the model. Typically a lambda, but not limited to that. Input: agent_id, model -> Output: Agent of agent_type
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.reset

    **reset()**

    Reset the model.

    Clear out all agents, agent and event statistics and resets the cache of SD equations.

    The agent factories are kept though, so you could directly reconfigure the model using the configure method.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.reset_cache

    **reset_cache()**

    Reset cache of all System Dynamics equations and call the reset_cache method on all agents. Clear the agent statistics.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.run

    **run(show_progress_widget=False, collect_data=True)**

    Run the simulation.

    This esssentially just calls the run method of the models scheduler. Only relevant for agent-based models, does nothing on pure SD DSL models.

    * **Parameters**

        * **show_progress_widget** – Boolean (Default=False).
        If True, shows a progress bar while the simulation runs. It is built on tqdm, so it works in a terminal, in marimo and in Jupyter alike.

        * **collect_data** – Boolean (Default=True).
        If True, data is automatically collected in the models DataCollector, e.g. for plotting the model behaviour. If you are training the model e.g. using reinforcement learning, it might be useful to turn data collection of.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.run_specs

    **run_specs(starttime, stoptime, dt)**

    Configure the runspecs of the model.

    * **Parameters**

        * **starttime** – Integer.
        The starttime of the model.

        * **stoptime** – Integer.
        The stoptime of the model.

        * **dt** – The dt of the model.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.run_step

    **run_step(step, show_progress_widget=False, collect_data=True)**

    Run a simulation step.

    This esssentially just calls the run method of the models scheduler.

    * **Parameters**

        * **step** – Int.
        The step to run

        * **show_progress_widget** – Boolean (Default=False).
        If True, shows a progress bar while the simulation runs. It is built on tqdm, so it works in a terminal, in marimo and in Jupyter alike.

        * **collect_data** – Boolean (Default=True).
        If True, data is automatically collected in the models DataCollector, e.g. for plotting the model behaviour. If you are training the model e.g. using reinforcement learning, it might be useful to turn data collection off.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.set_property

    **set_property(name, property_spec)**

    Configure a property of the model itself, as opposed to the properties of individual agents.

    Properties set via this mechanism are stored internally in a dictionary of properties, the value of the property directly can be access directly as an object attribute, i.e. as self.<name of property>.

    The key point about keeping properties in this way is that they can then easily be collected in a data collector.

    * **Parameters**

        * **name** – String.
        Name of the property to set.

        * **property_spec** – Dict.
        Specification of property: {“type”:<type of property, free form string>,”value”:<value of property>}. In principle the property can store any kind of value, the type is currently not evaluated by the framework
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.set_property_value

    **set_property_value(name, value)**

    Set the value of a model property by name.

    Model properties can also be set directly via the model attributes, i.e. as self.<nname of property>=<value of property>

    * **Parameters**


        * **name** – String.
        Name of property.

        * **value** – Any.
        Value of the property to set.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.set_scenario_manager

    **set_scenario_manager(scenario_manager)**

    Set the name of the scenario manager that is handling this model. Used by the `bptk` class during scenario registration.

    * **Parameters**

        **scenario_manager** – String.
        Name of the scenario manager.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.statistics

    **statistics()**

    Get statistics from DataCollector.

    * **Returns**

        The DataCollector used to collect the simulation statistics.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.to_json

    **to_json()**

    Serialise the model to the JSON format the Rust engine loads.

    You rarely need to call this — `run_scenarios(backend="rust")` does it for you. It is
    useful when you want to know *whether* a model can run on the Rust engine, because
    this is where the answer is decided: it raises `ValueError` for anything the engine
    cannot express, naming what it tripped over.

    * **Returns**

        A JSON string.

    * **Raises**

        `ValueError` if the model uses user-defined functions or arrayed aggregations. In
        a normal run that exception is caught and the scenario continues on the Python
        engine; see [Execution Backends](../concepts/execution_backends/execution_backends.md).
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Model.stock

    **stock(name)**

    Returns a [Stock](./api_flow.md) object with the given name - if a Stock with the given name already exists within the model, this one is returned, else a new Stock object is created, stored and returned.

    * **Parameters**

        **name** – String.
        Name of the stock.

    * **Returns**

        The Stock object.
    """)
    return


if __name__ == "__main__":
    app.run()
