
from BPTK_Py import Model
from BPTK_Py import sd_functions as sd

class simulation_model(Model):

    def __init__(self):

        # Never forget calling the super method to initialize the main parameters
        super().__init__(starttime=0.0,stoptime=15.0,dt=1.0,name ='abc' )

        # Stocks
        totalValue = self.stock("totalValue")

        # Flows
        interest = self.flow("interest")
        deposit = self.flow("deposit")

        # Converters
    
        # Constants
        interestRate = self.constant("interestRate")
        depositRate = self.constant("depositRate")
        initialValue = self.constant("initialValue")
        
        # Actual Logic

        initialValue.equation = 1000.0
        interestRate.equation = 0.05
        depositRate.equation = 1000.0

        totalValue.initial_value = initialValue

        interest.equation = interestRate * totalValue
        deposit.equation = depositRate

        totalValue.equation = interest + deposit


        