# Front matter the .py format cannot carry; injected on export.
# description: A small System Dynamics model of two competitors setting prices against each other.
# keywords: system dynamics, systemdynamics, pricing, competition, bptk, bptk-py, python, business simulation
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Competitive Pricing Dynamics")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Competitive Pricing Model
    """)
    return


@app.cell
def _():
    from BPTK_Py import Model
    from BPTK_Py import sd_functions as sd

    return Model, sd


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We create our model using the `Model` class as follows:
    """)
    return


@app.cell
def _(Model):
    model = Model(starttime=0.0,stoptime=2.0,dt=0.25,name='CompetitvePricing')
    return (model,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The stock and flow model consists of six parts:

    - Production and inventory
    - Demand formation
    - Price adjustment
    - Profit
    - Perceived Inventory
    - Expected Profitability

    The following sections explain each part in more detail. Furthermore, they demonstrate the composition of stocks, flows, converters and constants.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Creating model
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 1) Production and Inventory
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    <div align="center"><img src="images/competitive_pricing_model_1.svg" width="90%"></div>
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Stocks:** production capacity, production, inventory
    """)
    return


@app.cell
def _(model):
    productionCapacity = model.stock("productionCapacity")
    production = model.stock("production")
    inventory = model.stock("inventory")
    return inventory, production, productionCapacity


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Flows:** production start rate, production rate, consumption rate
    """)
    return


@app.cell
def _(model):
    productionStartRate = model.flow("productionStartRate")
    productionRate = model.flow("productionRate")
    consumptionRate = model.flow("consumptionRate")
    return consumptionRate, productionRate, productionStartRate


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Converters:** effect of profitability on capacity utilization,capacity utilization, inventory coverage
    """)
    return


@app.cell
def _(model):
    capacityUtilization = model.converter("capacityUtilization")
    effectOfProfitabilityOnCapacityUtilization = model.converter("effectOfProfitabilityOnCapacityUtilization")
    inventoryCoverage = model.converter("inventoryCoverage")
    return (
        capacityUtilization,
        effectOfProfitabilityOnCapacityUtilization,
        inventoryCoverage,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Constants:** production time
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    *Normalized expected profitability and demand are not constants. They are results of other parts.*
    """)
    return


@app.cell
def _(model):
    productionTime = model.constant("productionTime")
    return (productionTime,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 2) Demand formation
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    <div align="center"><img src="images/competitive_pricing_model_4.svg" width="90%"></div>
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    *This model does not have any stocks or flows.*
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Converters:** relative value of product, effect of relative value on demand, reference demand, demand
    """)
    return


@app.cell
def _(model):
    relativeValueOfProduct = model.converter("relativeValueOfProduct")
    effectOfRelativeValueOnDemand = model.converter("effectOfRelativeValueOnDemand")
    referenceDemand = model.converter("referenceDemand")
    demand = model.converter("demand")
    return (
        demand,
        effectOfRelativeValueOnDemand,
        referenceDemand,
        relativeValueOfProduct,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Constants:** price of substitutes, size of shock, market shock on
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    *Price is not a constant. It is a result of another part.*
    """)
    return


@app.cell
def _(model):
    sizeOfShock = model.constant("sizeOfShock")
    marketShockOn = model.constant("marketShockOn")
    priceOfSubstitutes = model.constant("priceOfSubstitutes")
    return marketShockOn, priceOfSubstitutes, sizeOfShock


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 3) Price Adjustment
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This section contains two models. The first model determines the minimum price. The second describes the formation of the product's price.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    <div align="center"><img src="images/competitive_pricing_model_7.svg" width="90%"></div>
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    *This model does not have any stocks, flows or constants. Unit variable cost and unit capacity cost are results of other parts.*
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Converters:** capacity cost per unit, minimum price
    """)
    return


@app.cell
def _(model):
    minimumPrice = model.converter("minimumPrice")
    capacityCostPerUnit = model.converter("capacityCostPerUnit")
    return capacityCostPerUnit, minimumPrice


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    <div align="center"><img src="images/competitive_pricing_model_2.svg" width="90%"></div>
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Stocks:** expected price
    """)
    return


