# Front matter the .py format cannot carry; injected on export.
# keywords: system dynamics, balancing loop, system archetype, causal loop diagram,stock and flow diagram, bptk, bptk-py, python, business simulation
# description: Simulation models and interactive dashboards for balancing, goal seeking feedback loops
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Balancing Feedback Archetype")


@app.cell
def _():
    import marimo as mo

    return (mo,)




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Balancing Feedback Archetype

    Balancing feedback loops seek to close the gap between the current state of a system and it's desired state (the goal state).

    Even simple balancing loops can exhibit quite complex behaviour, because in reality we often encounter delays within the loop.

    The following causal loop diagram illustrates the key elements of a balancing feedback loop:

    ![Causal Loop Diagram of the Balancing Feedback Loop](cld_balancing_loop.svg)

    The diagram explains what happens when the _Actual State_ of a system deviates from the _Desired State_ of the system: The system observes the gap and then takes appropriate action to close the gap. There may be delays in observing and comunicating the current state of the system, there may be delays in making decisions regarding the correct actions to take, and there may be delays in actually implementing the actions once a decision has been made.

    Typical examples from corporate life are reporting delays: in many companies, financial reports are always lagging behind reality, so it may take a while before management realizes that the profitability of the company has decreased. Management may then take some time to agree on which measures to take, e.g. to cut costs or to improve marketing and sales processes. Then again it may take some time to actually take action. e.g. because it takes time to assemble an appropriate task force. Meanwhile the state of the system has changed yet again. Taken together, delays may lead to oscialltory behaviour, as illustrated in the graph.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## A Stock and Flow Model for the Balancing Feedback Archetype

    Let's build a simple stock and flow model of the balancing feedback loop:

    ![Stock and Flow Diagram of Balancing Feedback Loop](sfd_balancing_loop.svg)

    The only stock in the system is the actual state of the system, which depends on its past values. We model the change in the stock as a biflow, which depends on the (delayed) action.

    The size of the action depends on the (delayed) gap and on the adjustment time – the adjustment time is a measure of how quickly we wish to close the gap.

    The gap itself is simply the difference between the desired state and the (delayed measurement of the) actual state.

    Based on this model, we can easily create the following model using the SD DSL:
    """)
    return


@app.cell
def _():
    from BPTK_Py import Model, bptk
    from BPTK_Py import sd_functions as sd
    import matplotlib.pyplot as plt
    model = Model(starttime=0.0,stoptime=260.0,dt=1.0,name='Balancing')
    # decleare elements
    actual_state = model.stock("actual_state")
    change = model.biflow("change")
    desired_state = model.constant("desired_state")
    gap = model.converter("gap")
    action = model.converter("action")
    adjustment_time = model.constant("adjustment_time")
    measurement_delay = model.constant("measurement_delay")
    decision_delay = model.constant("decision_delay")
    action_delay = model.constant("action_delay")
    # define elements
    actual_state.initial_value=1.0
    actual_state.equation=change

    change.equation = sd.delay(model,action,action_delay,0.0)
    adjustment_time.equation= 30.0
    action.equation = sd.delay(model,gap,decision_delay,0.0)/adjustment_time

    gap.equation = desired_state-sd.delay(model, actual_state, measurement_delay,1.0)

    desired_state.equation = 50.0

    measurement_delay.equation = 0.0
    decision_delay.equation = 0.0
    action_delay.equation = 0.0
    bptk_1 = bptk()
    bptk_1.register_model(model)
    return bptk_1, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    In the base scenario, we assume there are no delays. The desired state is set to 50.0 in all scenarios and the actual state is initially 1.0. Assuming an adjustment time of 30 weeks, this leads to the following plot of actual state and desired state:
    """)
    return


