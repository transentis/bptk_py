# Front matter the .py format cannot carry; injected on export.
# description: The Make Your PSF Grow model built in Stella Architect, loaded from its XMILE file and run on both engines.
# keywords: system dynamics, professional services firm, growth, business simulation, bptk, bptk-py, python, xmile, stella
#
# The page reads its model from the files beside it, which do not reach the browser,
# so it is shown with its results rather than run.
# interactive: false
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Make Your PSF Grow (Stella)")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # The Same Model in Stella

    The model this chapter builds step by step in the SD DSL also exists as a Stella
    Architect model: `make_your_psf_grow.stmx`, in the XMILE format. BPTK-Py compiles it into
    an SD DSL model and runs it like any other - this page shows how.

    ## The scenario file

    A scenario file beside the page names the XMILE file as `source`, and the file the
    compiled model is written to as `model`:

    ```json
    {
        "psf": {
            "source": "simulation_models/make_your_psf_grow.stmx",
            "model": "simulation_models/make_your_psf_grow",
            "scenarios": {
                "base": {}
            }
        }
    }
    ```

    When `bptk` reads it, the model is compiled - and compiled again whenever the `.stmx`
    changes. [XMILE Step by Step](../../../xmile/xmile_step_by_step/xmile_step_by_step.md)
    explains the details.

    ## Running it

    The Stella model has the same modules as the SD DSL version, so its elements carry the
    same names - `cash.cash`, `kpi.projectBacklog`:
    """)
    return


@app.cell
def _():
    from BPTK_Py import bptk

    bptk = bptk()
    bptk.plot_scenarios(
        scenario_managers=["psf"],
        scenarios=["base"],
        equations=["cash.cash"],
        title="Cash, Base Case",
        x_label="Months",
        y_label="€",
        format="axes",
    )
    return (bptk,)


if __name__ == "__main__":
    app.run()