@app.cell
def _(model):
    expectedPrice = model.stock("expectedPrice")
    return (expectedPrice,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Flows:** change in expected price
    """)
    return


@app.cell
def _(model):
    changeInExpectedPrice = model.flow("changeInExpectedPrice")
    return (changeInExpectedPrice,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Converters:** indicated price, effect of inventory coverage on price, price
    """)
    return


@app.cell
def _(model):
    indicatedPrice = model.converter("indicatedPrice")
    effectOfInventoryCoverageOnPrice = model.converter("effectOfInventoryCoverageOnPrice")
    price = model.converter("price")
    return effectOfInventoryCoverageOnPrice, indicatedPrice, price


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Constants:**
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    *Minimum price and normalized inventory coverage are not constants. Minimum price is a result of the previous model and normalized inventory coverage is a result of another part.*
    """)
    return


@app.cell
def _(model):
    priceAdjustmentTime = model.constant("priceAdjustmentTime")
    return (priceAdjustmentTime,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 4) Profit
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    <div align="center"><img src="images/competitive_pricing_model_6.svg" width="90%"></div>
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    *This model has no stocks and flows. Production capacity is not a stock of this part. It is a result of the "Production and Inventory" part from the beginning.*
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Converters:** capacity cost, variable cost, cost, revenue, profit
    """)
    return


@app.cell
def _(model):
    capacityCost = model.converter("capacityCost")
    variableCost = model.converter("variableCost")
    cost = model.converter("cost")
    revenue = model.converter("revenue")
    profit = model.converter("profit")
    return capacityCost, cost, profit, revenue, variableCost


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Constants:** unit capacity cost, unit variable cost
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    *Production rate, price and consumption rate are not constants of this model. They are results of other parts. Production rate and consumption rate are converters of the "Production and Inventory" model. Price is a converter of the "Price Adjustment" part.*
    """)
    return


@app.cell
def _(model):
    unitCapacityCost = model.constant("unitCapacityCost")
    unitVariableCost = model.constant("unitVariableCost")
    return unitCapacityCost, unitVariableCost


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 5) Perceived Inventory
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ![Commodity Pricing Dynamics](images/competitive_pricing_model_3.svg)
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Stocks:** perceived inventory coverage
    """)
    return


@app.cell
def _(model):
    perceivedInventoryCoverage = model.stock("perceivedInventoryCoverage")
    return (perceivedInventoryCoverage,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Flows:** change in perceived inventory coverage
    """)
    return


@app.cell
def _(model):
    changeInPerceivedInventoryCoverage = model.flow("changeInPerceivedInventoryCoverage")
    return (changeInPerceivedInventoryCoverage,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Converters:** normalized perceived inventory coverage
    """)
    return


@app.cell
def _(model):
    normalizedPerceivedInventoryCoverage = model.converter("normalizedPerceivedInventoryCoverage")
    return (normalizedPerceivedInventoryCoverage,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Constants:** inventory coverage perception time, reference inventory coverage
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    *Inventory coverage is not a constant of this part. It is a converter and a result of the "Production and Inventory" model.*
    """)
    return


@app.cell
def _(model):
    referenceInventoryCoverage = model.constant("referenceInventoryCoverage")
    inventoryCoveragePerceptionTime = model.constant("inventoryCoveragePerceptionTime")
    return inventoryCoveragePerceptionTime, referenceInventoryCoverage


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 6) Expected Profitability
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    <div align="center"><img src="images/competitive_pricing_model_5.svg" width="90%"></div>
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Stocks:** expected profitability
    """)
    return


@app.cell
def _(model):
    expectedProfitability = model.stock("expectedProfitability")
    return (expectedProfitability,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Flows:** change in expected profitability
    """)
    return


@app.cell
def _(model):
    changeInExpectedProfitability = model.flow("changeInExpectedProfitability")
    return (changeInExpectedProfitability,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Converters:** normalized expected profitability
    """)
    return


