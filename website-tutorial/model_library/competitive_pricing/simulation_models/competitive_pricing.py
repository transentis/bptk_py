"""competitive_pricing - generated from XMILE by the BPTK-Py compiler, target py-sddsl."""

from BPTK_Py import Model
from BPTK_Py import sd_functions as sd


class CompetitivePricing(Model):

    def __init__(self):
        super().__init__(starttime=1.0, stoptime=61.0, dt=0.25, name='competitive_pricing')

        # ── Defining the elements ────────────────────────────────────────────

        # Stocks
        expectedPrice = self.stock('expectedPrice')
        expectedProfitability = self.stock('expectedProfitability')
        inventory = self.stock('inventory')
        perceivedInventoryCoverage = self.stock('perceivedInventoryCoverage')
        production = self.stock('production')
        productionCapacity = self.stock('productionCapacity')

        # Flows
        consumptionRate = self.flow('consumptionRate')
        productionRate = self.flow('productionRate')
        productionStartRate = self.flow('productionStartRate')

        # Biflows
        changeInExpectedPrice = self.biflow('changeInExpectedPrice')
        changeInExpectedProfitability = self.biflow('changeInExpectedProfitability')
        changeInPerceivedInventoryCoverage = self.biflow('changeInPerceivedInventoryCoverage')

        # Converters
        capacityCost = self.converter('capacityCost')
        capacityCostPerUnit = self.converter('capacityCostPerUnit')
        capacityUtilization = self.converter('capacityUtilization')
        cost = self.converter('cost')
        demand = self.converter('demand')
        effectOfInventoryCoverageOnPrice = self.converter('effectOfInventoryCoverageOnPrice')
        effectOfProfitabilityOnCapacityUtilization = self.converter('effectOfProfitabilityOnCapacityUtilization')
        effectOfRelativeValueOnDemand = self.converter('effectOfRelativeValueOnDemand')
        indicatedPrice = self.converter('indicatedPrice')
        inventoryCoverage = self.converter('inventoryCoverage')
        minimumPrice = self.converter('minimumPrice')
        normalizedExpectedProfitability = self.converter('normalizedExpectedProfitability')
        normalizedPerceiedInventoryCoverage = self.converter('normalizedPerceiedInventoryCoverage')
        price = self.converter('price')
        profit = self.converter('profit')
        referenceDemand = self.converter('referenceDemand')
        relativeValueOfProduct = self.converter('relativeValueOfProduct')
        revenue = self.converter('revenue')
        variableCost = self.converter('variableCost')

        # Constants
        inventoryCoveragePerceptionTime = self.constant('inventoryCoveragePerceptionTime')
        marketShockOn = self.constant('marketShockOn')
        priceAdjustmentTime = self.constant('priceAdjustmentTime')
        priceOfSubstitutes = self.constant('priceOfSubstitutes')
        productionTime = self.constant('productionTime')
        profitAdjustmentTime = self.constant('profitAdjustmentTime')
        referenceExpectedProfitability = self.constant('referenceExpectedProfitability')
        referenceInventoryCoverage = self.constant('referenceInventoryCoverage')
        sizeOfShock = self.constant('sizeOfShock')
        unitCapacityCost = self.constant('unitCapacityCost')
        unitVariableCost = self.constant('unitVariableCost')

        # ── Setting the initial values and equations ─────────────────────────

        # Graphical functions
        self.points['effectOfInventoryCoverageOnPrice'] = [[0.0, 1.404], [0.16666666666666666, 1.415], [0.3333333333333333, 1.404], [0.5, 1.372], [0.6666666666666666, 1.351], [0.8333333333333334, 1.277], [1.0, 1.0], [1.1666666666666667, 0.787], [1.3333333333333333, 0.55], [1.5, 0.4], [1.6666666666666667, 0.34], [1.8333333333333333, 0.298], [2.0, 0.298]]
        self.points['effectOfProfitabilityOnCapacityUtilization'] = [[0.0, 0.324], [0.16666666666666666, 0.33], [0.3333333333333333, 0.372], [0.5, 0.394], [0.6666666666666666, 0.41], [0.8333333333333334, 0.42], [1.0, 0.5], [1.1666666666666667, 0.745], [1.3333333333333333, 0.80075], [1.5, 0.8565], [1.6666666666666667, 0.91225], [1.8333333333333333, 0.968], [2.0, 0.968]]
        self.points['effectOfRelativeValueOnDemand'] = [[0.0, 0.17], [0.16666666666666666, 0.191], [0.3333333333333333, 0.213], [0.5, 0.277], [0.6666666666666666, 0.351], [0.8333333333333334, 0.479], [1.0, 1.0], [1.1666666666666667, 1.362], [1.3333333333333333, 1.479], [1.5, 1.574], [1.6666666666666667, 1.638], [1.8333333333333333, 1.66], [2.0, 1.66]]

        # Stocks
        expectedPrice.initial_value = 3.0
        expectedPrice.inflows = [changeInExpectedPrice]
        expectedProfitability.initial_value = 100.0
        expectedProfitability.inflows = [changeInExpectedProfitability]
        inventory.initial_value = 300.0
        inventory.inflows = [productionRate]
        inventory.outflows = [consumptionRate]
        perceivedInventoryCoverage.initial_value = 3.0
        perceivedInventoryCoverage.inflows = [changeInPerceivedInventoryCoverage]
        production.initial_value = 300.0
        production.inflows = [productionStartRate]
        production.outflows = [productionRate]
        productionCapacity.initial_value = 200.0

        # Flows
        consumptionRate.equation = sd.max(0.0, sd.min(inventory, demand))
        productionRate.equation = sd.max(0.0, sd.min(production, sd.delay(self, productionStartRate, productionTime, 100.0)))
        productionStartRate.equation = sd.max(0.0, (capacityUtilization * productionCapacity))

        # Biflows
        changeInExpectedPrice.equation = (((indicatedPrice - expectedPrice)) / priceAdjustmentTime)
        changeInExpectedProfitability.equation = (((profit - expectedProfitability)) / profitAdjustmentTime)
        changeInPerceivedInventoryCoverage.equation = (((inventoryCoverage - perceivedInventoryCoverage)) / inventoryCoveragePerceptionTime)

        # Converters
        capacityCost.equation = (unitCapacityCost * productionCapacity)
        capacityCostPerUnit.equation = (capacityCost / productionRate)
        capacityUtilization.equation = effectOfProfitabilityOnCapacityUtilization
        cost.equation = (variableCost + capacityCost)
        demand.equation = (effectOfRelativeValueOnDemand * referenceDemand)
        effectOfInventoryCoverageOnPrice.equation = sd.lookup(normalizedPerceiedInventoryCoverage, 'effectOfInventoryCoverageOnPrice')
        effectOfProfitabilityOnCapacityUtilization.equation = sd.lookup(normalizedExpectedProfitability, 'effectOfProfitabilityOnCapacityUtilization')
        effectOfRelativeValueOnDemand.equation = sd.lookup(relativeValueOfProduct, 'effectOfRelativeValueOnDemand')
        indicatedPrice.equation = sd.max(price, minimumPrice)
        inventoryCoverage.equation = (inventory / consumptionRate)
        minimumPrice.equation = (unitVariableCost + capacityCostPerUnit)
        normalizedExpectedProfitability.equation = (expectedProfitability / referenceExpectedProfitability)
        normalizedPerceiedInventoryCoverage.equation = (perceivedInventoryCoverage / referenceInventoryCoverage)
        price.equation = (expectedPrice * effectOfInventoryCoverageOnPrice)
        profit.equation = (revenue - cost)
        referenceDemand.equation = (100.0 + (marketShockOn * sd.step(sizeOfShock, 10.0)))
        relativeValueOfProduct.equation = (priceOfSubstitutes / price)
        revenue.equation = (consumptionRate * price)
        variableCost.equation = (unitVariableCost * productionRate)

        # Constants
        inventoryCoveragePerceptionTime.equation = 3.0
        marketShockOn.equation = 0.0
        priceAdjustmentTime.equation = 3.0
        priceOfSubstitutes.equation = 3.0
        productionTime.equation = 3.0
        profitAdjustmentTime.equation = 12.0
        referenceExpectedProfitability.equation = 100.0
        referenceInventoryCoverage.equation = 3.0
        sizeOfShock.equation = 50.0
        unitCapacityCost.equation = 0.5
        unitVariableCost.equation = 1.0


def simulation_model():
    return CompetitivePricing()
