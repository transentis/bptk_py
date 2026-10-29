# Front matter the .py format cannot carry; injected on export.
# keywords: system dynamics, xmile, stella, bptk, bptk-py, python, business simulation, beer game, beer distribution game
# description: The Beer Game model built in Stella Architect, loaded from its XMILE file and run on both engines.
#
# The page reads its model from the files beside it, which do not reach the browser,
# so it is shown with its results rather than run.
# interactive: false
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="The Beer Game in Stella")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # The Beer Game in Stella

    The Beer Game model of [Understanding the Beer Game](understanding_the_beergame.md) also
    exists as a Stella Architect model: `beer_game.stmx`, in the XMILE format. BPTK-Py compiles
    it into an SD DSL model and runs it like any other.

    ## The scenario file

    A scenario file beside the page names the XMILE file as `source` and the file the compiled
    model is written to as `model`. Its scenarios set the policy switches of the model; the
    typical game is the base case:

    ```json
    {
      "smBeergameSD": {
        "source": "simulation_models/beer_game.stmx",
        "model": "simulation_models/beer_game",
        "base_constants": {
          "policySettings.steadyStateOn": 0,
          "policySettings.sophisticatedOrderDecisionOn": 0,
          "policySettings.weightingOpenOrders": 0,
          "policySettings.weightingBackorder": 1,
          "policySettings.stockAdjustmentTime": 1
        },
        "scenarios": {
          "typical": {},
          "ignoreBackorders": {
            "constants": {"policySettings.sophisticatedOrderDecisionOn": 1}
          }
        }
      }
    }
    ```

    When `bptk` reads it, the model is compiled - and compiled again whenever the `.stmx`
    changes. [XMILE Step by Step](../../xmile/xmile_step_by_step/xmile_step_by_step.md)
    explains the details.

    ## Running it

    The typical game, with the whiplash that
    [Understanding the Beer Game](understanding_the_beergame.md#supply-chain-dynamics-dealing-with-changing-demands-for-beer)
    explains - the same orders as the SD DSL version of the model gives:
    """)
    return


@app.cell
def _():
    from BPTK_Py import bptk

    bptk = bptk()
    bptk.plot_scenarios(
        scenario_managers=["smBeergameSD"],
        kind="area",
        scenarios=["typical"],
        title="Order Behaviour in a Typical Game",
        x_label="Weeks",
        y_label="Beer Ordered",
        equations=[
            "brewery.actualProduction",
            "distributor.actualOrder",
            "wholesaler.actualOrder",
            "retailer.actualOrder",
            "retailer.incomingOrder",
        ],
        series_names={
            "smBeergameSD_typical_brewery.actualProduction": "Brewery",
            "smBeergameSD_typical_distributor.actualOrder": "Distributor",
            "smBeergameSD_typical_wholesaler.actualOrder": "Wholesaler",
            "smBeergameSD_typical_retailer.actualOrder": "Retailer",
            "smBeergameSD_typical_retailer.incomingOrder": "Consumer",
        },
        format="axes",
    )
    return (bptk,)


if __name__ == "__main__":
    app.run()
