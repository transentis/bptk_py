# Front matter the .py format cannot carry; injected on export.
# description: Agent-based model of the Bass Diffusion Model
# keywords: agent-based modeling, abm, business prototyping, bptk, bptk-py, python, business simulation
#
# The reader can do nothing here but look at the chart - the model comes from a scenario
# file and no cell offers anything worth editing. So the render bakes the picture in and
# the browser does not run it: browser execution would buy nothing and cost the plot.
# interactive: false
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Bass Diffusion Model")


@app.cell
def _():
    import marimo as mo

    return (mo,)




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Bass Diffusion Model
    **An Agent-based Implementation**

    This is an implementation of the Bass Diffusion model as an agent-based model using the
    BPTK-Py framework. It simulates 10,000 individual customers over 60 timesteps, so the
    chart below is computed when this page is built rather than in your browser.
    """)
    return


@app.cell
def _():
    ## BPTK Package
    from BPTK_Py.bptk import bptk 

    bptk = bptk()
    bptk.plot_scenarios(
        scenario_managers=["ABMsmBass"],
        kind="area",
        scenarios=["scenarioBassBase"],
        agents=["customer"],
        agent_states=["potentialCustomer", "currentCustomer"],
        format="axes",
    )
    return


if __name__ == "__main__":
    app.run()