@app.cell
def _(model):
    normalizedExpectedProfitability = model.converter("normalizedExpectedProfitability")
    return (normalizedExpectedProfitability,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Constants:** profit adjustment time, reference expected profitability
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    *Profit is not a constant of this part. It is a result of the "Profit" model.*
    """)
    return


@app.cell
def _(model):
    referenceExpectedProfitability = model.constant("referenceExpectedProfitability")
    profitAdjustmentTime = model.constant("profitAdjustmentTime")
    return profitAdjustmentTime, referenceExpectedProfitability


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Initializing the stocks
    """)
    return


@app.cell
def _(
    expectedPrice,
    expectedProfitability,
    inventory,
    perceivedInventoryCoverage,
    production,
    productionCapacity,
):
    productionCapacity.initial_value = 200.0
    production.initial_value = 300.0
    inventory.initial_value = 300.0
    expectedPrice.initial_value = 3.0
    perceivedInventoryCoverage.initial_value = 3.0
    expectedProfitability.initial_value = 100.0
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Defining Equations
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Production and Inventory
    """)
    return


@app.cell
def _(capacityUtilization, consumptionRate, demand, effectOfProfitabilityOnCapacityUtilization, inventory, inventoryCoverage, model, normalizedExpectedProfitability, production, productionCapacity, productionRate, productionStartRate, productionTime, sd):
    productionTime.equation = 3.0
    effectOfProfitabilityOnCapacityUtilization.equation = sd.lookup(normalizedExpectedProfitability,"effectOfProfitabilityOnCapacityUtilization")
    capacityUtilization.equation = effectOfProfitabilityOnCapacityUtilization
    productionStartRate.equation = capacityUtilization*productionCapacity
    productionRate.equation = sd.min(production, sd.delay(model, productionStartRate, productionTime, 100.0))
    consumptionRate.equation = sd.min(inventory,demand)
    inventoryCoverage.equation = inventory/consumptionRate
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The stocks production and inventory have inflows and outflows.
    """)
    return


@app.cell
def _(
    consumptionRate,
    inventory,
    production,
    productionRate,
    productionStartRate,
):
    production.equation = productionStartRate - productionRate
    inventory.equation = productionRate - consumptionRate
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We define the effect of profitability on capacity utilzation in our model using a non-linear relationship (depending on the normalized expected profitability). We capture this relationship in a lookup table that we store in the `points` property of the model (using a Python list):
    """)
    return


@app.cell
def _(model):
    model.points["effectOfProfitabilityOnCapacityUtilization"] = [
        [0.0,0.324],
        [0.167,0.33],
        [0.333,0.372],
        [0.5,0.394],
        [0.667,0.41],
        [0.833,0.42],
        [1.0,0.5],
        [1.167,0.745],
        [1.333,0.80075],
        [1.5,0.8565],
        [1.667,0.91225],
        [1.833,0.968],
        [2.0,0.968]
    ]
    model.plot_lookup("effectOfProfitabilityOnCapacityUtilization", format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Demand Formation
    """)
    return


