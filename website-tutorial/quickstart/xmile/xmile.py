# Front matter the .py format cannot carry; injected on export.
# description: Running a Stella Architect XMILE model with BPTK using a scenario file.
# keywords: xmile, stella architect, system dynamics, scenarios, bptk, bptk-py, python, business simulation
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Customer Acquisition as an XMILE Model")


@app.cell
def _():
    import marimo as mo

    return (mo,)

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Customer Acquisition as an XMILE Model
    """)
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Many modelers prefer to build models using visual modeling environments and not directly in code. One such environment is Stella Architect. Using Stella Architect, you can build System Dynamics models visually. You can then import them into Python using BPTK and work with them much like with any other model.

    The framework transpiles the XMILE model into an SD DSL model and does so again whenever you change it in the visual modeling environment, as [XMILE Step by Step](../../xmile/xmile_step_by_step/xmile_step_by_step.md) explains. So you can model in Stella Architect and experiment with scenarios in a notebook.
    """)
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Setting Up The Model

    This is what our customer acquisition model looks like in Stella Architect:

    ![Stella Architect](../images/stella_architect.png)
    """)
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Setting Up The Scenarios

    To work with XMILE models, all we have to do is set up a [scenario file](./scenarios/scenarios.json) in the `scenarios` folder.

    The scenario file tells the framework where to find the [XMILE model](./simulation_models/customer_acquisition_xmile.stmx) and which scenarios to set up.

    In our case the file looks like this - the only difference to the SD DSL scenario definition is the inclusion of the XMILE source, which [XMILE Step by Step](../../xmile/xmile_step_by_step/xmile_step_by_step.md) explains.

    ```JSON
    {
        "xmile_customer_acquisition":
        {
            "source":"simulation_models/customer_acquisition_xmile.stmx",
            "model":"simulation_models/customer_acquisition_xmile",
            "scenarios":
            {
              "base": { },

            "low_word_of_mouth":{
                "constants":{
                    "wordOfMouthSuccess":0.001
                }
            },
            "high_word_of_mouth":{
                "constants":{
                    "wordOfMouthSuccess":0.1
                }
            }
            }
        }
    }

    ```
    """)
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    As soon as we instantiate bptk, the framework automatically searches the scenarios folder for scenarios and loads them.
    """)
    return

@app.cell
def _():
    import BPTK_Py

    bptk_3 = BPTK_Py.bptk()
    return (bptk_3,)

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Let's list all the scenarios and equations the framework finds.
    """)
    return

@app.cell
def _(bptk_3, mo):
    with mo.capture_stdout() as output:
        bptk_3.list_equations(scenario_managers=['xmile_customer_acquisition'], scenarios=[])

    mo.plain_text(output.getvalue())
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We directly plot the scenarios:
    """)
    return

@app.cell
def _(bptk_3):
    bptk_3.plot_scenarios(
        scenario_managers=['xmile_customer_acquisition'],
        scenarios=['base', 'high_word_of_mouth', 'low_word_of_mouth'],
        equations=['customers'],
        series_names={
            'xmile_customer_acquisition_base_customers': 'Base',
            'xmile_customer_acquisition_low_word_of_mouth_customers': 'Low Word of Mouth',
            'xmile_customer_acquisition_high_word_of_mouth_customers': 'High Word of Mouth',
        },
        format="axes",
    )
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    NOTE: Once the XMILE file has been transpiled, the model runs without the software that created it - on the Python engine or on the Rust engine.
    """)
    return

if __name__ == "__main__":
    app.run()
