# Front matter the .py format cannot carry; injected on export.
# keywords: system dynamics,sd dsl, bptk, bptk-py, python, business simulation, beer game, beer distribution game
# description: An analysis of the Beer Distribution Game using System Dynamics and the System Dynamics Domain Specific Language for Python (SD DSL)
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="The Beer Distribution Game")


@app.cell
def _():
    import marimo as mo

    return (mo,)




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Understanding The Beergame - XMILE Version
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    >This page follows the blog post [Understanding The Beer Game](https://www.transentis.com/understanding-the-beer-game/) from the [transentis blog](https://www.transentis.com/blog). It uses a version of the Beer Game built using System Dynamics and iseesystems Stella modeling environment. You can find the Stella model in the `simulation_models` directory (`beer_game.stmx`)
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This notebook contains the plots for a beergame simulation that was built using Stella Architect / XMILE. This repository also contains notebooks with ABM and SD DSL versions of the beergame model.
    """)
    return


@app.cell
def _():
    from BPTK_Py.bptk import bptk 

    bptk = bptk()
    bptk.plot_scenarios(
        scenario_managers=["smBeergameSD"],
        kind="area",
        scenarios=["typical"],
        title="Order Behaviour in a Typical Game",
        x_label="Weeks",
        y_label="Beer Ordered",
        equations=["brewery.actualProduction","distributor.actualOrder","wholesaler.actualOrder","retailer.actualOrder", "retailer.incomingOrder"],
        series_names={
            "smBeergameSD_typical_brewery.actualProduction" : "Brewery",
            "smBeergameSD_typical_distributor.actualOrder" : "Distributor",
            "smBeergameSD_typical_wholesaler.actualOrder": "Wholesaler",
            "smBeergameSD_typical_retailer.actualOrder": "Retailer",
            "smBeergameSD_typical_retailer.incomingOrder": "Consumer"
        }, format="axes"
    )
    return (bptk,)


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smBeergameSD"],
        kind="area",
        scenarios=["typical"],
        title="Consumer Orders",
        x_label="Weeks",
        y_label="Beer Ordered",
        equations=["retailer.incomingOrder"],
        series_names={
            "smBeergameSD_typical_retailer.incomingOrder": "Consumer"
        }, format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smBeergameSD"],
        kind="area",
        scenarios=["typical"],
        title="Surplus in a Typical Game",
        x_label="Weeks",
        y_label="Beer Surplus",
        equations=["brewery.surplus","distributor.surplus","wholesaler.surplus","retailer.surplus", "retailer.surplus"],
        series_names={
            "smBeergameSD_typical_brewery.surplus" : "Brewery",
            "smBeergameSD_typical_distributor.surplus" : "Distributor",
            "smBeergameSD_typical_wholesaler.surplus": "Wholesaler",
            "smBeergameSD_typical_retailer.surplus": "Retailer"
        }, format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smBeergameSD"],
        kind="area",
        scenarios=["ignoreBackorders"],
        title="Ignoring Backorders – Retailer Order Behaviour",
        x_label="Weeks",
        y_label="Beer Units",
        equations=["retailer.incomingOrder","retailer.inventory","retailer.orderDecision"],
        series_names={
            "smBeergameSD_ignoreBackorders_retailer.incomingOrder" : "Incoming Order",
            "smBeergameSD_ignoreBackorders_retailer.inventory": "Inventory",
            "smBeergameSD_ignoreBackorders_retailer.orderDecision": "Order Decision"
        }, format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smBeergameSD"],
        kind="area",
        scenarios=["ignoreBackorders"],
        title="Ignoring Backorders – Retailer Cost",
        x_label="Weeks",
        y_label="USD",
        equations=["performanceControlling.retailerCostAcc","policySettings.targetRetailerCost"],
        series_names={
            "smBeergameSD_ignoreBackorders_performanceControlling.retailerCostAcc" : "Accumlated Retailer Cost",
            "smBeergameSD_ignoreBackorders_policySettings.targetRetailerCost": "Target Retailer Cost"
        }, format="axes"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    So let’ s see what happens when the ordering policy takes open orders in to account.
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smBeergameSD"],
        kind="area",
        scenarios=["includeSupplyLine"],
        title="Remember Open Orders – Retailer Order Behaviour",
        x_label="Weeks",
        y_label="Beer Units",
        equations=["retailer.incomingOrder","retailer.inventory","retailer.orderDecision"],
        series_names={
            "smBeergameSD_includeSupplyLine_retailer.incomingOrder" : "Consumer Order",
            "smBeergameSD_includeSupplyLine_retailer.inventory": "Retailer Inventory",
            "smBeergameSD_includeSupplyLine_retailer.orderDecision": "Retailer Order",
        
        }, format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smBeergameSD"],
        kind="area",
        scenarios=["includeSupplyLine"],
        title="Remember Open Orders – Retailer Cost",
        x_label="Weeks",
        y_label="USD",
        equations=["performanceControlling.retailerCostAcc","policySettings.targetRetailerCost"],
        series_names={
            "smBeergameSD_includeSupplyLine_performanceControlling.retailerCostAcc" : "Accumlated Retailer Cost",
            "smBeergameSD_includeSupplyLine_policySettings.targetRetailerCost": "Target Retailer Cost"
        }, format="axes"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Our surplus is also looking good, we easily reach the surplus target:
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smBeergameSD"],
        kind="area",
        scenarios=["includeSupplyLine"],
        title="Remember Open Orders – Retailer Surplus",
        x_label="Weeks",
        y_label="USD",
        equations=["retailer.surplus","policySettings.targetSurplus"],
        series_names={
            "smBeergameSD_includeSupplyLine_retailer.surplus" : "Retailer Surplus",
            "smBeergameSD_includeSupplyLine_policySettings.targetSurplus": "Target Surplus"
        }, format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smBeergameSD"],
        kind="area",
        scenarios=["includeSupplyLine"],
        title="Remember Open Orders – Order Behaviour",
        x_label="Weeks",
        y_label="Beer Ordered",
        equations=["brewery.actualProduction","distributor.actualOrder","wholesaler.actualOrder","retailer.actualOrder", "retailer.incomingOrder"],
        series_names={
            "smBeergameSD_includeSupplyLine_brewery.actualProduction" : "Brewery",
            "smBeergameSD_includeSupplyLine_distributor.actualOrder" : "Distributor",
            "smBeergameSD_includeSupplyLine_wholesaler.actualOrder": "Wholesaler",
            "smBeergameSD_includeSupplyLine_retailer.actualOrder": "Retailer",
            "smBeergameSD_includeSupplyLine_retailer.incomingOrder": "Consumer"
        }, format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smBeergameSD"],
        kind="area",
        scenarios=["includeSupplyLine"],
        title="Remember Open Orders – Supply Chain Cost",
        x_label="Weeks",
        y_label="USD",
        equations=["performanceControlling.supplyChainCostAcc","policySettings.targetSupplyChainCost"],
        series_names={
            "smBeergameSD_includeSupplyLine_performanceControlling.supplyChainCostAcc" : "Accumlated Supply Chain Cost",
            "smBeergameSD_includeSupplyLine_policySettings.targetSupplyChainCost": "Target Supply Chain Cost"
        }, format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smBeergameSD"],
        kind="area",
        scenarios=["inventoryAdjustmentTime8"],
        title="Order Behaviour – 8 Weeks Inventory Adjustment Time",
        x_label="Weeks",
        y_label="Beer Ordered",
        equations=["brewery.actualProduction","distributor.actualOrder","wholesaler.actualOrder","retailer.actualOrder", "retailer.incomingOrder"],
        series_names={
            "smBeergameSD_inventoryAdjustmentTime8_brewery.actualProduction" : "Brewery",
            "smBeergameSD_inventoryAdjustmentTime8_distributor.actualOrder" : "Distributor",
            "smBeergameSD_inventoryAdjustmentTime8_wholesaler.actualOrder": "Wholesaler",
            "smBeergameSD_inventoryAdjustmentTime8_retailer.actualOrder": "Retailer",
            "smBeergameSD_inventoryAdjustmentTime8_retailer.incomingOrder": "Consumer"
        }, format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smBeergameSD"],
        kind="area",
        scenarios=["inventoryAdjustmentTime8"],
        title="Supply Chain Cost – 8 Weeks Inventory Adjustment Time",
        x_label="Weeks",
        y_label="USD",
        equations=["performanceControlling.supplyChainCostAcc","policySettings.targetSupplyChainCost"],
        series_names={
            "smBeergameSD_inventoryAdjustmentTime8_performanceControlling.supplyChainCostAcc" : "Accumlated Supply Chain Cost",
            "smBeergameSD_inventoryAdjustmentTime8_policySettings.targetSupplyChainCost": "Target Supply Chain Cost"
        }, format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smBeergameSD"],
        kind="area",
        scenarios=["inventoryAdjustmentTime8"],
        title="Retailer Cost – 8 Weeks Inventory Adjustment Time",
        x_label="Weeks",
        y_label="USD",
        equations=["performanceControlling.retailerCostAcc","policySettings.targetRetailerCost"],
        series_names={
            "smBeergameSD_inventoryAdjustmentTime8_performanceControlling.retailerCostAcc" : "Accumlated Retailer Cost",
            "smBeergameSD_inventoryAdjustmentTime8_policySettings.targetRetailerCost": "Target Retailer Cost"
        }, format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smBeergameSD"],
        kind="area",
        scenarios=["inventoryAdjustmentTime8"],
        title="Retailer Surplus – 8 Weeks Inventory Adjustment Time",
        x_label="Weeks",
        y_label="USD",
        equations=["retailer.surplus","policySettings.targetSurplus"],
        series_names={
            "smBeergameSD_inventoryAdjustmentTime8_retailer.surplus":"Surplus",
            "smBeergameSD_inventoryAdjustmentTime8_policySettings.targetSurplus":"Target Surplus"
        }, format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smBeergameSD"],
        kind="area",
        scenarios=["inventoryAdjustmentTime2","inventoryAdjustmentTime8","inventoryAdjustmentTime16"],
        title="Retailer Surplus",
        x_label="Weeks",
        y_label="USD",
        equations=["retailer.surplus"],
        series_names={
            "smBeergameSD_inventoryAdjustmentTime2_retailer.surplus":"Inventory Adjustment Time 2",
         "smBeergameSD_inventoryAdjustmentTime8_retailer.surplus":"Inventory Adjustment Time 8",
             "smBeergameSD_inventoryAdjustmentTime16_retailer.surplus":"Inventory Adjustment Time 16",
        }, format="axes"
    
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smBeergameSD"],
        kind="area",
        scenarios=["inventoryAdjustmentTime2","inventoryAdjustmentTime8","inventoryAdjustmentTime16"],
        title="Supply Chain Cost",
        x_label="Weeks",
        y_label="USD",
        equations=["performanceControlling.supplyChainCostAcc"],
        series_names={
            "smBeergameSD_inventoryAdjustmentTime2_performanceControlling.supplyChainCostAcc":"Inventory Adjustment Time 2",
         "smBeergameSD_inventoryAdjustmentTime8_performanceControlling.supplyChainCostAcc":"Inventory Adjustment Time 8",
             "smBeergameSD_inventoryAdjustmentTime16_performanceControlling.supplyChainCostAcc":"Inventory Adjustment Time 16",
        }, format="axes"
    )
    return


@app.cell
def _():
    # magic command not supported in marimo; please file an issue to add support
    # %run src/dashboard/beergame_dashboard_xmile.ipy
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Our analysis of the supply chain also points to further improvement potential – the way the supply chain in the Beer Game is structured, each player only communicates orders to his immediate supplier in the chain, therefore it takes quite a long time to react to changes in customer demand.

    Surely we could improve the performance of the supply chain, if the consumers demand for beer were communicated to all players in the chain directly?

    So instead of just taking a local view of each players behavior we could take a global view of the entire supply chain; instead of just improving each players ordering policy we should change the architecture of the entire supply chain.

    Needless to say that this is what actually happened in the “real world”, we just need to look at just-in-time production and lean manufacturing (and let’s not forget that the beer game was developed in the 1950s, before these revolutions took place).

    Though these ideas are very exciting, I feel we have achieved enough for now and will therefore leave a detailed investigation of these ideas to a future post.
    """)
    return


if __name__ == "__main__":
    app.run()
