# Front matter the .py format cannot carry; injected on export.
# description: Building the customer acquisition model as an agent-based model with BPTK.
# keywords: agent-based modeling, abm, agents, events, scenarios, bptk, bptk-py, python, business simulation
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Customer Acquisition using Agent-based Modeling")


@app.cell
def _():
    import marimo as mo

    return (mo,)

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Customer Acquisition using Agent-based Modeling

    The basic concept behind Agent-based models is quite simple: you populate an environment (the model) with a set of agents. Agents and the environment each have a set of properties and each agent must always be in a defined state.

    Agents can perform actions and interact amongst each other and with the environment by sending each other events - the agents react to these events by updating their properties and/or changing their state.

    ![Agents and their environment](../images/agents_environment.svg)

    So to create an agent using Python and the BPTK framework, all you really need to do is:

    * Identify the relevant agents
    * Define the agents properties
    * For each agent, implement an initializer which sets the agents initial state
    * Define handlers for each kind of event you want your agent to react to
    * Define an action method, which describes what the agent does in each time-step, e.g. perform internal tasks and send events to other agents

    Defining the model is even easier:

    * Define the environment properties and update them when necessary
    * Tell the model which kinds of agents there are
    * Then, to configure the simulation, all we need to do is to set the initial values of the properties and instantiate the initial agents. Each unique configuration of a model is referred to as a scenario. The BPTK framework helps you to manage different scenarios and compare results easily.

    Configuring Agent-based models is best done using a config file defined in JSON.

    Agent-based modeling is a very powerful approach and you can build models using ABM that you cannot build using SD. This power comes at a prices though: because each agent is modelled as an individual entity, agent-based models are quite slow.

    ## Setting Up the Model

    For the customer acquisition model, we really just need to agents: the company that sends advertising events and the consumers that receive those events. If a consumer becomes a customer, then the consumers starts sending word ouf mouth events.

    This is illustrated in the following diagram:

    ![Customer Acquisition ABM](../images/customer_acquisition_abm.svg)

    Note that the advertising budget and the contact rate are properties of the respective agents – this is a glimpse at the power of agent-based modeling, because we could easily set individual contact rates for the consumers or have multiple companies advertising competing products. All these aspects cannot easily be modelled using System Dynamics.
    """)
    return

@app.cell
def _():
    import BPTK_Py
    from BPTK_Py import Agent
    from BPTK_Py import Event
    from BPTK_Py import DataCollector
    from BPTK_Py import SimultaneousScheduler

    return Agent, BPTK_Py, DataCollector, Event, SimultaneousScheduler

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Setting up agents is actually quite simple - all you need to do is register handlers for the events and define the `act` method.
    """)
    return

@app.cell
def _(Agent, Event):
    class Consumer(Agent):
        def initialize(self):
            self.agent_type = "consumer"
            self.state = "potential"
            self.register_event_handler(["potential"],"advertising_event",self.handle_advertising_event)
            self.register_event_handler(["potential"],"word_of_mouth_event",self.handle_word_of_mouth_event)
        
        def handle_advertising_event(self,event):
            if self.is_event_relevant(self.model.advertising_success):
                self.state="customer"
    
        def handle_word_of_mouth_event(self, event):
            if self.is_event_relevant(self.model.word_of_mouth_success):
                self.state="customer"
                
        def act(self,time,round_no,step_no):
            # consumers who are customers generate word of mouth events
            if self.state == "customer":
                self.model.random_events(
                    "consumer",
                    self.contact_rate,
                    lambda agent_id: Event("word_of_mouth_event", self.id, agent_id)
                )

    return (Consumer,)

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Note that the company agent defined below accesses the properties `advertising_budget`and `consumers_reacher_per _euro`. These properties are defined in the scenarios and can then be accessed "magically" as either agent properties or model properties.
    """)
    return

@app.cell
def _(Agent, Event):
    class Company(Agent):
        def initialize(self):
                self.agent_type="company"
                self.state = "active"
    
        def act(self,time,round_no,step_no):
            self.model.random_events(
                "consumer",
                self.advertising_budget*self.model.consumers_reached_per_euro,
                lambda agent_id: Event("advertising_event",self.id, agent_id)
            )

    return (Company,)

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The model itself needs a way of instantiating agents - for this you register agent factories, which return an agent of a particular type. In their simplest form an agent factory is just a lambda function.
    """)
    return

