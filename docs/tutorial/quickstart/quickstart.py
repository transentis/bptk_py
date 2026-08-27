# Front matter the .py format cannot carry; injected on export.
# description: Overview of the BPTK computational modeling framework.
# keywords: agent-based modeling, abm, bptk, bptk-py, xmile, stella, python, business simulation, marimo, Pandas, Matplotlib
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Business Prototyping Toolkit Quickstart")


@app.cell
def _():
    import marimo as mo

    return (mo,)

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Business Prototyping Toolkit Quickstart

    ![BPTK Quickstart](./images/hero.svg)
    """)
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The Business Prototyping Toolkit (BPTK) is a computational modeling framework that enables you to build simulation models using System Dynamics (SD) and/or agent-based modeling (ABM) and manage simulation scenarios with ease.

    The framework is used to build models of markets, business models, organisations and entire business ecosystems. It can be used to build small, explorative models — such as the one on the following pages — as well as large models with hundreds of thousands of equations.

    The guiding principle of the framework is to let the modeler concentrate on building simulation models by providing a seamless interface for managing model settings and scenarios and for plotting simulation results. It takes a "minimalistic" approach and just provides the necessary modeling and simulation functionality, using standard open source packages for everything else.

    * Plotting is built in, using Matplotlib — one call gives you a chart of any scenario. Because the results are plain Matplotlib and Pandas objects, you can take them further whenever you need to: your own chart styles, or interactive dashboards built in a notebook environment such as [marimo](https://marimo.io).
    * Simulation results are returned as Pandas dataframes.
    * Numerics via NumPy and SciPy.

    Model settings and scenarios are kept in JSON files. These settings are automatically loaded by the framework upon initialization, as are the model classes themselves. This makes interactive modeling, coding and testing very painless, especially in a reactive notebook environment such as marimo.
    """)
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Key Components of the Business Prototyping Toolkit
    """)
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The toolkit has been available since 2018 and supports Agent-based modeling (ABM), System Dynamics modeling (SD) and hybrid models that use both.

    There is also support for importing XMILE models created with external modeling environments, such as [iseesystems](https://www.iseesystems.com) Stella Architect or iThink.

    Once you have a model, you can then define and manage different simulation scenarios, plot the results of those scenarios and build interactive dashboards.

    The framework also provides a simple REST API server, which lets you serve up and query models using web technology.

    ![BPTK Building Blocks](./images/bptk_components.svg)

    We used it to build a dashboard illustrating different COVID scenarios; the repositories for the [dashboard](https://github.com/transentis/sim-covid-dashboard) and the [simulation](https://github.com/transentis/sim-covid-19) are available on [GitHub](https://github.com/transentis/).
    """)
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Example Model: Simulating Customer Acquisition using the Bass Diffusion Model
    """)
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    To illustrate the different ways of building simulation models using BPTK, we will use a simple model of customer acquisition known as the [Bass Diffusion Model](https://en.wikipedia.org/wiki/Bass_diffusion_model). It describes the process of how new products or services are adopted by consumers.

    We will build it four times over: with the System Dynamics DSL, with agent-based modeling, as a hybrid of the two, and as a XMILE model.

    The basic structure of the model is illustrated in the following causal loop diagram:

    ![Customer Acquisition CLD](./images/customer_acquisition_cld.svg)
    """)
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Contents

    The quickstart is split into one page per modeling approach - each builds the same
    customer acquisition example, so you can compare them directly.

    Every one of them runs right here in your browser: press the play button on a cell,
    change a value, and the cells below it recompute. To run them on your own machine
    instead, see [Installation](../usage/installation.md).

    * [System Dynamics with the SD DSL](sd_dsl/sd_dsl.md) - build the model in Python,
      set up scenarios and add an interactive slider
    * [Agent-based Modeling](agent_based/agent_based.md) - the same example with agents
      that send each other events
    * [Hybrid ABM and SD Models](hybrid/hybrid.md) - agents that contain a System
      Dynamics model
    * [XMILE Models](xmile/xmile.md) - run a model built in Stella Architect
    """)
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Further Examples
    """)
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    You can find more examples in the [Model Library](../model_library/model_library.md).
    """)
    return

if __name__ == "__main__":
    app.run()