@app.cell
def _(demand, effectOfRelativeValueOnDemand, marketShockOn, model, price, priceOfSubstitutes, referenceDemand, relativeValueOfProduct, sd, sizeOfShock):
    sizeOfShock.equation = 50.0
    marketShockOn.equation = 0.0
    priceOfSubstitutes.equation = 3.0
    relativeValueOfProduct.equation = priceOfSubstitutes/price
    effectOfRelativeValueOnDemand.equation = sd.lookup(relativeValueOfProduct,"effectOfRelativeValueOnDemand")
    referenceDemand.equation = 100+marketShockOn*sd.step(sizeOfShock,10.0)
    demand.equation = effectOfRelativeValueOnDemand*referenceDemand
    model.points["effectOfRelativeValueOnDemand"] = [
        [0.0,0.17],
        [0.167,0.191],
        [0.333,0.213],
        [0.5,0.277],
        [0.667,0.351],
        [0.833,0.479],
        [1.0,1.0],
        [1.167,1.362],
        [1.333,1.479],
        [1.5,1.574],
        [1.667,1.638],
        [1.833,1.66],
        [2.0,1.66]
    ]
    model.plot_lookup("effectOfRelativeValueOnDemand", format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Price Adjustment
    """)
    return


@app.cell
def _(capacityCost, capacityCostPerUnit, changeInExpectedPrice, effectOfInventoryCoverageOnPrice, expectedPrice, indicatedPrice, minimumPrice, model, normalizedPerceivedInventoryCoverage, price, priceAdjustmentTime, productionRate, sd, unitVariableCost):
    priceAdjustmentTime.equation = 3.0
    capacityCostPerUnit.equation = capacityCost/productionRate
    minimumPrice.equation = unitVariableCost+capacityCostPerUnit
    effectOfInventoryCoverageOnPrice.equation = sd.lookup(normalizedPerceivedInventoryCoverage,"effectOfInventoryCoverageOnPrice")
    price.equation = expectedPrice/effectOfInventoryCoverageOnPrice
    indicatedPrice.equation = sd.max(price, minimumPrice)
    changeInExpectedPrice.equation = (indicatedPrice-expectedPrice)/priceAdjustmentTime
    # And the stock integrates that flow. Without this line the flow is computed and
    # never applied: the expected price stays at its initial 3.0 for the whole run and
    # the price adjustment loop - the subject of this section - does nothing.
    expectedPrice.equation = changeInExpectedPrice
    model.points["effectOfInventoryCoverageOnPrice"] = [
        [0.0,1.404],
        [0.167,1.415],
        [0.333,1.404],
        [0.5,1.372],
        [0.667,1.351],
        [0.833,1.277],
        [1.0,1.0],
        [1.167,0.787],
        [1.333,0.550],
        [1.5,0.4],
        [1.667,0.34],
        [1.833,0.298],
        [2.0,0.298]
    ]
    model.plot_lookup("effectOfInventoryCoverageOnPrice", format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Profit
    """)
    return


@app.cell
def _(capacityCost, consumptionRate, cost, price, productionCapacity, productionRate, profit, revenue, unitCapacityCost, unitVariableCost, variableCost):
    unitCapacityCost.equation = 0.5
    unitVariableCost.equation = 1.0
    capacityCost.equation = unitCapacityCost*productionCapacity
    variableCost.equation = unitVariableCost*productionRate
    cost.equation = variableCost + capacityCost
    revenue.equation = price * consumptionRate
    profit.equation = revenue - cost
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Perceived Inventory Coverage
    """)
    return


@app.cell
def _(changeInPerceivedInventoryCoverage, inventoryCoverage, inventoryCoveragePerceptionTime, normalizedPerceivedInventoryCoverage, perceivedInventoryCoverage, referenceInventoryCoverage):
    referenceInventoryCoverage.equation = 3.0
    inventoryCoveragePerceptionTime.equation = 3.0
    changeInPerceivedInventoryCoverage.equation = (inventoryCoverage-perceivedInventoryCoverage)/inventoryCoveragePerceptionTime
    normalizedPerceivedInventoryCoverage.equation = perceivedInventoryCoverage/referenceInventoryCoverage
    perceivedInventoryCoverage.equation = changeInPerceivedInventoryCoverage
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Expected Profitability
    """)
    return


@app.cell
def _(changeInExpectedProfitability, expectedProfitability, normalizedExpectedProfitability, profit, profitAdjustmentTime, referenceExpectedProfitability):
    referenceExpectedProfitability.equation = 100.0
    profitAdjustmentTime.equation = 12.0
    changeInExpectedProfitability.equation = (profit-expectedProfitability)/profitAdjustmentTime
    expectedProfitability.equation = changeInExpectedProfitability
    normalizedExpectedProfitability.equation = expectedProfitability/referenceExpectedProfitability
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Scenario Management
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We now use the scenario management of the BPTK-Py framework. We first import the library.
    """)
    return


@app.cell
def _():
    import BPTK_Py
    bptk = BPTK_Py.bptk()
    return (bptk,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Then we set up a scenario manager using a Python dictionary. The scenario manager identifies the baseline constants of the model:
    """)
    return