@app.cell
def _(Company, Consumer, DataCollector, SimultaneousScheduler):
    # Imported here rather than taken from the cell above: there `Model` shares a
    # cell with the SD model, so every edit to that model would re-run this whole
    # section as well.
    from BPTK_Py import Model as AbmModel

    class CustomerAcquisitionAbm(AbmModel):
        def instantiate_model(self):
            self.register_agent_factory("consumer", lambda agent_id,agent_model,properties: Consumer(agent_id, agent_model,properties))
            self.register_agent_factory("company", lambda agent_id,agent_model, properties: Company(agent_id, agent_model, properties))
    customer_acquisition_abm=CustomerAcquisitionAbm(1,60,dt=1,name="Customer Acquisition Agent-based Model",scheduler=SimultaneousScheduler(),data_collector=DataCollector())
    customer_acquisition_abm.instantiate_model()
    return CustomerAcquisitionAbm, customer_acquisition_abm

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    NOTE: Running an agent-based model takes noticeably longer than running a System Dynamics model, because every agent acts in every step. The population here is deliberately small, so that the model runs in your browser as well.
    """)
    return

@app.cell
def _(customer_acquisition_abm):
    customer_acquisition_abm_config =  {
                 "runspecs": {
                      "starttime": 1,
                      "stoptime":60,
                      "dt": 1.0
                },
                "properties":
                {
                    "word_of_mouth_success":
                    {
                        "type":"Double",
                        "value":0.01
                    },
                    "advertising_success":
                    {
                        "type":"Double",
                        "value":0.1
                    },
                    "consumers_reached_per_euro":
                    {
                        "type":"Integer",
                        "value":8
                    }
                
                },
                "agents":
                [
                    {
                        "name":"company",
                        "count":1,
                        "properties":{
                             "advertising_budget":
                            {
                                "type":"Integer",
                                "value":1
                            }
                        }
                    },
                    {
                        "name":"consumer",
                        "count":50,
                        "properties":{
                            "contact_rate":
                            {
                            "type":"Integer",
                            "value":10
                            }
                        }
                        
                    }
                ]
            }
    customer_acquisition_abm.configure(customer_acquisition_abm_config)

    customer_acquisition_abm.run()

    [customer_acquisition_abm.statistics().get(1.0*key) for key in range(1,5)]
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Setting Up Scenarios

    The scenario mechanism works exactly the same for SD DSL, agent-based and hybrid models, so you can load different kinds of model side by side and compare their results.
    """)
    return

@app.cell
def _(BPTK_Py, CustomerAcquisitionAbm, DataCollector, SimultaneousScheduler):
    bptk_1 = BPTK_Py.bptk()

    # A scenario manager gets its own model instance. Handing it the one we just ran
    # by hand does not work: `reset()` empties the agent list but keeps the agent id
    # counter, so the next run's ids point past the list and the run dies with an
    # IndexError - which is swallowed by the thread it runs in and leaves an empty
    # chart. Remove this once that is fixed in the library.
    customer_acquisition_abm_scenarios = CustomerAcquisitionAbm(
        1, 60, dt=1, name="Customer Acquisition Agent-based Model",
        scheduler=SimultaneousScheduler(), data_collector=DataCollector()
    )
    customer_acquisition_abm_scenarios.instantiate_model()
    abm_scenario_manager={
        "abm_customer_acquisition":{
            "name":"abm_customer_acquisition",
            "type":"abm",
            "model":customer_acquisition_abm_scenarios,
            "scenarios":{
                "base":
            {
                 "runspecs": {
                      "starttime": 1,
                      "stoptime":60,
                      "dt": 1.0
                },
                "properties":
                {
                    "word_of_mouth_success":
                    {
                        "type":"Double",
                        "value":0.01
                    },
                    "advertising_success":
                    {
                        "type":"Double",
                        "value":0.1
                    },
                    "consumers_reached_per_euro":
                    {
                        "type":"Integer",
                        "value":8
                    }
                
                },
                "agents":
                [
                    {
                        "name":"company",
                        "count":1,
                        "properties":{
                             "advertising_budget":
                            {
                                "type":"Integer",
                                "value":1
                            }
                        }
                    },
                    {
                        "name":"consumer",
                        "count":50,
                        "properties":{
                             "contact_rate":
                             {
                                "type":"Integer",
                                "value":10
                            }
                        
                        }
                    }
                ]
            }
            }
        }
    
    
    }
    bptk_1.register_scenario_manager(abm_scenario_manager)

    bptk_1.plot_scenarios(scenario_managers=['abm_customer_acquisition'], scenarios=['base'], agents=['consumer'], agent_states=['customer'], format="axes")
    return
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    NOTE: especially for larger models it is much better to keep the model and the scenario definitions in separate files.
    """)
    return

if __name__ == "__main__":
    app.run()
