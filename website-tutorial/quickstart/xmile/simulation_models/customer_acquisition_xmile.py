"""customer_acquisition_xmile - generated from XMILE by the BPTK-Py compiler, target py-sddsl."""

from BPTK_Py import Model
from BPTK_Py import sd_functions as sd


class CustomerAcquisitionXmile(Model):

    def __init__(self):
        super().__init__(starttime=0.0, stoptime=60.0, dt=1.0, name='customer_acquisition_xmile')

        # ── Defining the elements ────────────────────────────────────────────

        # Stocks
        customers = self.stock('customers')
        potentialCustomers = self.stock('potentialCustomers')

        # Flows
        customerAcquisition = self.flow('customerAcquisition')

        # Converters
        acquisitionThroughAdvertising = self.converter('acquisitionThroughAdvertising')
        acquisitionThroughWordOfMouth = self.converter('acquisitionThroughWordOfMouth')
        consumersReachedThroughAdvertising = self.converter('consumersReachedThroughAdvertising')
        consumersReachedThroughWordOfMouth = self.converter('consumersReachedThroughWordOfMouth')
        marketSaturation = self.converter('marketSaturation')

        # Constants
        advertisingBudget = self.constant('advertisingBudget')
        advertisingSuccess = self.constant('advertisingSuccess')
        consumersReachedPerEuro = self.constant('consumersReachedPerEuro')
        contactRate = self.constant('contactRate')
        initialCustomers = self.constant('initialCustomers')
        initialPotentialCustomers = self.constant('initialPotentialCustomers')
        wordOfMouthSuccess = self.constant('wordOfMouthSuccess')

        # ── Setting the initial values and equations ─────────────────────────

        # Stocks
        customers.initial_value = initialCustomers
        customers.inflows = [customerAcquisition]
        potentialCustomers.initial_value = initialPotentialCustomers
        potentialCustomers.outflows = [customerAcquisition]

        # Flows
        customerAcquisition.equation = sd.max(0.0, (acquisitionThroughAdvertising + acquisitionThroughWordOfMouth))

        # Converters
        acquisitionThroughAdvertising.equation = (consumersReachedThroughAdvertising * advertisingSuccess)
        acquisitionThroughWordOfMouth.equation = ((consumersReachedThroughWordOfMouth * wordOfMouthSuccess) * ((1.0 - marketSaturation)))
        consumersReachedThroughAdvertising.equation = ((consumersReachedPerEuro * advertisingBudget) * ((1.0 - marketSaturation)))
        consumersReachedThroughWordOfMouth.equation = (customers * contactRate)
        marketSaturation.equation = (customers / ((potentialCustomers + customers)))

        # Constants
        advertisingBudget.equation = 100.0
        advertisingSuccess.equation = 0.1
        consumersReachedPerEuro.equation = 100.0
        contactRate.equation = 10.0
        initialCustomers.equation = 0.0
        initialPotentialCustomers.equation = 60000.0
        wordOfMouthSuccess.equation = 0.01


def simulation_model():
    return CustomerAcquisitionXmile()