@app.cell
def _(bptk_1):
    bptk_1.plot_scenarios(title='Balancing loops are goal seeking loops', scenario_managers=['smBalancing'], scenarios=['base'], equations=['actual_state', 'desired_state'], format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The actual state slowly adjust to the desired state - note that it takes much longer then 40 weeks to adjust to the desired state: the size of the action depends on the size of the gap, as the gap gets smaller, so does the size of the action.

    Now let's take a look at what happens when we adjust the delays - in the next scenario, we assume all delays are equal to 10 weeks.
    """)
    return


@app.cell
def _(bptk_1):
    bptk_1.register_scenarios(scenario_manager='smBalancing', scenarios={'oscillations': {'constants': {'adjustment_time': 12.0, 'measurement_delay': 4.0, 'decision_delay': 4.0, 'action_delay': 4.0}}})
    return


@app.cell
def _(bptk_1):
    bptk_1.plot_scenarios(title='Delays lead to oscillations', scenario_managers=['smBalancing'], scenarios=['oscillations'], equations=['actual_state', 'desired_state'], format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    In this scenario we see oscillating behavior: first it takes quite some time for any change in the actual state. Because of the delay in the observation of the actual state, we take to much action and overshoot the goal: the actual state becomes bigger than the desired state.

    The system then corrects its action downwards, but again the desired state is overshot and the actual state ends up being to small. The oscillations dampen down, but we can see it will take some time for the system to adjust.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Experimeting with the Balancing Feedback Archetype

    The dashboard below let's you experiment with different settings for delays and adjustment times.
    """)
    return


@app.cell
def _(bptk_1, mo):
    bptk_1.register_scenarios(scenario_manager='smBalancing', scenarios={'interactive': {}})

    adjustment_time_slider = mo.ui.slider(
        start=1.0, stop=100.0, step=1.0, value=12.0, show_value=True,
        label="Adjustment Time"
    )
    measurement_delay_slider = mo.ui.slider(
        start=0.0, stop=4.0, step=1.0, value=0.0, show_value=True,
        label="Measurement Delay"
    )
    decision_delay_slider = mo.ui.slider(
        start=0.0, stop=4.0, step=1.0, value=0.0, show_value=True,
        label="Decision Delay"
    )
    action_delay_slider = mo.ui.slider(
        start=0.0, stop=4.0, step=1.0, value=0.0, show_value=True,
        label="Action Delay"
    )
    return (
        action_delay_slider,
        adjustment_time_slider,
        decision_delay_slider,
        measurement_delay_slider,
    )


@app.cell
def _(
    action_delay_slider,
    adjustment_time_slider,
    bptk_1,
    decision_delay_slider,
    measurement_delay_slider,
    mo,
    plt,
):
    # Every plot leaves its figure in matplotlib's registry, and this cell re-runs on
    # every move of a slider - a dozen moves fill the browser's heap and the page stops
    # answering. Closing the previous run's figures keeps it bounded; they have already
    # been rendered by then.
    plt.close("all")

    scenario = bptk_1.get_scenario("smBalancing", "interactive")
    scenario.constants["adjustment_time"] = adjustment_time_slider.value
    scenario.constants["measurement_delay"] = measurement_delay_slider.value
    scenario.constants["decision_delay"] = decision_delay_slider.value
    scenario.constants["action_delay"] = action_delay_slider.value
    bptk_1.reset_scenario_cache(scenario_manager="smBalancing", scenario="interactive")

    _axes = bptk_1.plot_scenarios(
        scenario_managers=["smBalancing"],
        scenarios=["interactive"],
        equations=["actual_state", "desired_state"],
        series_names={
            "smBalancing_interactive_actual_state": "Actual State",
            "smBalancing_interactive_desired_state": "Desired State",
        },
        title="Experimenting with Balancing Feedback Loops",
        x_label="Week",
        y_label="State",
        format="axes",
    )

    # Sliders and diagram in one output block.
    mo.vstack([
        adjustment_time_slider,
        measurement_delay_slider,
        decision_delay_slider,
        action_delay_slider,
        _axes.figure,
    ])
    return


if __name__ == "__main__":
    app.run()
