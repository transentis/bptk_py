# Front matter the .py format cannot carry; injected on export.
# description: A tutorial introduction to System Dynamics with BPTK - stocks, flows, feedback and delay, built up in one model and simulated step by step.
# keywords: system dynamics, tutorial, stocks and flows, feedback, bptk, bptk-py, python, business simulation
import marimo

__generated_with = "0.23.13"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # System Dynamics Tutorial
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    System dynamics is a method devoted to the study of systems, and is thus a tool within the Systems Thinking tool kit. It uses simple graphical notations to model systems such as stock and flow diagrams. These diagrams contain specific components and symbols to describe systems. This tutorial gives an introduction to the elements of stock and flow diagrams using the BPTK-Py framework.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The tutorial explains system dynamics with a population model. The model shows how the population changes over time and which factors influence the population value.

    ![Stock and Flow Diagram of Population Growth](./sfd_population_growth.svg)
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Now, let's create the model. It is used to store all stocks, converters and flows. The model runs for 10 years (starttime = 0, stoptime = 10) and we want to analyse the results after each year (dt = 1). In the next steps we are going to add the stocks and flows to the model.

    We want to simulate how the population changes in the next ten years under external influences.
    """)
    return


@app.cell
def _():
    from BPTK_Py import Model
    from BPTK_Py import sd_functions as sd

    model = Model(starttime=1.0,stoptime=10.0,dt=1.0,name='Population')
    return Model, model, sd


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Stocks

    A stock represents a part of a system whose value at any given instant in time depends on the systems past behavior. The value of the stocks at a particular instant in time cannot simply be determined by measuring the value of the other parts of the system at that instant in time – the only way you can calculate it is by measuring how it changes at every instant and adding up all these changes.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ![Population Stock](./sfd_population.svg)

    The stock in our model represents the population at each timestep. Initially, we assume 80 mio. people living in our fictional country.  We create a model by entering `model.stock(<name>)`. The name of our stock is "population".
    """)
    return


@app.cell
def _(model):
    population = model.stock("population")
    population.initial_value = 80000000.0
    population.plot(format="axes")
    return (population,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The population does not change. There are no other factors influencing the number of people. To simulate changes in the population, we need births and deaths. We add these factors by using flows.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Flows

    Flows represent the rate at which the stock is changing at any given timestep. They either flow into a stock (causing it to increase) or flow out of a stock (causing it to decrease).
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ![Births and Deaths Flows](./sfd_flows.svg)
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Let us make this model simple and just suppose 1,000,000 babies are born and 2,000,000 people die each year. The flows are defined by using the method `model.flow(<name>)`.
    """)
    return


@app.cell
def _(model):
    births = model.flow("births")
    births.equation = 1000000.0
    births.plot(format="axes")
    return (births,)


@app.cell
def _(model):
    deaths = model.flow("deaths")
    deaths.equation = 2000000.0
    deaths.plot(format="axes")
    return (deaths,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Equations

    To connect elements we require equations. These are mathematical operations that are evaluated at each timestep. We combine the flows with our stock by setting the ``equation`` field of ``population``.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ![Stocks and Flows](./sfd_stocks_flows.svg)
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    In our simple example, the population is the sum of births minus the deaths plus the initial value or the value from the last timestep.

    The Logic in System Dynamics is always the same: Values at timestep ``t`` depend on the result at ``t-1`` Let us look at the population:
    ```

    population.equation = births - deaths

    population (1)  = 80,000,0000 (start time)
    population (2) = population(1) + (births(2) - deaths(2)) = 80,000,000 + (1,000,000 - 2,000,000) = 79,000,000
    population (3) = population(2) + (births(2) - deaths(2)) = 79,000,000 + (1,000,000 - 2,000,000) = 78,000,000

    and so on...
    ```

    See how easy it is to define this behavior:
    """)
    return


@app.cell
def _(births, deaths, population):
    population.equation = births - deaths
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    And let's check whether we are able to obtain the expected results:
    """)
    return


@app.cell
def _(mo, population):
    # marimo sends a cell's stdout to the console, not to its output area.
    # Captured and handed to `mo.plain_text` it comes back as one block.
    with mo.capture_stdout() as output:
        print("population(1): " + str(population(1)))
        print("population(2): " + str(population(2)))
        print("population(3): " + str(population(3)))

    mo.plain_text(output.getvalue())
    return


@app.cell
def _(population):
    population.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    In reality, the number of births or deaths is not fixed, we usually work with ratios. They change depending on the population and external factors (diseases, medical supply, food supply etc.). In system dynamics, we model such behavior with converters.

    ### Converters

    Converters either represent parts at the boundary of the system (i.e. parts whose value is not determined by the behavior of the system itself) or they represent parts of a system whose value can be derived from other parts of the system at any time through some computational procedure.

    Let us add converters to the population model:
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ![Population Growth with Birth Rate, Death Rate and Food Available as Converters](./sfd_population_growth.svg)
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    In the image above, the converters are represented by circles. In Python, we define converters with ``model.converter`` or ``model.constant``. ``constants`` are converters with a constant value (i.e. they never change).

    We want to model the birth rate and death rate that are influenced by the food supply.
    """)
    return


