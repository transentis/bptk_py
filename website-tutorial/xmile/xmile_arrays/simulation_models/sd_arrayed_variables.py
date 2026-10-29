"""sd_arrayed_variables - generated from XMILE by the BPTK-Py compiler, target py-sddsl."""

from BPTK_Py import Model
from BPTK_Py import sd_functions as sd


class SdArrayedVariables(Model):

    def __init__(self):
        super().__init__(starttime=1.0, stoptime=13.0, dt=0.25, name='sd_arrayed_variables')

        # ── Defining the elements ────────────────────────────────────────────

        # Stocks
        inventory = self.stock('inventory')
        inventory.setup_named_matrix({'1': {'germany': 0.0, 'england': 0.0, 'austria': 0.0, 'greece': 0.0}, '2': {'germany': 0.0, 'england': 0.0, 'austria': 0.0, 'greece': 0.0}, '3': {'germany': 0.0, 'england': 0.0, 'austria': 0.0, 'greece': 0.0}})
        production = self.stock('production')
        production.setup_named_matrix({'1': {'germany': 0.0, 'england': 0.0, 'austria': 0.0, 'greece': 0.0}, '2': {'germany': 0.0, 'england': 0.0, 'austria': 0.0, 'greece': 0.0}, '3': {'germany': 0.0, 'england': 0.0, 'austria': 0.0, 'greece': 0.0}})

        # Flows
        productionRate = self.flow('productionRate')
        productionRate.setup_named_matrix({'1': {'germany': 0.0, 'england': 0.0, 'austria': 0.0, 'greece': 0.0}, '2': {'germany': 0.0, 'england': 0.0, 'austria': 0.0, 'greece': 0.0}, '3': {'germany': 0.0, 'england': 0.0, 'austria': 0.0, 'greece': 0.0}})
        productionStart = self.flow('productionStart')
        productionStart.setup_named_matrix({'1': {'germany': 0.0, 'england': 0.0, 'austria': 0.0, 'greece': 0.0}, '2': {'germany': 0.0, 'england': 0.0, 'austria': 0.0, 'greece': 0.0}, '3': {'germany': 0.0, 'england': 0.0, 'austria': 0.0, 'greece': 0.0}})

        # Converters
        averageInventory = self.converter('averageInventory')
        averageInventoryUsingSize = self.converter('averageInventoryUsingSize')
        inventorySize = self.converter('inventorySize')
        largestGermanInventory = self.converter('largestGermanInventory')
        productionDuration = self.converter('productionDuration')
        productionDuration.setup_named_matrix({'1': {'germany': 0.0, 'england': 0.0, 'austria': 0.0, 'greece': 0.0}, '2': {'germany': 0.0, 'england': 0.0, 'austria': 0.0, 'greece': 0.0}, '3': {'germany': 0.0, 'england': 0.0, 'austria': 0.0, 'greece': 0.0}})
        productionStartRate = self.converter('productionStartRate')
        productionStartRate.setup_named_matrix({'1': {'germany': 0.0, 'england': 0.0, 'austria': 0.0, 'greece': 0.0}, '2': {'germany': 0.0, 'england': 0.0, 'austria': 0.0, 'greece': 0.0}, '3': {'germany': 0.0, 'england': 0.0, 'austria': 0.0, 'greece': 0.0}})
        smallestGermanInventory = self.converter('smallestGermanInventory')
        totalInventory = self.converter('totalInventory')

        # ── Setting the initial values and equations ─────────────────────────

        # Stocks
        inventory['1']['germany'].initial_value = 0.0
        inventory['1']['germany'].inflows = [productionRate['1']['germany']]
        inventory['1']['england'].initial_value = 0.0
        inventory['1']['england'].inflows = [productionRate['1']['england']]
        inventory['1']['austria'].initial_value = 0.0
        inventory['1']['austria'].inflows = [productionRate['1']['austria']]
        inventory['1']['greece'].initial_value = 0.0
        inventory['1']['greece'].inflows = [productionRate['1']['greece']]
        inventory['2']['germany'].initial_value = 0.0
        inventory['2']['germany'].inflows = [productionRate['2']['germany']]
        inventory['2']['england'].initial_value = 0.0
        inventory['2']['england'].inflows = [productionRate['2']['england']]
        inventory['2']['austria'].initial_value = 0.0
        inventory['2']['austria'].inflows = [productionRate['2']['austria']]
        inventory['2']['greece'].initial_value = 0.0
        inventory['2']['greece'].inflows = [productionRate['2']['greece']]
        inventory['3']['germany'].initial_value = 0.0
        inventory['3']['germany'].inflows = [productionRate['3']['germany']]
        inventory['3']['england'].initial_value = 0.0
        inventory['3']['england'].inflows = [productionRate['3']['england']]
        inventory['3']['austria'].initial_value = 0.0
        inventory['3']['austria'].inflows = [productionRate['3']['austria']]
        inventory['3']['greece'].initial_value = 0.0
        inventory['3']['greece'].inflows = [productionRate['3']['greece']]
        production['1']['germany'].initial_value = 0.0
        production['1']['germany'].inflows = [productionStart['1']['germany']]
        production['1']['germany'].outflows = [productionRate['1']['germany']]
        production['1']['england'].initial_value = 0.0
        production['1']['england'].inflows = [productionStart['1']['england']]
        production['1']['england'].outflows = [productionRate['1']['england']]
        production['1']['austria'].initial_value = 0.0
        production['1']['austria'].inflows = [productionStart['1']['austria']]
        production['1']['austria'].outflows = [productionRate['1']['austria']]
        production['1']['greece'].initial_value = 0.0
        production['1']['greece'].inflows = [productionStart['1']['greece']]
        production['1']['greece'].outflows = [productionRate['1']['greece']]
        production['2']['germany'].initial_value = 0.0
        production['2']['germany'].inflows = [productionStart['2']['germany']]
        production['2']['germany'].outflows = [productionRate['2']['germany']]
        production['2']['england'].initial_value = 0.0
        production['2']['england'].inflows = [productionStart['2']['england']]
        production['2']['england'].outflows = [productionRate['2']['england']]
        production['2']['austria'].initial_value = 0.0
        production['2']['austria'].inflows = [productionStart['2']['austria']]
        production['2']['austria'].outflows = [productionRate['2']['austria']]
        production['2']['greece'].initial_value = 0.0
        production['2']['greece'].inflows = [productionStart['2']['greece']]
        production['2']['greece'].outflows = [productionRate['2']['greece']]
        production['3']['germany'].initial_value = 0.0
        production['3']['germany'].inflows = [productionStart['3']['germany']]
        production['3']['germany'].outflows = [productionRate['3']['germany']]
        production['3']['england'].initial_value = 0.0
        production['3']['england'].inflows = [productionStart['3']['england']]
        production['3']['england'].outflows = [productionRate['3']['england']]
        production['3']['austria'].initial_value = 0.0
        production['3']['austria'].inflows = [productionStart['3']['austria']]
        production['3']['austria'].outflows = [productionRate['3']['austria']]
        production['3']['greece'].initial_value = 0.0
        production['3']['greece'].inflows = [productionStart['3']['greece']]
        production['3']['greece'].outflows = [productionRate['3']['greece']]

        # Flows
        productionRate['1']['germany'].equation = sd.max(0.0, sd.delay(self, productionStart['1']['germany'], productionDuration['1']['germany'], 0.0))
        productionRate['1']['england'].equation = sd.max(0.0, sd.delay(self, productionStart['1']['england'], productionDuration['1']['england'], 0.0))
        productionRate['1']['austria'].equation = sd.max(0.0, sd.delay(self, productionStart['1']['austria'], productionDuration['1']['austria'], 0.0))
        productionRate['1']['greece'].equation = sd.max(0.0, sd.delay(self, productionStart['1']['greece'], productionDuration['1']['greece'], 0.0))
        productionRate['2']['germany'].equation = sd.max(0.0, sd.delay(self, productionStart['2']['germany'], productionDuration['2']['germany'], 0.0))
        productionRate['2']['england'].equation = sd.max(0.0, sd.delay(self, productionStart['2']['england'], productionDuration['2']['england'], 0.0))
        productionRate['2']['austria'].equation = sd.max(0.0, sd.delay(self, productionStart['2']['austria'], productionDuration['2']['austria'], 0.0))
        productionRate['2']['greece'].equation = sd.max(0.0, sd.delay(self, productionStart['2']['greece'], productionDuration['2']['greece'], 0.0))
        productionRate['3']['germany'].equation = sd.max(0.0, sd.delay(self, productionStart['3']['germany'], productionDuration['3']['germany'], 0.0))
        productionRate['3']['england'].equation = sd.max(0.0, sd.delay(self, productionStart['3']['england'], productionDuration['3']['england'], 0.0))
        productionRate['3']['austria'].equation = sd.max(0.0, sd.delay(self, productionStart['3']['austria'], productionDuration['3']['austria'], 0.0))
        productionRate['3']['greece'].equation = sd.max(0.0, sd.delay(self, productionStart['3']['greece'], productionDuration['3']['greece'], 0.0))
        productionStart['1']['germany'].equation = sd.max(0.0, productionStartRate['1']['germany'])
        productionStart['1']['england'].equation = sd.max(0.0, productionStartRate['1']['england'])
        productionStart['1']['austria'].equation = sd.max(0.0, productionStartRate['1']['austria'])
        productionStart['1']['greece'].equation = sd.max(0.0, productionStartRate['1']['greece'])
        productionStart['2']['germany'].equation = sd.max(0.0, productionStartRate['2']['germany'])
        productionStart['2']['england'].equation = sd.max(0.0, productionStartRate['2']['england'])
        productionStart['2']['austria'].equation = sd.max(0.0, productionStartRate['2']['austria'])
        productionStart['2']['greece'].equation = sd.max(0.0, productionStartRate['2']['greece'])
        productionStart['3']['germany'].equation = sd.max(0.0, productionStartRate['3']['germany'])
        productionStart['3']['england'].equation = sd.max(0.0, productionStartRate['3']['england'])
        productionStart['3']['austria'].equation = sd.max(0.0, productionStartRate['3']['austria'])
        productionStart['3']['greece'].equation = sd.max(0.0, productionStartRate['3']['greece'])

        # Converters
        averageInventory.equation = inventory[:, :].arr_mean()
        averageInventoryUsingSize.equation = (inventory[:, :].arr_sum() / 12.0)
        inventorySize.equation = 12.0
        largestGermanInventory.equation = sd.If(inventory[:, 'germany'].arr_rank(3.0) == 1.0, inventory['1']['germany'], sd.If(inventory[:, 'germany'].arr_rank(3.0) == 2.0, inventory['2']['germany'], sd.If(inventory[:, 'germany'].arr_rank(3.0) == 3.0, inventory['3']['germany'], 0.0)))
        productionDuration['1']['germany'].equation = 1.0
        productionDuration['1']['england'].equation = 2.0
        productionDuration['1']['austria'].equation = 3.0
        productionDuration['1']['greece'].equation = 4.0
        productionDuration['2']['germany'].equation = 5.0
        productionDuration['2']['england'].equation = 6.0
        productionDuration['2']['austria'].equation = 8.0
        productionDuration['2']['greece'].equation = 7.0
        productionDuration['3']['germany'].equation = 9.0
        productionDuration['3']['england'].equation = 10.0
        productionDuration['3']['austria'].equation = 11.0
        productionDuration['3']['greece'].equation = 12.0
        productionStartRate['1']['germany'].equation = 10.0
        productionStartRate['1']['england'].equation = 20.0
        productionStartRate['1']['austria'].equation = 30.0
        productionStartRate['1']['greece'].equation = 40.0
        productionStartRate['2']['germany'].equation = 40.0
        productionStartRate['2']['england'].equation = 30.0
        productionStartRate['2']['austria'].equation = 20.0
        productionStartRate['2']['greece'].equation = 10.0
        productionStartRate['3']['germany'].equation = 20.0
        productionStartRate['3']['england'].equation = 30.0
        productionStartRate['3']['austria'].equation = 40.0
        productionStartRate['3']['greece'].equation = 50.0
        smallestGermanInventory.equation = sd.If(inventory[:, 'germany'].arr_rank(1.0) == 1.0, inventory['1']['germany'], sd.If(inventory[:, 'germany'].arr_rank(1.0) == 2.0, inventory['2']['germany'], sd.If(inventory[:, 'germany'].arr_rank(1.0) == 3.0, inventory['3']['germany'], 0.0)))
        totalInventory.equation = inventory[:, :].arr_sum()


def simulation_model():
    return SdArrayedVariables()
