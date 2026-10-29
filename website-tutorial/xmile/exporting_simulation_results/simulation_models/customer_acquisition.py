"""customer_acquisition - generated from XMILE by the BPTK-Py compiler, target py-sddsl."""

from BPTK_Py import Model
from BPTK_Py import sd_functions as sd


class CustomerAcquisition(Model):

    def __init__(self):
        super().__init__(starttime=0.0, stoptime=60.0, dt=1.0, name='customer_acquisition')

        # ── Defining the elements ────────────────────────────────────────────

        # Stocks
        advertisingCustomers = self.stock('advertisingCustomers')
        customers = self.stock('customers')
        profit = self.stock('profit')
        referralCustomers = self.stock('referralCustomers')

        # Flows
        advCustIn = self.flow('advCustIn')
        customerAcquisition = self.flow('customerAcquisition')
        earnings = self.flow('earnings')
        referralCustIn = self.flow('referralCustIn')
        spending = self.flow('spending')

        # Converters
        acquisitionThroughAdvertising = self.converter('acquisitionThroughAdvertising')
        acquisitionThroughReferrals = self.converter('acquisitionThroughReferrals')
        marketSaturation_ = self.converter('marketSaturation%')
        potentialCustomersReachedThroughAdvertising = self.converter('potentialCustomersReachedThroughAdvertising')

        # Constants
        advertisingSuccess_ = self.constant('advertisingSuccess%')
        classicalAdvertisingCost = self.constant('classicalAdvertisingCost')
        initialCustomers = self.constant('initialCustomers')
        initialInvestmentInService = self.constant('initialInvestmentInService')
        personsReachedPerEuro = self.constant('personsReachedPerEuro')
        referralAdvertisingCost = self.constant('referralAdvertisingCost')
        referralFreeMonths = self.constant('referralFreeMonths')
        referralProgramAdoption_ = self.constant('referralProgramAdoption%')
        referrals = self.constant('referrals')
        serviceFee = self.constant('serviceFee')
        serviceMargin = self.constant('serviceMargin')
        targetCustomerDilution_ = self.constant('targetCustomerDilution%')
        targetMarket = self.constant('targetMarket')

        # ── Setting the initial values and equations ─────────────────────────

        # Stocks
        advertisingCustomers.initial_value = 0.0
        advertisingCustomers.inflows = [advCustIn]
        customers.initial_value = initialCustomers
        customers.inflows = [customerAcquisition]
        profit.initial_value = (-initialInvestmentInService)
        profit.inflows = [earnings]
        profit.outflows = [spending]
        referralCustomers.initial_value = 0.0
        referralCustomers.inflows = [referralCustIn]

        # Flows
        advCustIn.equation = sd.max(0.0, acquisitionThroughAdvertising)
        customerAcquisition.equation = sd.max(0.0, (acquisitionThroughAdvertising + acquisitionThroughReferrals))
        earnings.equation = sd.max(0.0, ((serviceMargin * serviceFee) * customers))
        referralCustIn.equation = sd.max(0.0, acquisitionThroughReferrals)
        spending.equation = sd.max(0.0, sd.If((referrals > 0.0), (((acquisitionThroughReferrals * (((referralFreeMonths * serviceFee) / referrals))) + referralAdvertisingCost) + classicalAdvertisingCost), classicalAdvertisingCost))

        # Converters
        acquisitionThroughAdvertising.equation = ((potentialCustomersReachedThroughAdvertising * advertisingSuccess_) / 100.0)
        acquisitionThroughReferrals.equation = ((((referrals * customers) * ((1.0 - (marketSaturation_ / 100.0)))) * referralProgramAdoption_) / 100.0)
        marketSaturation_.equation = ((100.0 * customers) / targetMarket)
        potentialCustomersReachedThroughAdvertising.equation = ((((personsReachedPerEuro * classicalAdvertisingCost) * targetCustomerDilution_) / 100.0) * ((1.0 - (marketSaturation_ / 100.0))))

        # Constants
        advertisingSuccess_.equation = 0.1
        classicalAdvertisingCost.equation = 10000.0
        initialCustomers.equation = 0.0
        initialInvestmentInService.equation = 1000000.0
        personsReachedPerEuro.equation = 100.0
        referralAdvertisingCost.equation = 10000.0
        referralFreeMonths.equation = 3.0
        referralProgramAdoption_.equation = 10.0
        referrals.equation = 0.0
        serviceFee.equation = 10.0
        serviceMargin.equation = 0.5
        targetCustomerDilution_.equation = 80.0
        targetMarket.equation = 6000000.0


def simulation_model():
    return CustomerAcquisition()