@app.cell
def _(model):
    scenario_manager = {
        "smCompetitivePricing":{
    
        "model": model,
        "base_constants": {
            "marketShockOn":0,
            "sizeOfShock":50

        },
       "base_points":{
                "effectOfProfitabilityOnCapacityUtilization":
                [
                    [0.0, 0.324],
                    [0.16666666666666666, 0.33],
                    [0.3333333333333333, 0.372],
                    [0.5, 0.394],
                    [0.6666666666666666, 0.41],
                    [0.8333333333333334, 0.42],
                    [1.0, 0.5],
                    [1.1666666666666667, 0.745],
                    [1.3333333333333333, 0.80075],
                    [1.5, 0.8565],
                    [1.6666666666666667, 0.91225],
                    [1.8333333333333333, 0.968],
                    [2.0, 0.968]
                ],
                "effectOfRelativeValueOnDemand" :
                   [
                       [0.0, 0.17],
                       [0.16666666666666666, 0.191],
                       [0.3333333333333333, 0.213],
                       [0.5, 0.277],
                       [0.6666666666666666, 0.351],
                       [0.8333333333333334, 0.479],
                       [1.0, 1.0],
                       [1.1666666666666667, 1.362],
                       [1.3333333333333333, 1.479],
                       [1.5, 1.574],
                       [1.6666666666666667, 1.638],
                       [1.8333333333333333, 1.66],
                       [2.0, 1.66]
                   ] 
                ,
                 "effectOfInventoryCoverageOnPrice" :  
                      [
                          [0.0, 1.404],
                          [0.16666666666666666, 1.415],
                          [0.3333333333333333, 1.404],
                          [0.5, 1.372],
                          [0.6666666666666666, 1.351],
                          [0.8333333333333334, 1.277],
                          [1.0, 1.0],
                          [1.1666666666666667, 0.787],
                          [1.3333333333333333, 0.55],
                          [1.5, 0.4],
                          [1.6666666666666667, 0.34],
                          [1.8333333333333333, 0.298],
                          [2.0, 0.298]
                      ] 
            },
            "scenarios":{
                 "base":{
                  }    
            }
        
     }
    }
    return (scenario_manager,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The next step is to register the scenario manager as follows:
    """)
    return


@app.cell
def _(bptk, scenario_manager):
    # Registering a manager whose name already exists leaves the *old* model in place -
    # `register_scenario_manager` warns and keeps it. Dropping the registry first is what
    # lets an edit anywhere in the model above reach the sixteen charts below.
    bptk.reset_all_scenarios()
    bptk.register_scenario_manager(scenario_manager)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Once we have this, we can define and register more scenarios as follows:
    """)
    return