@app.cell
def _(model):
    birthRate = model.converter("birthRate")
    deathRate = model.converter("deathRate")
    foodAvailablePerPerson = model.converter("foodAvailablePerPerson")
    foodAvailable = model.constant("foodAvailable")
    return birthRate, deathRate, foodAvailable, foodAvailablePerPerson


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Connectors

    Much like in causal loop diagrams the connectors of a system show how the parts of a system influence each other.  Stocks can only be influenced by flows (i.e. there can be no connector that connects into a stock), flows can be influenced by stocks, other flows, and by converters. Converters either are not influenced at all (i.e. they are at the systems boundary) or are influenced by stocks, flows and other converters.

    Please note that we do not explicitly model connectors but create the connection by defining equations. Equations are expressive enough to represent interactions between model elements.

    Since `foodAvailable` is a constant, we can initiliaze it with a float value.
    """)
    return


@app.cell
def _(foodAvailable):
    foodAvailable.equation = 80000000.0
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The converters `foodAvailablePerPerson` and `birthRate` are formulas. `foodAvailablePerPerson` depends on `population` and `foodAvailable`. The more people the less food per person. The birth rate decreases if we have less than one unit food per person.
    """)
    return


@app.cell
def _(birthRate, births, foodAvailable, foodAvailablePerPerson, population):
    foodAvailablePerPerson.equation = foodAvailable / population

    birthRate.equation = 0.01 * foodAvailablePerPerson

    births.equation = birthRate * population
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We define the death rate in our model using a non-linear relationship (depending on food available per person). We capture this relationship in a lookup table (often also called "graphical function" in the System Dynamics context) that we store in the `points` property of the model (using a Python list).
    """)
    return


@app.cell
def _(deathRate, deaths, model, population):
    model.points["deathRate"] = [
        [0.0,1.0],
        [0.1,0.670320046036],
        [0.2,0.449328964117],
        [0.3,0.301194211912],
        [0.4,0.201896517995],
        [0.5,0.135335283237],
        [0.6,0.0907179532894],
        [0.7,0.0608100626252],
        [0.8,0.0407622039784],
        [0.9,0.025],
        [1.0,0.01]
    ]

    deaths.equation = deathRate * population
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We can easily plot the lookup table to see whether it has the right shape:
    """)
    return


@app.cell
def _(model):
    model.plot_lookup("deathRate", format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We now need to connect the `deathRate` lookup to the `foodAvailablePerPopulation`:
    """)
    return


@app.cell
def _(deathRate, foodAvailablePerPerson, sd):
    deathRate.equation = sd.lookup(foodAvailablePerPerson, "deathRate")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Now, we have defined all components. Let us plot them. We first register the model.
    """)
    return


@app.cell
def _(model):
    import BPTK_Py
    bptk = BPTK_Py.bptk()
    bptk.register_model(model)
    return (bptk,)


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenarios="base",
        scenario_managers="smPopulation",
        equations=["population","deaths","births"], format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    With these settings the population is stable, because birth rate and death rate are equal.
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenarios=["base"],
        scenario_managers="smPopulation",
        equations=["birthRate","deathRate"],
        series_names={}, format="axes"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Scenarios

    BPTK Py creates a scenario `base` by default when registering the model. However, it is boring just to examine one scenario. We want to make various assumptions to understand the behavior of the model or the system. Changing values can lead to different outcomes. For this purpose, the BPTK Py framework provides a powerful scenario management enabling us to create different scenarios.

    We set up a scenario manager using a Python dictionary. The scenario manager identifies the baseline constants of the model:
    """)
    return


@app.cell
def _(model):
    scenario_manager = {
        "smPopulation":{
            "model": model,
            "base_constants": {
            "population": 80000000.0,
            "foodAvailable": 80000000.0
            },
            "base_points":{
              "deathRate": [
                [0.0,1.0],
                [0.1,0.670320046036],
                [0.2,0.449328964117],
                [0.3,0.301194211912],
                [0.4,0.201896517995],
                [0.5,0.135335283237],
                [0.6,0.0907179532894],
                [0.7,0.0608100626252],
                [0.8,0.0407622039784],
                [0.9,0.0273237224473],
                [1.0,0.0183156388887]]
            }
        }
    }
    return (scenario_manager,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The scenario manager has to be registered as follows:
    """)
    return


