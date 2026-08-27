# Front matter the .py format cannot carry; injected on export.
# keywords: system dynamics, limits to growth, system archetype, causal loop diagram,stock and flow diagram, bptk, bptk-py, python, business simulation
# description: Simulation model and interactive dashboard for the limits to growth archetype
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Limits to Growth Archetype")


@app.cell
def _():
    import marimo as mo

    return (mo,)




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Limits to Growth Archetype

    Nothing can grow indefinitely, hence a reinforceing, growing loop will destroy any system that is part of unless it is kept in check by a balancing loop.

    The following causal loop diagram shows the limits to growth archetype in its simplest form:

    ![Causal Loop Diagram of Limits to Growth Archetype](cld_limits_to_growth.svg)

    At is heart is a reinforcing loop that changes the state of the system according to a growth factor, just as in the reinforcing loop archetype. But in contrast to that archetype, the growth factor isn't constant but is limit by the resource adequacy of the system.

    The resource adequacy get's smaller and smaller when the systems state approaches the carrying capacity.

    If there are no delays in the system, then this limits to growth archetype while display S-shaped growth. If there are delays present, then the growth of the system will overshoot the carrying capacity and then will oscillate around that value.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## A Stock and Flow Model of the Limits To Growth Archetype

    Let's take a look at a stock and flow diagram for this archetype. In this diagram, we've separated the fractional change into a constant, which is then multiplied by the resource adequacy. This leads to an _adjusted fractional change_

    ![Stock and Flow Diagram of the Limits To Growth Archetype](sfd_limits_to_growth.svg)

    Given the diagram, we can build a model as shown below.
    """)
    return


@app.cell
def _():
    from BPTK_Py import Model, bptk
    from BPTK_Py import sd_functions as sd
    import matplotlib.pyplot as plt
    model = Model(starttime=0.0,stoptime=260.0,dt=1.0,name='Limits_to_growth')
    # decleare elements
    state = model.stock("state")
    change = model.biflow("change")
    adjusted_fractional_change = model.converter("adjusted_fractional_change")
    fractional_change = model.constant("fractional_change")
    resource_adequacy = model.converter("resource_adequacy")
    carrying_capacity = model.constant("carrying_capacity")
    delay_resource_adequacy = model.constant("delay_resource_adequacy")
    # define elements
    state.initial_value=1.0
    state.equation=change

    change.equation = state*adjusted_fractional_change
    adjusted_fractional_change.equation= fractional_change*resource_adequacy
    resource_adequacy.equation = (carrying_capacity - sd.delay(model, state, delay_resource_adequacy,1.0))/carrying_capacity
    fractional_change.equation=0.1
    carrying_capacity.equation= 50.0

    delay_resource_adequacy.equation = 0.0
    bptk_1 = bptk()
    bptk_1.register_model(model)
    return bptk_1, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The plot below shows that the Limits to Growth archetype leads to S-shaped growth if there are no delays present in the system.
    """)
    return


@app.cell
def _(bptk_1):
    bptk_1.plot_scenarios(title='S-Shaped Growth', scenario_managers=['smLimits_to_growth'], scenarios=['base'], equations=['state', 'carrying_capacity'], format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Now let's add a scenario that introduces a delay: in this case we assume that the adjustment of the resource adequacy lags behind the actual system state by 10 weeks - this leads to an oscillatory behavior as displayed in the plot below.
    """)
    return


@app.cell
def _(bptk_1):
    bptk_1.register_scenarios(scenario_manager='smLimits_to_growth', scenarios={'oscillations': {'constants': {'delay_resource_adequacy': 10.0}}})
    return


@app.cell
def _(bptk_1):
    bptk_1.plot_scenarios(scenario_managers=['smLimits_to_growth'], scenarios=['oscillations'], equations=['state', 'carrying_capacity'], format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Experimenting with the Limits To Growth Archetype
    """)
    return


@app.cell
def _(bptk_1, mo):
    bptk_1.register_scenarios(scenario_manager='smLimits_to_growth', scenarios={'interactive': {}})

    delay_slider = mo.ui.slider(
        start=0.0, stop=20.0, step=1.0, value=10.0, show_value=True, label="Delay"
    )
    change_rate_slider = mo.ui.slider(
        start=0.0, stop=0.2, step=0.01, value=0.1, show_value=True,
        label="Fractional Change Rate"
    )
    return change_rate_slider, delay_slider


@app.cell
def _(bptk_1, change_rate_slider, delay_slider, mo, plt):
    # Every plot leaves its figure in matplotlib's registry, and this cell re-runs on
    # every move of a slider - a dozen moves fill the browser's heap and the page stops
    # answering. Closing the previous run's figures keeps it bounded; they have already
    # been rendered by then.
    plt.close("all")

    scenario = bptk_1.get_scenario("smLimits_to_growth", "interactive")
    scenario.constants["delay_resource_adequacy"] = delay_slider.value
    scenario.constants["fractional_change"] = change_rate_slider.value
    bptk_1.reset_scenario_cache(
        scenario_manager="smLimits_to_growth", scenario="interactive"
    )

    _axes = bptk_1.plot_scenarios(
        scenario_managers=["smLimits_to_growth"],
        scenarios=["interactive"],
        equations=["state", "carrying_capacity"],
        series_names={
            "smLimits_to_growth_interactive_state": "State",
            "smLimits_to_growth_interactive_carrying_capacity": "Carrying Capacity",
        },
        title="System State",
        x_label="Week",
        y_label="State",
        format="axes",
    )

    # Sliders and diagram in one output block: apart, the reader has to scroll
    # between the control and what it controls.
    mo.vstack([delay_slider, change_rate_slider, _axes.figure])
    return


if __name__ == "__main__":
    app.run()
