# Front matter the .py format cannot carry; injected on export.
# description: Building a customer acquisition model with the BPTK SD DSL, setting up scenarios and an interactive UI.
# keywords: system dynamics, sd dsl, scenarios, marimo, bptk, bptk-py, python, business simulation
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Building the Customer Acquisition Model with SD DSL")


@app.cell
def _():
    import marimo as mo

    return (mo,)

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Building the Customer Acquisition Model with SD DSL

    Based on the causal loop diagram, we will implement a stock and flow model with the following stocks, flows, converters and constants:

    ![Customer Acquisition CLD](../images/customer_acquisition_stock_flow.svg)
    """)
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Building The Model

    Setting up the model using the SD DSL is quite easy. We first instantiate a model class, which will be the container that holds the model elements. This ensures you can run multiple models in parallel. We then add the stocks, flows, converters and constants, write the equations - the neat thing is that we can write these directly using the model elements - and finally initialize the stocks and set the constants.

    All of this lives in a single cell, and that is deliberate: change any number in it, press play, and every diagram and table below recomputes.
    """)
    return

@app.cell
def _():
    from BPTK_Py import Model
    from BPTK_Py import sd_functions as sd
    model = Model(starttime=1.0,stoptime=60.0, dt=1.0, name="Customer Acquisition SDDSL")

    # stocks
    customers = model.stock("customers")
    potential_customers = model.stock("potential_customers")
    # flows
    customer_acquisition=model.flow("customer_acquisition")
    # converters
    acquisition_through_advertising = model.converter("acquisition_through_advertising")
    acquisition_through_word_of_mouth = model.converter("acquisition_through_word_of_mouth")
    consumers_reached_through_advertising = model.converter("consumers_reached_through_advertising")
    consumers_reached_through_word_of_mouth= model.converter("consumers_reached_through_word_of_mouth")
    market_saturation = model.converter("market_saturation")
    # constants
    initial_customers = model.constant("initial_customers")
    initial_potential_customers = model.constant("initial_potential_customers")
    advertising_success = model.constant("advertising_success")
    consumers_reached_per_euro = model.constant("consumers_reached_per_euro")
    advertising_budget = model.constant("advertising_budget")
    word_of_mouth_success = model.constant("word_of_mouth_success")
    contact_rate = model.constant("contact_rate")

    # equations
    customers.equation = customer_acquisition
    potential_customers.equation = -customer_acquisition
    customer_acquisition.equation=sd.min(potential_customers,acquisition_through_advertising+acquisition_through_word_of_mouth)
    acquisition_through_advertising.equation = advertising_success*consumers_reached_through_advertising
    consumers_reached_through_advertising.equation = consumers_reached_per_euro*advertising_budget*(1-market_saturation)
    market_saturation.equation = customers/(customers+potential_customers)
    acquisition_through_word_of_mouth.equation = word_of_mouth_success*consumers_reached_through_word_of_mouth
    consumers_reached_through_word_of_mouth.equation=contact_rate*customers*(1-market_saturation)

    # initial values and constants
    customers.initial_value=initial_customers
    potential_customers.initial_value=initial_potential_customers
    initial_customers.equation = 0.0
    initial_potential_customers.equation = 60000.0
    advertising_success.equation = 0.1
    consumers_reached_per_euro.equation = 100.0
    advertising_budget.equation = 100.0
    word_of_mouth_success.equation = 0.01
    contact_rate.equation = 10.0
    return customer_acquisition, customers, model

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The model is now complete and we can directly plot the behaviour of the model elements over time:
    """)
    return

@app.cell
def _():
    #| echo: false
    import matplotlib.pyplot as plt
    return (plt,)

@app.cell
def _(customers, plt):
    plt.close("all")  # see the note on the interactive cell below
    customers.plot(format="axes")
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Of course you can also access the underlying Pandas dataframe:
    """)
    return

@app.cell
def _(customers):
    customers.plot(return_df=True).iloc[1:10]
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    For debugging purposes it can be useful to take a look at the internal representation of the model equations - these are stored as Python lambda functions.
    """)
    return

@app.cell
def _(customers):
    customers.function_string
    return

@app.cell
def _(customer_acquisition):
    customer_acquisition.function_string
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Setting Up Scenarios
    """)
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Scenarios are just particular settings for the constants and graphical functions in your model and scenario managers are a simple way of grouping scenarios.

    You can create scenarios directly in Python (which we will do here), but the easiest way to maintain them is to keep them in separate JSON files – you can define as many scenario managers and scenarios in a file as you would like and use as many files as you would like.

    Each scenario manager references the model it pertains to. So you can run multiple simulation models in one notebook.

    If you do keep them in files, BPTK-Py looks for a `scenarios/` folder beside your notebook and loads everything it finds there – including the underlying simulation models. The [XMILE quickstart](../xmile/xmile.md) works that way; here we stay in Python.
    """)
    return

@app.cell
def _(model):
    scenario_manager={
        "sddsl_customer_acquisition":{
            "model":model,
            "base_constants":{
                "initial_customers" : 0.0,
                "initial_potential_customers" : 60000.0,
                "advertising_success": 0.1,
                "consumers_reached_per_euro" : 100.0,
                "advertising_budget" : 100.0,
                "word_of_mouth_success": 0.01,
                "contact_rate" : 10.0
            }
        }
    }
    return (scenario_manager,)

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    To manage the scenarios you need to instantiate the bptk class - this class stores the scenario managers and scenarios and provides lots of convenient functions to plot data, export model results or import data.

    A convenient feature of scenarios is that you only have to define variables that change - essentially the scenario manager first takes the constants as set in the model itself and then overrides them with the settings from the scenario.
    """)
    return