@app.cell
def _(bptk, scenario_manager):
    bptk.register_scenario_manager(scenario_manager)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    After registering the scenario mangager, we can define and register more scenarios. Let us change `foodAvailable` from 80,000,000 units to 700,000 units.
    """)
    return


@app.cell
def _(bptk):
    bptk.register_scenarios(
        scenarios ={
            "scenario07": {
                "constants": {
                    "foodAvailable": 70000000.0
                }
            }
        },
        scenario_manager="smPopulation")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Now, we can plot our scenarios `base` and `scenario07` and see how changing `foodAvailable` affects the population. We plot the `population` for both scenarios.
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenarios=["base","scenario07"],
        scenario_managers="smPopulation",
        equations=["population"],
        series_names={}, format="axes"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    According to the stock and flow diagram `foodAvailable` influences `foodAvailablePerPerson`. The less food we have, the less food one person has. `foodAvailablePerPerson` then affects the births and deaths. Less people are born and more people die because we don't have enough food for each person. As a result, the population of `scenario07` decreases.
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenarios=["base","scenario07"],
        scenario_managers="smPopulation",
        equations=["deathRate"],
        series_names={}, format="axes"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Export Data as a Pandas Dataframe

    We built BPTK-Py with integration in mind. This means, you can easily export the simulation results as so-called "DataFrames". This is a standard Python exchange format for data. This means you can easily process the simulation results in other data analysis / data science packages for further processing (Machine Learning, Data enrichment and many more). Just add the argument ``return_df=True`` to the plot_scenarios call:
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenarios=["base","scenario07"],
        scenario_managers="smPopulation",
        equations=["population"], 
        series_names={},
        return_df=True)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Try It Yourself

    The tutorial above builds the model one step at a time, and each step's effect shows up
    in the next diagram. That reads well, but it means editing a step only changes what
    comes after it once you run that part too.

    So here is the finished model in a single cell, with its own name so it cannot collide
    with the one above. Change a number, an equation or a point of the death-rate table and
    press play - the chart below it recomputes.

    As it stands the chart is a flat line, and that is the model being right rather than
    broken: with 80 million people and 80 million units of food, food per person is exactly
    1.0, the birth rate is 0.01, and the death rate the lookup returns at 1.0 is also 0.01.
    The two cancel and the population sits still. Which is what makes the experiments
    visible - every one of them pushes the model off that balance.

    Things worth trying:

    * `foodAvailable` from 80 to 60 million: the population falls and settles near 64 million
    * the `0.01` in `birthRate`: how sensitive is the outcome to the birth rate?
    * a `deathRate` table that falls off more steeply
    """)
    return


@app.cell
def _(Model, sd):
    playground = Model(starttime=1.0, stoptime=10.0, dt=1.0, name="PopulationPlayground")

    pg_population = playground.stock("population")
    pg_births = playground.flow("births")
    pg_deaths = playground.flow("deaths")
    pg_birthRate = playground.converter("birthRate")
    pg_deathRate = playground.converter("deathRate")
    pg_foodPerPerson = playground.converter("foodAvailablePerPerson")
    pg_food = playground.constant("foodAvailable")

    pg_population.initial_value = 80000000.0
    pg_population.equation = pg_births - pg_deaths

    pg_food.equation = 80000000.0
    pg_foodPerPerson.equation = pg_food / pg_population

    pg_birthRate.equation = 0.01 * pg_foodPerPerson
    pg_births.equation = pg_birthRate * pg_population

    playground.points["deathRate"] = [
        [0.0, 1.0],
        [0.1, 0.670320046036],
        [0.2, 0.449328964117],
        [0.3, 0.301194211912],
        [0.4, 0.201896517995],
        [0.5, 0.135335283237],
        [0.6, 0.0907179532894],
        [0.7, 0.0608100626252],
        [0.8, 0.0407622039784],
        [0.9, 0.025],
        [1.0, 0.01],
    ]
    pg_deathRate.equation = sd.lookup(pg_foodPerPerson, "deathRate")
    pg_deaths.equation = pg_deathRate * pg_population

    pg_population.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Thanks for working through this tutorial!
    """)
    return


if __name__ == "__main__":
    app.run()