@app.cell
def _(bptk):
    bptk.register_scenarios(
        scenarios =
            {
                 "marketShock":{
                    "constants":{
                        "marketShockOn":1
                    }
                },
                  "availabilityLoop":{
                   "constants":{
                        "marketShockOn":1
                    },
                   "points":{
                          "effectOfProfitabilityOnCapacityUtilization" : 
                           [
                               [0.0, 0.5],
                               [0.16666666666666666, 0.5],
                               [0.3333333333333333, 0.5],
                               [0.5, 0.5],
                               [0.6666666666666666, 0.5],
                               [0.8333333333333334, 0.5],
                               [1.0, 0.5],
                               [1.1666666666666667, 0.5],
                               [1.3333333333333333, 0.5],
                               [1.5, 0.5],
                               [1.6666666666666667, 0.5],
                               [1.8333333333333333, 0.5],
                               [2.0, 0.5]
                           ],
                        "effectOfRelativeValueOnDemand" :
                        [
                            [0.0, 1.0],
                            [0.16666666666666666,1.0],
                            [0.3333333333333333, 1.0],
                            [0.5, 1.0],
                            [0.6666666666666666, 1.0],
                            [0.8333333333333334, 1.0],
                            [1.0, 1.0],
                            [1.1666666666666667, 1.0],
                            [1.3333333333333333,1.0],
                            [1.5, 1.0],
                            [1.6666666666666667,1.0],
                            [1.8333333333333333, 1.0],
                            [2.0, 1.0]
                        ],
                         "effectOfInventoryCoverageOnPrice" :  
                            [
                                [0.0, 1.0],
                                [0.16666666666666666, 1.0],
                                [0.3333333333333333, 1.0],
                                [0.5, 1.0],
                                [0.6666666666666666, 1.0],
                                [0.8333333333333334, 1.0],
                                [1.0, 1.0],
                                [1.1666666666666667, 1.0],
                                [1.3333333333333333, 1.0],
                                [1.5, 1.0],
                                [1.6666666666666667, 1.0],
                                [1.8333333333333333, 1.0],
                                [2.0, 1.0]
                            ] 
                   }
               
               },
               "capacityUtilizationLoop":{
                   "constants":{
                        "marketShockOn":1
                    },
                   "points":{
                      
                        "effectOfRelativeValueOnDemand" :
                        [
                            [0.0, 1.0],
                            [0.16666666666666666,1.0],
                            [0.3333333333333333, 1.0],
                            [0.5, 1.0],
                            [0.6666666666666666, 1.0],
                            [0.8333333333333334, 1.0],
                            [1.0, 1.0],
                            [1.1666666666666667, 1.0],
                            [1.3333333333333333,1.0],
                            [1.5, 1.0],
                            [1.6666666666666667,1.0],
                            [1.8333333333333333, 1.0],
                            [2.0, 1.0]
                        ]
               
               }
               },
                 "substitutionLoop":{
                   "constants":{
                        "marketShockOn":1
                    },
                   "points":{
                          "effectOfProfitabilityOnCapacityUtilization" : 
                           [
                               [0.0, 0.5],
                               [0.16666666666666666, 0.5],
                               [0.3333333333333333, 0.5],
                               [0.5, 0.5],
                               [0.6666666666666666, 0.5],
                               [0.8333333333333334, 0.5],
                               [1.0, 0.5],
                               [1.1666666666666667, 0.5],
                               [1.3333333333333333, 0.5],
                               [1.5, 0.5],
                               [1.6666666666666667, 0.5],
                               [1.8333333333333333, 0.5],
                               [2.0, 0.5]
                           ]
                   }
               
               }
            }
        ,
        scenario_manager="smCompetitivePricing")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Using the `plot_lookup` function on the bptk class, we can compare the lookup functions between different scenarios.
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_lookup(
        scenario_managers=["smCompetitivePricing"],
        lookup_names=["effectOfProfitabilityOnCapacityUtilization"],
        scenarios=["base","availabilityLoop"], format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Scenario Experiments
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Base Case
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Let's quickly run through the base case first, which starts the model in equilibrium.

    The equilibrium price for our product is set at EUR 3. This is equal to both the indicated price  and the expected price. The minimum price (the amount we need to be profitable) is at EUR 1.5
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
                scenario_managers=["smCompetitivePricing"],
                scenarios=["base"], 
                equations=["minimumPrice","price","indicatedPrice","expectedPrice"], format="axes"
                )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Initially there is a reference demand of 100 units per month. Because the market is in equilibrium, the reference demand (i.e. the demand given the equilibrium price) equals the actual demand.
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
                scenario_managers=["smCompetitivePricing"],
                scenarios=["base"], 
                equations=["demand","referenceDemand"], format="axes"
                )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Our production capacity is 200 units per month - but we only produce 100 units per month to avoid overstocking and are thus at a utilization of 50%. 300 units are "work in progress" within production.
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
                scenario_managers=["smCompetitivePricing"],
                scenarios=["base"], 
                equations=["productionCapacity","productionRate","production"], format="axes"
                )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Capacity utilization is thus at 50%.
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
                scenario_managers=["smCompetitivePricing"],
                scenarios=["base"], 
                equations=["capacityUtilization"], format="axes"
                )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The inventory is also at 300 and the consumption rate equals the demand, i.e. is at 100.
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
                scenario_managers=["smCompetitivePricing"],
                scenarios=["base"], 
                equations=["inventory","consumptionRate"], format="axes"
                )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This leads to an inventory coverage of 3.
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
                scenario_managers=["smCompetitivePricing"],
                scenarios=["base"], 
                equations=["inventoryCoverage"], format="axes"
                )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Market Shock
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Let's investigate what happens if there is a sudden increase in the underlying demand of 50% at timestep 10. Note that the increase in demand is _at the current level of pricing_.
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
                scenario_managers=["smCompetitivePricing"],
                scenarios=["marketShock"], 
                equations=["referenceDemand"], format="axes"
                )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The graph below shows how the actual demand and the inventory develops - as expected, there is an inital demand peak. But this causes the inventory to drop, which increases the price. The increase price leads to increased production, which then lowers the price and thus increases demand.
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
                scenario_managers=["smCompetitivePricing"],
                scenarios=["marketShock"], 
                equations=["demand", "inventory"], format="axes"
                )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This is because the actual price affects the demand - if the price is higher then the reference price, demand drops, if the price is lower, demand increases compared to the reference demand.

    The plot below shows how the dependency is quantified in this model using a non-linear function - the exact shape of this function will depend on your specific situation.
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_lookup(
                scenario_managers=["smCompetitivePricing"],
                scenarios=["base"],
                lookup_names=["effectOfRelativeValueOnDemand"], format="axes"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We also assume that prices are sensitive to the availability of the product. If the product becomes scare (i.e. the inventory coverage falls), prices go up, and vice versa. The dependency is modelled using the following table function:
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_lookup(
                scenario_managers=["smCompetitivePricing"],
                scenarios=["base"],
                lookup_names=["effectOfInventoryCoverageOnPrice"], format="axes"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The production rate increases to a new, much higher level.
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
                scenario_managers=["smCompetitivePricing"],
                scenarios=["marketShock"], 
                equations=['productionRate'], format="axes"
                )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The price increases initially, because of the drop in inventory coverage. But the inventory coverage quickly recoveres due to increase production. Because inventory coverage influences the price, this leads to a price that is actually lower than the original price, but also to a demand that is higher than that indicated by the initial market shock.
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
                scenario_managers=["smCompetitivePricing"],
                scenarios=["marketShock"], 
                equations=['price','inventoryCoverage'], format="axes"
                )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    even though the overall demand incrase is only at around 75%, our profits more than double, as seen in the graph below.
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
                scenario_managers=["smCompetitivePricing"],
                scenarios=["base","marketShock"], 
                equations=['profit'], format="axes"
                )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This is because we are utilizing our production capacity better: we go from a utilization of 50% to a utilization above 90%, as seen in the graph below.
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
                scenario_managers=["smCompetitivePricing"],
                scenarios=["base","marketShock"], 
                equations=['capacityUtilization'], format="axes"
                )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The figures above show that with the given shock of a 50% increase in underlying demand, we get close to our capacity limits.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Try It Yourself

    The scenarios above are fixed: a base case and a 50 % demand shock. The cell below
    registers one more that is yours to change. Two constants are the interesting ones -
    `sizeOfShock` is the size of the demand jump in percent, and `marketShockOn` switches it
    on at all - and the chart underneath compares your scenario against the base case.

    Change a number, press play, and the chart redraws. A shock of 20 rather than 50 is a
    good first move: does the profit still more than double?
    """)
    return


@app.cell
def _(bptk):
    # `register_scenarios` returns nothing, so the name below is what gives the chart a
    # dependency on this cell. Without it marimo would see no reason to redraw.
    bptk.register_scenarios(
        scenarios={
            "myShock": {
                "constants": {
                    "marketShockOn": 1,
                    "sizeOfShock": 20,
                }
            }
        },
        scenario_manager="smCompetitivePricing",
    )
    my_scenario = "myShock"
    return (my_scenario,)


@app.cell
def _(bptk, my_scenario):
    bptk.plot_scenarios(
        scenario_managers=["smCompetitivePricing"],
        scenarios=["base", my_scenario],
        equations=["profit"],
        title="Profit: base case against your own shock",
        format="axes",
    )
    return


if __name__ == "__main__":
    app.run()
