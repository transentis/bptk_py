# Front matter the .py format cannot carry; injected on export.
# description: A closer look at the mathematics underlying the System Dynamics libary
# keywords: system dynamics, systemdynamics, sd dsl, bptk, bptk-py, python, business simulation
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="The Mathematics Underlying The System Dynamics Libary")


@app.cell
def _():
    import marimo as mo

    return (mo,)




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # The Mathematics Underlying The System Dynamics Library
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    One of the nice features of System Dynamics is that each element in a System Dynamics model has a precise mathematical definition.

    The computationally relevant elements in a System Dynamics model are:

    * Stocks
    * Flows
    * Converters
    * Constants
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Each stocks represents a difference equation, where the value of a stock $S$ at time $t$ depends on its value at time $t-dt$ plus the net inflow per $dt$:
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    Stock(t)=Stock(t-dt)+dt \times \sum_{Inflows}Inflow(t-dt)-dt \times \sum_{Outflows}Outflow(t-dt)
    \end{equation*}
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Assuming the simulation starts at time $t_0$, we need to define the inital value of the stock:
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    Stock(t_0)=initial\_value
    \end{equation*}
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Note that stocks only depend on their inital value and the value of their flows since.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Flows are functions of their input and may or may not depend on time. Any model element can be an input to a flow.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    Flow(t) = function(input_1(t),...,input_n(t),t)
    \end{equation*}
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Constants are special cases of converters. Flows are mathematically equivalent to converters - the only difference is that flows can flow in to our out of stocks, while converters cannot.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    Converter(t) = function(input_1(t),...,input_n(t),t)
    \end{equation*}
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    That's really all there is to defining the equations for a System Dyamics model.

    Using the SD DSL, you don't need to worry about formulating the equations for yourself, because this is done for you under the hood by the framework.

    But it is important that you understand what the elements stand for.

    ## Turning Difference Equations into Integral Equations

    If you have a little mathematical background you will have noticed that we could rewrite the difference equation for a stock as follows:
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \frac{Stock(t)-Stock(t-dt)}{dt} =\sum_{Inflows}Inflow(t-dt)-\sum_{Outflows}Outflow(t-dt)
    \end{equation*}
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    If we let $dt$ get infinitesimally small, we end up with an ordinary differential equation (ODE) which shows that the derivative of the stock (it's rate of change) is defined by net difference between its inflows and outflows:
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \frac{dStock(t)}{dt}=\sum_{Inflows}Inflow(t-dt)-\sum_{Outflows}Outflow(t-dt)
    \end{equation*}
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    One consequence of this is that we can use System Dynmica models to numerically solve ordinary differential equations - let's look at a concrete example, the *[Harmonic Oscillator](https://en.wikipedia.org/wiki/Harmonic_oscillator)*
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Example: The Harmonic Oscillator
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    A simple example for a harmonic oscillator is a mass on a spring. The force exerted by the spring on the mass is proportional to position of the mass: the further the mass is pulled from the equilibrium position, the stronger the force.

    The proportional factor is called the spring constant or the *Stiffness* of the spring.

    ![Weight on a Spring](spring.svg)

    Mathematically we can write this as:

    \begin{equation*}
    Force =- Stiffness * Position
    \end{equation*}

    Knowing that the force exerted is defined as mass multiplied by the acceleration of the mass, this gives us the following equation:

    \begin{equation*}
    Mass \times Acceleration =- Stiffness * Position
    \end{equation*}

    And because Acceleration is the second derivative of the position, we end up with the following ordinary differential equation for the harmonic oscillator:

    \begin{equation*}
    \frac{d^2Acceleration}{dt^2} =- \frac{Stiffness}{Mass} * Position
    \end{equation*}

    This differential equation has an analytical solution:

    \begin{equation*}
    Position(t) = \cos(t \times \sqrt \frac{Stiffness}{Mass} )
    \end{equation*}
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Let's see how we could model this using System Dynamics: the flow of a stock is equivalent to the first derivative ... so in order to model the second derivative, we must explicitly model the first derivative of the position, which is its velocity.

    Hence the differential equation above is equivalent to the following diagram:

    ![Stock and Flow Diagram of Harmonic Oscillator](harmonic_oscillator.svg)
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Using the SD DSL, we can express the diagram as follows - the elements, their
    equations and an ``analytical_solution`` converter carrying the closed form of the
    same oscillator, all in one cell. Everything here is editable: change the ``mass``,
    the ``stiffness`` or ``dt`` and press play.
    """)
    return


@app.cell
def _():
    from BPTK_Py import Model
    from BPTK_Py import sd_functions as sd

    model = Model(starttime=0.0, stoptime=10.0, dt=0.001, name="Oscillator")

    # Two stocks for position and velocity, a biflow for each because both can go either
    # way, and a converter for the acceleration.
    position = model.stock("position")
    velocity = model.stock("velocity")
    change_in_position = model.biflow("change_in_position")
    change_in_velocity = model.biflow("change_in_velocity")
    acceleration = model.converter("acceleration")
    mass = model.constant("mass")
    stiffness = model.constant("stiffness")
    analytical_solution = model.converter("analytical_solution")
    diff = model.converter("diff")

    position.initial_value = 1.0
    position.equation = change_in_position
    change_in_position.equation = velocity

    velocity.initial_value = 0.0
    velocity.equation = change_in_velocity
    change_in_velocity.equation = acceleration

    acceleration.equation = -mass * stiffness * position

    mass.equation = 1.0
    stiffness.equation = 1.0

    # `analytical_solution` is the closed form of the same oscillator, and `diff` the
    # distance between the two - which is what makes the numerical error visible below.
    analytical_solution.equation = -1 * sd.cos(sd.pi() + sd.time())
    diff.equation = position - analytical_solution
    return (model,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    In order to plot the equations it is easiest to set up a scenario:
    """)
    return


@app.cell
def _(model):
    from BPTK_Py import bptk

    bptk = bptk()

    # Registering a model whose scenario manager already exists leaves the *old* model in
    # place - `register_scenario_manager` warns and keeps it. Drop the registry first, or
    # an edit above will be plotted against the model you started with.
    bptk.reset_all_scenarios()
    bptk.register_model(model)

    bptk.plot_scenarios(
        scenario_managers=["smOscillator"],
        scenarios=["base"],
        equations=["position", "analytical_solution"],
        format="axes",
    )
    return (bptk,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The numerical solution is quite precise (and the precision can be increased further by decreasing dt) - you can see nicely in the following graph that the error increases over time:
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smOscillator"],
        scenarios=["base"],
        equations=["diff"], format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ``return_df=True`` hands back the numbers behind the chart, so the error can be filtered
    rather than eyeballed. There is no error greater than 0.004 - the table below comes back
    empty:
    """)
    return


@app.cell
def _(bptk):
    df = bptk.plot_scenarios(
        scenario_managers=["smOscillator"],
        scenarios=["base"],
        equations=["diff"],
        return_df=True,
    )
    df[df["diff"] > 0.004]
    return (df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    But 672 of the 10,001 timesteps have an error above 0.003:
    """)
    return


@app.cell
def _(df):
    df[df["diff"] > 0.003]
    return


if __name__ == "__main__":
    app.run()