@app.cell
def _(scenario_manager):
    import BPTK_Py
    bptk = BPTK_Py.bptk()
    bptk.register_scenario_manager(scenario_manager)
    bptk.register_scenarios(
        scenario_manager="sddsl_customer_acquisition",
        scenarios=
        {
            "base":{
            },
            "low_word_of_mouth":{
                "constants":{
                    "word_of_mouth_success":0.001
                }
            },
            "high_word_of_mouth":{
                "constants":{
                    "word_of_mouth_success":0.1
                }
            },
            "interactive_scenario":{}
        }
    )
    return (bptk,)

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Now we can plot the three scenarios against each other:
    """)
    return

@app.cell
def _(bptk, plt):
    plt.close("all")  # see the note on the interactive cell below
    bptk.plot_scenarios(
        scenario_managers=["sddsl_customer_acquisition"],
        scenarios=["base","low_word_of_mouth","high_word_of_mouth"],
        equations=["customers"],
        series_names={
            "sddsl_customer_acquisition_base_customers":"Base",
            "sddsl_customer_acquisition_low_word_of_mouth_customers":"Low Word of Mouth",
            "sddsl_customer_acquisition_high_word_of_mouth_customers":"High Word of Mouth",
        }, format="axes"
    )
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    You can ask a `bptk` instance at any time which scenarios it knows about:
    """)
    return

@app.cell
def _(bptk):
    bptk.get_scenario_names([],format="dict")
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Building An Interactive UI

    It is easy to build interactive dashboards using marimo's UI elements – all you need from BPTK is the ability to plot graphs.
    """)
    return

@app.cell
def _(mo):
    # Not `word_of_mouth_success`: the model already binds that name, and marimo
    # forbids one name in two cells.
    word_of_mouth_slider = mo.ui.slider(
        start=0.001, stop=0.1, step=0.001, value=0.01, show_value=True,
        label="Word Of Mouth Success"
    )
    return (word_of_mouth_slider,)

@app.cell
def _(bptk, mo, plt, word_of_mouth_slider):
    # Every plot_scenarios call leaves its figure in matplotlib's registry, and this
    # cell makes three of them on every slider move - a dozen moves fill the
    # browser's heap and the page stops answering. Closing the previous run's
    # figures keeps it bounded; they have already been rendered by then.
    plt.close("all")

    scenario = bptk.get_scenario("sddsl_customer_acquisition", "interactive_scenario")
    scenario.constants["word_of_mouth_success"] = word_of_mouth_slider.value
    bptk.reset_scenario_cache(
        scenario_manager="sddsl_customer_acquisition", scenario="interactive_scenario"
    )

    _customers = bptk.plot_scenarios(
        scenario_managers=["sddsl_customer_acquisition"],
        scenarios=["interactive_scenario"],
        equations=["customers"],
        title="Customers",
        x_label="Time",
        y_label="No. of Customers",
        format="axes",
    )
    _acquisition = bptk.plot_scenarios(
        scenario_managers=["sddsl_customer_acquisition"],
        scenarios=["interactive_scenario"],
        equations=["customer_acquisition"],
        title="Customer Acquisition",
        x_label="Time",
        y_label="No. of Customers",
        format="axes",
    )
    _scenarios = bptk.plot_scenarios(
        scenario_managers=["sddsl_customer_acquisition"],
        scenarios=["base", "low_word_of_mouth", "high_word_of_mouth", "interactive_scenario"],
        equations=["customers"],
        series_names={
            "sddsl_customer_acquisition_base_customers": "Base",
            "sddsl_customer_acquisition_interactive_scenario_customers": "Interactive",
            "sddsl_customer_acquisition_low_word_of_mouth_customers": "Low Word of Mouth",
            "sddsl_customer_acquisition_high_word_of_mouth_customers": "High Word of Mouth",
        },
        format="axes",
    )

    # Slider and diagram in one output block: apart, the reader has to scroll
    # between the control and what it controls.
    mo.vstack([
        word_of_mouth_slider,
        mo.ui.tabs({
            "Customers": _customers.figure,
            "Customer Acquisition": _acquisition.figure,
            "Scenarios": _scenarios.figure,
        }),
    ])
    return

if __name__ == "__main__":
    app.run()
