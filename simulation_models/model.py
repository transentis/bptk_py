#      _                   _ _
#  _____| |__ ___ _ __  _ __(_| |___ _ _
# (_-/ _` / _/ _ | '  \| '_ | | / -_| '_|
# /__\__,_\__\___|_|_|_| .__|_|_\___|_|
#                      |_|
# Copyright (c) 2013-2016 transentis management & consulting. All rights reserved.
#




import statistics
import math
import random

# linear interpolation between a set points
def LERP(x, points):
	first = 0
	last = len(points)-1

	def getX(i):
			return points[i][0]

	def getY(i):
			return points[i][1]

	def getOffset(x):
			for i in range(first,last):
					if x < getX(i): return i-1
			return last -1

	if x <= getX(first): return getY(first)
	if x >= getX(last): return getY(last)

	n = getOffset(x)
	x0 = getX(n)
	y0 = getY(n)
	x1 = getX(n+1)
	y1 = getY(n+1)

	return (y1 - y0) * (x - x0) / (x1 - x0) + y0


class simulation_model():
  def memoize(self, equation, arg):
    mymemo = self.memo[equation]
    if equation in self.constants and int(arg) > 0:
      return self.equations[equation](0)
    if arg in mymemo.keys():
      return mymemo[arg]
    else:
      result = self.equations[equation](arg)
      mymemo[arg] = result
      return result

  def __init__(self):
    # Simulation Buildins
    self.dt = 1
    self.starttime = 1
    self.stoptime = 61
    self.equations = {
  	# Stocks 
  		'capabilities▸totalWorkforceExperience': lambda t : max( 0, self.memoize('resources▸initialEmployees', t) * 12 if  t  <=  self.starttime  else self.memoize('capabilities▸totalWorkforceExperience', t-self.dt) +  self.dt  * ( self.memoize('capabilities▸gainingExperience', t-self.dt) - ( self.memoize('capabilities▸losingExperience', t) ) ) ),

  		'cash▸cash': lambda t : max( 0, self.memoize('equity▸initialShareholderStock', t) if  t  <=  self.starttime  else self.memoize('cash▸cash', t-self.dt) +  self.dt  * ( self.memoize('cash▸cashIn', t-self.dt) + self.memoize('cash▸cashFromBorrowing', t) - ( self.memoize('cash▸cashOut', t) ) ) ),

  		'cashFlow▸cashFlowYtd': lambda t : 0 if  t  <=  self.starttime  else self.memoize('cashFlow▸cashFlowYtd', t-self.dt) +  self.dt  * ( self.memoize('cashFlow▸cashFlowIn', t-self.dt) - ( self.memoize('cashFlow▸cashFlowReset', t) ) ),

  		'cashFlow▸financingCashFlowYtd': lambda t : 0 if  t  <=  self.starttime  else self.memoize('cashFlow▸financingCashFlowYtd', t-self.dt) +  self.dt  * ( self.memoize('cashFlow▸financingCashFlowIn', t-self.dt) - ( self.memoize('cashFlow▸financingCashFlowReset', t) ) ),

  		'cashFlow▸investmentCashFlowYtd': lambda t : 0 if  t  <=  self.starttime  else self.memoize('cashFlow▸investmentCashFlowYtd', t-self.dt) +  self.dt  * ( self.memoize('cashFlow▸investmentCashFlowIn', t-self.dt) - ( self.memoize('cashFlow▸investmentCashFlowReset', t) ) ),

  		'cashFlow▸operatingCashFlowYtd': lambda t : 0 if  t  <=  self.starttime  else self.memoize('cashFlow▸operatingCashFlowYtd', t-self.dt) +  self.dt  * ( self.memoize('cashFlow▸operatingCashFlowIn', t-self.dt) - ( self.memoize('cashFlow▸operatingCashFlowReset', t) ) ),

  		'cost▸cashExpensesYtd': lambda t : 0 if  t  <=  self.starttime  else self.memoize('cost▸cashExpensesYtd', t-self.dt) +  self.dt  * ( self.memoize('cost▸cashExpensesIn', t-self.dt) - ( self.memoize('cost▸cashExpensesReset', t) ) ),

  		'cost▸expensesYtd': lambda t : 0 if  t  <=  self.starttime  else self.memoize('cost▸expensesYtd', t-self.dt) +  self.dt  * ( self.memoize('cost▸expensesIs', t-self.dt) - ( self.memoize('cost▸yearlyExpensesReset', t) ) ),

  		'cost▸interestOnDebtYtd': lambda t : 0 if  t  <=  self.starttime  else self.memoize('cost▸interestOnDebtYtd', t-self.dt) +  self.dt  * ( self.memoize('cost▸interestDebtIn', t-self.dt) - ( self.memoize('cost▸interestDebtReset', t) ) ),

  		'cost▸marketingCostsYtd': lambda t : 0 if  t  <=  self.starttime  else self.memoize('cost▸marketingCostsYtd', t-self.dt) +  self.dt  * ( self.memoize('cost▸monthlyMarketingCost', t-self.dt) - ( self.memoize('cost▸yearlyMarketingCostReset', t) ) ),

  		'cost▸nonCashExpensesYtd': lambda t : 0 if  t  <=  self.starttime  else self.memoize('cost▸nonCashExpensesYtd', t-self.dt) +  self.dt  * ( self.memoize('cost▸nonCashExpensesIn', t-self.dt) - ( self.memoize('cost▸nonCashExpensesReset', t) ) ),

  		'cost▸payables': lambda t : 0 if  t  <=  self.starttime  else self.memoize('cost▸payables', t-self.dt) +  self.dt  * ( self.memoize('cost▸payablesIn', t-self.dt) - ( self.memoize('cost▸payablesOut', t) ) ),

  		'cost▸serviceCostsYtd': lambda t : 0 if  t  <=  self.starttime  else self.memoize('cost▸serviceCostsYtd', t-self.dt) +  self.dt  * ( self.memoize('cost▸monthlyServiceCost', t-self.dt) - ( self.memoize('cost▸yearlyServiceCostReset', t) ) ),

  		'cost▸wagesYtd': lambda t : 0 if  t  <=  self.starttime  else self.memoize('cost▸wagesYtd', t-self.dt) +  self.dt  * ( self.memoize('cost▸monthlyWages', t-self.dt) - ( self.memoize('cost▸yearlyWageReset', t) ) ),

  		'cost▸workplaceCostYtd': lambda t : 0 if  t  <=  self.starttime  else self.memoize('cost▸workplaceCostYtd', t-self.dt) +  self.dt  * ( self.memoize('cost▸monthlyWorkplaceCosts', t-self.dt) - ( self.memoize('cost▸yearlyWorkplaceCostReset', t) ) ),

  		'customers▸customers': lambda t : 100 if  t  <=  self.starttime  else self.memoize('customers▸customers', t-self.dt) +  self.dt  * ( self.memoize('customers▸customerAcquisition', t-self.dt) ),

  		'customers▸dynamicMarketBudget': lambda t : max( 0, self.memoize('customers▸marketingBudget', t) if  t  <=  self.starttime  else self.memoize('customers▸dynamicMarketBudget', t-self.dt) +  self.dt  * ( self.memoize('customers▸dynamicMarketBudgetRateOfChange', t-self.dt) ) ),

  		'customers▸marketingCustomers': lambda t : 0 if  t  <=  self.starttime  else self.memoize('customers▸marketingCustomers', t-self.dt) +  self.dt  * ( self.memoize('customers▸advCustIn', t-self.dt) ),

  		'customers▸potentialCustomers': lambda t : 6000000 if  t  <=  self.starttime  else self.memoize('customers▸potentialCustomers', t-self.dt) +  self.dt  * ( -1 * ( self.memoize('customers▸customerAcquisition', t-self.dt) ) ),

  		'customers▸wordOfMouthCustomers': lambda t : 0 if  t  <=  self.starttime  else self.memoize('customers▸wordOfMouthCustomers', t-self.dt) +  self.dt  * ( self.memoize('customers▸womCustIn', t-self.dt) ),

  		'debt▸debt': lambda t : self.memoize('debt▸initialDebt', t) if  t  <=  self.starttime  else self.memoize('debt▸debt', t-self.dt) +  self.dt  * ( self.memoize('debt▸debtIn', t-self.dt) - ( self.memoize('debt▸debtOut', t) ) ),

  		'debt▸debtRepayments': lambda t : 0 if  t  <=  self.starttime  else self.memoize('debt▸debtRepayments', t-self.dt) +  self.dt  * ( self.memoize('debt▸repaymentsIn', t-self.dt) - ( self.memoize('debt▸repaymentsOut', t) ) ),

  		'debt▸interestOnDebt': lambda t : 0 if  t  <=  self.starttime  else self.memoize('debt▸interestOnDebt', t-self.dt) +  self.dt  * ( self.memoize('debt▸interestIn', t-self.dt) - ( self.memoize('debt▸interestOut', t) ) ),

  		'debt▸interestReductionAmount': lambda t : 0 if  t  <=  self.starttime  else self.memoize('debt▸interestReductionAmount', t-self.dt) +  self.dt  * ( self.memoize('debt▸interestReductionIn', t-self.dt) - ( self.memoize('debt▸interestReductionOut', t) ) ),

  		'earnings▸earnings': lambda t : 0 if  t  <=  self.starttime  else self.memoize('earnings▸earnings', t-self.dt) +  self.dt  * ( self.memoize('earnings▸yearlyEarnings', t-self.dt) ),

  		'equity▸stock': lambda t : max( 0, self.memoize('equity▸initialShareholderStock', t) if  t  <=  self.starttime  else self.memoize('equity▸stock', t-self.dt) +  self.dt  * 0 ),

  		'productPortfolio▸featureIdeas': lambda t : max( 0, 200 if  t  <=  self.starttime  else self.memoize('productPortfolio▸featureIdeas', t-self.dt) +  self.dt  * ( self.memoize('productPortfolio▸featureIdeasDocumented', t-self.dt) - ( self.memoize('productPortfolio▸featuresAccepted', t) + self.memoize('productPortfolio▸featuresDismissed', t) ) ) ),

  		'productPortfolio▸featureReleaseCompletionStatus': lambda t : 0 if  t  <=  self.starttime  else self.memoize('productPortfolio▸featureReleaseCompletionStatus', t-self.dt) +  self.dt  * ( self.memoize('productPortfolio▸featuresCompleted', t-self.dt) - ( self.memoize('productPortfolio▸frcsReset', t) ) ),

  		'productPortfolio▸featuresInDesign': lambda t : 1 if  t  <=  self.starttime  else self.memoize('productPortfolio▸featuresInDesign', t-self.dt) +  self.dt  * ( self.memoize('productPortfolio▸featuresAccepted', t-self.dt) - ( self.memoize('productPortfolio▸featuresDesigned', t) ) ),

  		'productPortfolio▸featuresInDevelopment': lambda t : 1 if  t  <=  self.starttime  else self.memoize('productPortfolio▸featuresInDevelopment', t-self.dt) +  self.dt  * ( self.memoize('productPortfolio▸featuresDesigned', t-self.dt) - ( self.memoize('productPortfolio▸featuresDeveloped', t) ) ),

  		'productPortfolio▸featuresInLaunch': lambda t : 0 if  t  <=  self.starttime  else self.memoize('productPortfolio▸featuresInLaunch', t-self.dt) +  self.dt  * ( self.memoize('productPortfolio▸featuresTested', t-self.dt) - ( self.memoize('productPortfolio▸featuresLaunched', t) ) ),

  		'productPortfolio▸featuresInTest': lambda t : 1 if  t  <=  self.starttime  else self.memoize('productPortfolio▸featuresInTest', t-self.dt) +  self.dt  * ( self.memoize('productPortfolio▸featuresDeveloped', t-self.dt) - ( self.memoize('productPortfolio▸featuresTested', t) ) ),

  		'productPortfolio▸timeSinceLastFeatureRelease': lambda t : 0 if  t  <=  self.starttime  else self.memoize('productPortfolio▸timeSinceLastFeatureRelease', t-self.dt) +  self.dt  * ( self.memoize('productPortfolio▸timePassing', t-self.dt) - ( self.memoize('productPortfolio▸featureReleaseTimerReset', t) ) ),

  		'resources▸customerService': lambda t : self.memoize('resources▸initialCustomerService', t) if  t  <=  self.starttime  else self.memoize('resources▸customerService', t-self.dt) +  self.dt  * ( self.memoize('resources▸customerServiceIn', t-self.dt) - ( self.memoize('resources▸customerServiceOut', t) ) ),

  		'resources▸managingDirectors': lambda t : 2 if  t  <=  self.starttime  else self.memoize('resources▸managingDirectors', t-self.dt) +  self.dt  * 0,

  		'resources▸marketing': lambda t : self.memoize('resources▸initialMarketing', t) if  t  <=  self.starttime  else self.memoize('resources▸marketing', t-self.dt) +  self.dt  * 0,

  		'resources▸productDesigner': lambda t : self.memoize('resources▸initialProductDesigner', t) if  t  <=  self.starttime  else self.memoize('resources▸productDesigner', t-self.dt) +  self.dt  * ( self.memoize('resources▸productDesignerIn', t-self.dt) ),

  		'resources▸productDeveloper': lambda t : self.memoize('resources▸initialProductDevelopers', t) if  t  <=  self.starttime  else self.memoize('resources▸productDeveloper', t-self.dt) +  self.dt  * ( self.memoize('resources▸producDeveloperIn', t-self.dt) ),

  		'resources▸productTester': lambda t : self.memoize('resources▸initialProductTester', t) if  t  <=  self.starttime  else self.memoize('resources▸productTester', t-self.dt) +  self.dt  * ( self.memoize('resources▸productTesterIn', t-self.dt) ),

  		'revenue▸receivables': lambda t : 0 if  t  <=  self.starttime  else self.memoize('revenue▸receivables', t-self.dt) +  self.dt  * ( self.memoize('revenue▸receivablesIn', t-self.dt) - ( self.memoize('revenue▸receivablesOut', t) + self.memoize('revenue▸defaults', t) ) ),

  		'revenue▸revenueYtd': lambda t : 0 if  t  <=  self.starttime  else self.memoize('revenue▸revenueYtd', t-self.dt) +  self.dt  * ( self.memoize('revenue▸revenueIn', t-self.dt) - ( self.memoize('revenue▸yearlyRevenueReset', t) ) ),

  		'taxes▸provisionsForTax': lambda t : 0 if  t  <=  self.starttime  else self.memoize('taxes▸provisionsForTax', t-self.dt) +  self.dt  * ( self.memoize('taxes▸taxProvisionsIn', t-self.dt) - ( self.memoize('taxes▸taxesBecomingDue', t) ) ),

  		'taxes▸taxPayment': lambda t : max( 0, 0 if  t  <=  self.starttime  else self.memoize('taxes▸taxPayment', t-self.dt) +  self.dt  * ( self.memoize('taxes▸newPayments', t-self.dt) - ( self.memoize('taxes▸paymentBeingMade', t) ) ) ),

  		'taxes▸taxesDue': lambda t : 0 if  t  <=  self.starttime  else self.memoize('taxes▸taxesDue', t-self.dt) +  self.dt  * ( self.memoize('taxes▸taxesBecomingDue', t-self.dt) - ( self.memoize('taxes▸payingForTax', t) ) ),
    # flows 
  		'capabilities▸gainingExperience': lambda t : max( 0, self.memoize('resources▸employees', t) ),
  	
  		'capabilities▸losingExperience': lambda t : max( 0, self.memoize('capabilities▸workforceExperience', t) * self.memoize('resources▸employeesLost', t) ),
  	
  		'cash▸cashFromBorrowing': lambda t : max( 0, self.memoize('debt▸cashBorrowed', t) ),
  	
  		'cash▸cashIn': lambda t : max( 0, self.memoize('revenue▸receivablesOut', t) ),
  	
  		'cash▸cashOut': lambda t : max( 0, self.memoize('cash▸cashPayments', t) ),
  	
  		'cashFlow▸cashFlowIn': lambda t : self.memoize('cashFlow▸cashFlow', t),
  	
  		'cashFlow▸cashFlowReset': lambda t : max( 0, self.memoize('cashFlow▸cashFlowYtd', t)/ dt if 13 <= t and ((t -13) % 12) == 0 else 0 ),
  	
  		'cashFlow▸financingCashFlowIn': lambda t : self.memoize('cashFlow▸financingCashFlow', t),
  	
  		'cashFlow▸financingCashFlowReset': lambda t : max( 0, self.memoize('cashFlow▸financingCashFlowYtd', t)/ dt if 13 <= t and ((t -13) % 12) == 0 else 0 ),
  	
  		'cashFlow▸investmentCashFlowIn': lambda t : max( 0, self.memoize('cashFlow▸investmentCashFlow', t) ),
  	
  		'cashFlow▸investmentCashFlowReset': lambda t : max( 0, self.memoize('cashFlow▸investmentCashFlowYtd', t)/ dt if 13 <= t and ((t -13) % 12) == 0 else 0 ),
  	
  		'cashFlow▸operatingCashFlowIn': lambda t : self.memoize('cashFlow▸operatingCashFlow', t),
  	
  		'cashFlow▸operatingCashFlowReset': lambda t : max( 0, self.memoize('cashFlow▸operatingCashFlowYtd', t)/ dt if 13 <= t and ((t -13) % 12) == 0 else 0 ),
  	
  		'cost▸cashExpensesIn': lambda t : max( 0, self.memoize('cost▸cashExpenses', t) ),
  	
  		'cost▸cashExpensesReset': lambda t : max( 0, self.memoize('cost▸cashExpensesYtd', t)/ dt if 13 <= t and ((t -13) % 12) == 0 else 0 ),
  	
  		'cost▸expensesIs': lambda t : max( 0, self.memoize('cost▸expenses', t) ),
  	
  		'cost▸interestDebtIn': lambda t : max( 0, self.memoize('debt▸interestOnDebt', t) ),
  	
  		'cost▸interestDebtReset': lambda t : max( 0, self.memoize('cost▸interestOnDebtYtd', t)/ dt if 13 <= t and ((t -13) % 12) == 0 else 0 ),
  	
  		'cost▸monthlyMarketingCost': lambda t : max( 0, self.memoize('customers▸effectiveMarketingBudget', t) ),
  	
  		'cost▸monthlyServiceCost': lambda t : max( 0, self.memoize('cost▸serviceCost', t) ),
  	
  		'cost▸monthlyWages': lambda t : max( 0, self.memoize('cost▸wages', t) ),
  	
  		'cost▸monthlyWorkplaceCosts': lambda t : max( 0, self.memoize('cost▸workplaceCost', t) ),
  	
  		'cost▸nonCashExpensesIn': lambda t : max( 0, self.memoize('cost▸nonCashExpenses', t) ),
  	
  		'cost▸nonCashExpensesReset': lambda t : max( 0, self.memoize('cost▸nonCashExpensesYtd', t)/ dt if 13 <= t and ((t -13) % 12) == 0 else 0 ),
  	
  		'cost▸payablesIn': lambda t : max( 0, self.memoize('customers▸effectiveMarketingBudget', t) + self.memoize('cost▸serviceCost', t) + self.memoize('cost▸workplaceCost', t) ),
  	
  		'cost▸payablesOut': lambda t : max( 0, 0  if t - self.starttime < self.memoize('cost▸paymentTime', t) else self.memoize('cost▸payablesIn', ( t - (self.memoize('cost▸paymentTime', t)) )) ),
  	
  		'cost▸yearlyExpensesReset': lambda t : max( 0, self.memoize('cost▸expensesYtd', t)/ dt if 13 <= t and ((t -13) % 12) == 0 else 0 ),
  	
  		'cost▸yearlyMarketingCostReset': lambda t : max( 0, self.memoize('cost▸marketingCostsYtd', t)/ dt if 13 <= t and ((t -13) % 12) == 0 else 0 ),
  	
  		'cost▸yearlyServiceCostReset': lambda t : max( 0, self.memoize('cost▸serviceCostsYtd', t)/ dt if 13 <= t and ((t -13) % 12) == 0 else 0 ),
  	
  		'cost▸yearlyWageReset': lambda t : max( 0, self.memoize('cost▸wagesYtd', t)/ dt if 13 <= t and ((t -13) % 12) == 0 else 0 ),
  	
  		'cost▸yearlyWorkplaceCostReset': lambda t : max( 0, self.memoize('cost▸workplaceCostYtd', t)/ dt if 13 <= t and ((t -13) % 12) == 0 else 0 ),
  	
  		'customers▸advCustIn': lambda t : max( 0, self.memoize('customers▸acquisitionThroughMarketing', t) ),
  	
  		'customers▸customerAcquisition': lambda t : max( 0, self.memoize('customers▸acquisitionThroughMarketing', t) + self.memoize('customers▸acquisitionThroughWordOfMouth', t) ),
  	
  		'customers▸dynamicMarketBudgetRateOfChange': lambda t : self.memoize('customers▸targetMarketingBudget', t) / self.memoize('customers▸timeToAdjustDynamicMktBudget', t),
  	
  		'customers▸womCustIn': lambda t : max( 0, self.memoize('customers▸acquisitionThroughWordOfMouth', t) ),
  	
  		'debt▸debtIn': lambda t : max( 0, self.memoize('debt▸cashBorrowed', t) ),
  	
  		'debt▸debtOut': lambda t : max( 0, min( self.memoize('debt▸debt', t), self.memoize('debt▸debtRepayments', t) ) ),
  	
  		'debt▸interestIn': lambda t : max( 0, self.memoize('debt▸debtIn', t) * self.memoize('debt▸yearlyInterestOnDebtPct', t) / ( 12 * 100 ) ),
  	
  		'debt▸interestOut': lambda t : max( 0, min( self.memoize('debt▸interestOnDebt', t), self.memoize('debt▸interestReductionAmount', t) ) ),
  	
  		'debt▸interestReductionIn': lambda t : max( 0, self.memoize('debt▸repaymentsIn', t) * self.memoize('debt▸yearlyInterestOnDebtPct', t) / ( 12 * 100 ) ),
  	
  		'debt▸interestReductionOut': lambda t : max( 0, min( self.memoize('debt▸interestReductionAmount', t), 0  if t - self.starttime < self.memoize('debt▸numberOfRepaymentPeriods', t) else self.memoize('debt▸interestReductionIn', ( t - (self.memoize('debt▸numberOfRepaymentPeriods', t)) )) ) ),
  	
  		'debt▸repaymentsIn': lambda t : max( 0, self.memoize('debt▸debtIn', t) / self.memoize('debt▸numberOfRepaymentPeriods', t) ),
  	
  		'debt▸repaymentsOut': lambda t : max( 0, min( 0  if t - self.starttime < self.memoize('debt▸numberOfRepaymentPeriods', t) else self.memoize('debt▸repaymentsIn', ( t - (self.memoize('debt▸numberOfRepaymentPeriods', t)) )), self.memoize('debt▸debtRepayments', t) ) ),
  	
  		'earnings▸yearlyEarnings': lambda t : self.memoize('earnings▸profitAfterTaxYtd', t)/ dt if 13 <= t and ((t -13) % 12) == 0 else 0,
  	
  		'productPortfolio▸featureIdeasDocumented': lambda t : max( 0, self.memoize('productPortfolio▸featureIdeasFromCustomers', t) ),
  	
  		'productPortfolio▸featureReleaseTimerReset': lambda t : max( 0, ( self.memoize('productPortfolio▸timeSinceLastFeatureRelease', t) ) / dt if self.memoize('productPortfolio▸featureReleaseLaunchPolicy', t) > 0 else 0 ),
  	
  		'productPortfolio▸featuresAccepted': lambda t : max( 0, self.memoize('productPortfolio▸featureAcceptanceRate', t) ),
  	
  		'productPortfolio▸featuresCompleted': lambda t : max( 0, self.memoize('productPortfolio▸featuresTested', t) ),
  	
  		'productPortfolio▸featuresDesigned': lambda t : max( 0, min( self.memoize('resources▸featureDesignCapacity', t) * self.memoize('productPortfolio▸featuresInDesign', t) / self.memoize('productPortfolio▸featureDesignEffort', t), self.memoize('productPortfolio▸featuresInDesign', t) ) ),
  	
  		'productPortfolio▸featuresDeveloped': lambda t : max( 0, min( self.memoize('resources▸featureDevelopmentCapacity', t) * self.memoize('productPortfolio▸featuresInDevelopment', t) / self.memoize('productPortfolio▸featureDevelopmentEffort', t), self.memoize('productPortfolio▸featuresInDevelopment', t) ) ),
  	
  		'productPortfolio▸featuresDismissed': lambda t : max( 0, self.memoize('productPortfolio▸featureDismissalRate', t) ),
  	
  		'productPortfolio▸featuresLaunched': lambda t : 0,
  	
  		'productPortfolio▸featuresTested': lambda t : max( 0, min( self.memoize('resources▸featureTestCapacity', t) * self.memoize('productPortfolio▸featuresInTest', t) / self.memoize('productPortfolio▸featureTestEffort', t), self.memoize('productPortfolio▸featuresInTest', t) ) ),
  	
  		'productPortfolio▸frcsReset': lambda t : max( 0, ( self.memoize('productPortfolio▸featureReleaseCompletionStatus', t) ) / dt if self.memoize('productPortfolio▸featureReleaseLaunchPolicy', t) == 1 else 0 ),
  	
  		'productPortfolio▸timePassing': lambda t : 1,
  	
  		'resources▸customerServiceIn': lambda t : max( 0, self.memoize('policy▸growthOn', t) * max( self.memoize('resources▸customerServiceResourceGap', t), 0 ) / self.memoize('resources▸hiringTime', t) ),
  	
  		'resources▸customerServiceOut': lambda t : max( 0, self.memoize('policy▸growthOn', t) * ( -1 ) * min( self.memoize('resources▸customerServiceResourceGap', t), 0 ) / self.memoize('resources▸leavingTime', t) ),
  	
  		'resources▸producDeveloperIn': lambda t : max( 0, self.memoize('policy▸growthOn', t) * self.memoize('resources▸productDeveloperGap', t) / self.memoize('resources▸hiringTime', t) ),
  	
  		'resources▸productDesignerIn': lambda t : max( 0, self.memoize('policy▸growthOn', t) * self.memoize('resources▸productDesignerGap', t) / self.memoize('resources▸hiringTime', t) ),
  	
  		'resources▸productTesterIn': lambda t : max( 0, self.memoize('policy▸growthOn', t) * self.memoize('resources▸productTesterGap', t) / self.memoize('resources▸hiringTime', t) ),
  	
  		'revenue▸defaults': lambda t : self.memoize('revenue▸receivables', t) * self.memoize('revenue▸defaultPercentage', t) / 100,
  	
  		'revenue▸receivablesIn': lambda t : max( 0, self.memoize('revenue▸revenue', t) ),
  	
  		'revenue▸receivablesOut': lambda t : max( 0, 0  if t - self.starttime < self.memoize('revenue▸collectionTime', t) else self.memoize('revenue▸receivablesIn', ( t - (self.memoize('revenue▸collectionTime', t)) )) * ( 100 - self.memoize('revenue▸defaultPercentage', ( t - (self.memoize('revenue▸collectionTime', t)) )) ) / 100 ),
  	
  		'revenue▸revenueIn': lambda t : max( 0, self.memoize('revenue▸revenue', t) ),
  	
  		'revenue▸yearlyRevenueReset': lambda t : max( 0, self.memoize('revenue▸revenueYtd', t)/ dt if 13 <= t and ((t -13) % 12) == 0 else 0 ),
  	
  		'taxes▸newPayments': lambda t : max( 0, self.memoize('taxes▸taxesBecomingDue', t) / self.memoize('taxes▸paymentPeriods', t) ),
  	
  		'taxes▸payingForTax': lambda t : max( 0, min( self.memoize('taxes▸taxPayment', t), self.memoize('taxes▸taxesDue', t) ) ),
  	
  		'taxes▸paymentBeingMade': lambda t : max( 0, 0  if t - self.starttime < self.memoize('taxes▸paymentPeriods', t) else self.memoize('taxes▸newPayments', ( t - (self.memoize('taxes▸paymentPeriods', t)) )) ),
  	
  		'taxes▸taxProvisionsIn': lambda t : max( 0, self.memoize('taxes▸yearlyIncomeTax', t)/ dt if 13 <= t and ((t -13) % 12) == 0 else 0 ),
  	
  		'taxes▸taxesBecomingDue': lambda t : max( 0, 0  if t - self.starttime < self.memoize('taxes▸averageTimeBeforeTaxesBecomeDue', t) else self.memoize('taxes▸taxProvisionsIn', ( t - (self.memoize('taxes▸averageTimeBeforeTaxesBecomeDue', t)) )) ),
  		# converters 
  		'assets▸assets': lambda t : self.memoize('revenue▸receivables', t) + self.memoize('cash▸cash', t),

  		'balance▸balance': lambda t : self.memoize('assets▸assets', t) - self.memoize('balance▸totalLiabilitiesAndEquity', t),

  		'balance▸debtEquityRatio': lambda t : self.memoize('liabilities▸liabilities', t) / self.memoize('equity▸equity', t),

  		'balance▸returnOnInvestment': lambda t : 100 * self.memoize('earnings▸profitAfterTaxYtd', t) / self.memoize('balance▸totalLiabilitiesAndEquity', t),

  		'balance▸totalLiabilitiesAndEquity': lambda t : self.memoize('liabilities▸liabilities', t) + self.memoize('equity▸equity', t),

  		'capabilities▸workforceCapabilityPct': lambda t : self.memoize('capabilities▸learningCurve', t),

  		'capabilities▸workforceExperience': lambda t : self.memoize('capabilities▸totalWorkforceExperience', t) / self.memoize('resources▸employees', t),

  		'cash▸bankAccount': lambda t : self.memoize('cash▸cash', t) - self.memoize('debt▸debt', t),

  		'cash▸cashFlow': lambda t : self.memoize('cash▸cashIn', t) + self.memoize('cash▸cashFromBorrowing', t) - self.memoize('cash▸cashOut', t),

  		'cash▸cashGap': lambda t : max( self.memoize('cash▸desiredCash', t) - self.memoize('cash▸cash', t), 0 ),

  		'cash▸cashPayments': lambda t : self.memoize('cost▸payablesOut', t) + self.memoize('debt▸debtAmortization', t) + self.memoize('taxes▸payingForTax', t) + self.memoize('cost▸wages', t),

  		'cash▸desiredCash': lambda t : self.memoize('cash▸cashPayments', t) * self.memoize('cash▸desiredMothsOfCoverage', t) * self.memoize('policy▸debtPolicy', t),

  		'cash▸excessCash': lambda t : self.memoize('cash▸cashIn', t) + self.memoize('cash▸cashFromBorrowing', t) - self.memoize('cash▸cashPayments', t),

  		'cashFlow▸cashFlow': lambda t : self.memoize('cashFlow▸financingCashFlow', t) - self.memoize('cashFlow▸investmentCashFlow', t) + self.memoize('cashFlow▸operatingCashFlow', t),

  		'cashFlow▸cashFlowBalance': lambda t : self.memoize('cashFlow▸cashFlow', t) - self.memoize('cash▸cashFlow', t),

  		'cashFlow▸financingCashFlow': lambda t : self.memoize('debt▸netIncreaseInDebt', t),

  		'cashFlow▸operatingCashFlow': lambda t : self.memoize('earnings▸profitBeforeTax', t) + 0 + self.memoize('cost▸netIncreaseInPayables', t) - self.memoize('revenue▸netIncreaseInReceivables', t) - self.memoize('taxes▸payingForTax', t),

  		'cost▸cashExpenses': lambda t : self.memoize('cost▸workplaceCost', t) + self.memoize('cost▸wages', t) + self.memoize('customers▸effectiveMarketingBudget', t) + self.memoize('debt▸interestOnDebt', t) + self.memoize('cost▸serviceCost', t),

  		'cost▸customerServiceWages': lambda t : self.memoize('resources▸customerService', t) * self.memoize('cost▸customerServiceWage', t),

  		'cost▸expenses': lambda t : self.memoize('cost▸nonCashExpenses', t) + self.memoize('cost▸cashExpenses', t),

  		'cost▸infrastructureCost': lambda t : self.memoize('customers▸customers', t) * self.memoize('cost▸infrastructureCostPerCustomer', t),

  		'cost▸marketingWages': lambda t : self.memoize('resources▸marketing', t) * self.memoize('cost▸marketingWage', t),

  		'cost▸mdWages': lambda t : self.memoize('cost▸mdWage', t) * self.memoize('resources▸managingDirectors', t),

  		'cost▸netIncreaseInPayables': lambda t : self.memoize('cost▸payablesIn', t) - self.memoize('cost▸payablesOut', t),

  		'cost▸nonCashExpenses': lambda t : self.memoize('cost▸equipmentDepreciation', t) + self.memoize('revenue▸defaults', t),

  		'cost▸paymentProviderCost': lambda t : self.memoize('customers▸customers', t) * self.memoize('cost▸paymentTransactionCost', t),

  		'cost▸productDevelopmentWages': lambda t : self.memoize('resources▸productDevelopmentHeadcount', t) * self.memoize('cost▸productDevelopmentWage', t),

  		'cost▸serviceCost': lambda t : self.memoize('cost▸paymentProviderCost', t) + self.memoize('cost▸infrastructureCost', t),

  		'cost▸wages': lambda t : self.memoize('cost▸customerServiceWages', t) + self.memoize('cost▸marketingWages', t) + self.memoize('cost▸productDevelopmentWages', t) + self.memoize('cost▸mdWages', t),

  		'cost▸workplaceCost': lambda t : self.memoize('cost▸workplaceCostPerEmployee', t) * self.memoize('resources▸employees', t),

  		'customers▸acquisitionThroughMarketing': lambda t : self.memoize('customers▸potentialCustomersReachedThroughMarketing', t) * self.memoize('customers▸marketingSuccessPct', t) / 100,

  		'customers▸acquisitionThroughWordOfMouth': lambda t : self.memoize('customers▸potentialCustomersReachedThroughWordOfMouth', t) * self.memoize('customers▸wordOfMouthSuccessPct', t) / 100,

  		'customers▸customerServiceRequests': lambda t : self.memoize('customers▸customerServiceRequestsPerCustomer', t) * self.memoize('customers▸payingCustomers', t),

  		'customers▸effectiveMarketingBudget': lambda t : self.memoize('customers▸dynamicMarketBudget', t),

  		'customers▸indicatedMktBudget': lambda t : self.memoize('customers▸marketingBudget', t) if self.memoize('policy▸sophisticatedMarketingBudgetPolicy', t) == 0 else self.memoize('customers▸potentialMktBudget', t),

  		'customers▸market': lambda t : self.memoize('customers▸customers', t) + self.memoize('customers▸potentialCustomers', t),

  		'customers▸marketSaturationPct': lambda t : 100 * self.memoize('customers▸customers', t) / self.memoize('customers▸market', t),

  		'customers▸payingCustomers': lambda t : self.memoize('customers▸customers', t) * self.memoize('customers▸payingCustomerPct', t) / 100,

  		'customers▸potentialCustomersReachedThroughMarketing': lambda t : self.memoize('customers▸personsReachedPerEuro', t) * self.memoize('customers▸effectiveMarketingBudget', t) * self.memoize('customers▸targetCustomerDilutionPct', t) / 100 * ( 1 - self.memoize('customers▸marketSaturationPct', t) / 100 ),

  		'customers▸potentialCustomersReachedThroughWordOfMouth': lambda t : self.memoize('customers▸wordOfMouthContactRate', t) * self.memoize('customers▸customers', t) * ( 1 - self.memoize('customers▸marketSaturationPct', t) / 100 ),

  		'customers▸potentialMktBudget': lambda t : max( ( self.memoize('cash▸cash', t) - self.memoize('customers▸desiredMinimumCashLevel', t) ) + self.memoize('cash▸excessCash', t), 0 ),

  		'customers▸targetMarketingBudget': lambda t : self.memoize('customers▸indicatedMktBudget', t) - self.memoize('customers▸dynamicMarketBudget', t),

  		'debt▸cashBorrowed': lambda t : self.memoize('cash▸cashGap', t) * self.memoize('debt▸fractionBorrowed', t),

  		'debt▸debtAmortization': lambda t : self.memoize('debt▸debtOut', t) + self.memoize('debt▸interestOnDebt', t),

  		'debt▸netIncreaseInDebt': lambda t : self.memoize('debt▸debtIn', t) - self.memoize('debt▸debtOut', t),

  		'debt▸numberOfRepaymentPeriods': lambda t : 5 * 12,

  		'earnings▸profitAfterTaxYtd': lambda t : self.memoize('earnings▸profitBeforeTaxYtd', t) - self.memoize('taxes▸yearlyIncomeTax', t),

  		'earnings▸profitBeforeTax': lambda t : self.memoize('revenue▸revenue', t) - self.memoize('cost▸expenses', t),

  		'earnings▸profitBeforeTaxYtd': lambda t : self.memoize('revenue▸revenueYtd', t) - self.memoize('cost▸expensesYtd', t),

  		'equity▸equity': lambda t : self.memoize('equity▸stock', t) + self.memoize('taxes▸provisionsForTax', t) + self.memoize('earnings▸earnings', t) + self.memoize('earnings▸profitBeforeTaxYtd', t),

  		'liabilities▸liabilities': lambda t : self.memoize('debt▸debt', t) + self.memoize('taxes▸taxesDue', t) + self.memoize('cost▸payables', t),

  		'productPortfolio▸featureAcceptanceRate': lambda t : min( self.memoize('productPortfolio▸targetFeatureQualificationRate', t), self.memoize('productPortfolio▸maximumFeatureQualificationRate', t) ) * self.memoize('productPortfolio▸featureAcceptancePct', t) / 100,

  		'productPortfolio▸featureCompleteTarget': lambda t : self.memoize('productPortfolio▸featureDevelopmentTarget', t) * self.memoize('productPortfolio▸featureReleaseTime2marketTarget', t) * self.memoize('productPortfolio▸featureCompleteTargetPct', t) / 100,

  		'productPortfolio▸featureDevelopmentPolicy': lambda t : self.memoize('productPortfolio▸featureIdeas', t) / self.memoize('productPortfolio▸featureReleaseTime2marketTarget', t),

  		'productPortfolio▸featureDevelopmentTarget': lambda t : self.memoize('policy▸learnFromCustomerOn', t) * self.memoize('productPortfolio▸featureDevelopmentPolicy', t) + ( 1 - self.memoize('policy▸learnFromCustomerOn', t) ) * self.memoize('productPortfolio▸constantFeatureDevelopmentTarget', t),

  		'productPortfolio▸featureDismissalRate': lambda t : self.memoize('productPortfolio▸featureAcceptanceRate', t) * ( 100 - self.memoize('productPortfolio▸featureAcceptancePct', t) ) / self.memoize('productPortfolio▸featureAcceptancePct', t),

  		'productPortfolio▸featureIdeasFromCustomers': lambda t : self.memoize('customers▸customerServiceRequests', t) * self.memoize('productPortfolio▸customerFeatureRequestPct', t) / 100,

  		'productPortfolio▸featureReleaseLaunchPolicy': lambda t : 1 if self.memoize('productPortfolio▸featureReleaseCompletionStatus', t) >= self.memoize('productPortfolio▸featureCompleteTarget', t) and self.memoize('productPortfolio▸timeSinceLastFeatureRelease', t) >= self.memoize('productPortfolio▸featureReleaseTime2marketTarget', t) else 0,

  		'productPortfolio▸featuresInPipeline': lambda t : self.memoize('productPortfolio▸featuresInDesign', t) + self.memoize('productPortfolio▸featuresInDevelopment', t) + self.memoize('productPortfolio▸featuresInTest', t),

  		'productPortfolio▸maximumFeatureQualificationRate': lambda t : min( self.memoize('resources▸featureQualificationCapacity', t) * self.memoize('productPortfolio▸featureIdeas', t) / self.memoize('productPortfolio▸featureQualificationEffort', t), self.memoize('productPortfolio▸featureIdeas', t) ),

  		'productPortfolio▸targetFeatureQualificationRate': lambda t : 100 * self.memoize('productPortfolio▸featureDevelopmentTarget', t) / self.memoize('productPortfolio▸featureAcceptancePct', t),

  		'resourceDemand▸customerServiceDemand': lambda t : self.memoize('resourceDemand▸nominalCustomerServiceDemand', t) / ( self.memoize('capabilities▸workforceCapabilityPct', t) / 100 ),

  		'resourceDemand▸customerServiceEffortPerIncident': lambda t : 10 / 60 / 8 / 21,

  		'resourceDemand▸demandForFeatureDesign': lambda t : self.memoize('productPortfolio▸featuresInDesign', t) * self.memoize('productPortfolio▸featureDesignEffort', t),

  		'resourceDemand▸demandForFeatureDesignPct': lambda t : 100 * self.memoize('resourceDemand▸demandForFeatureDesign', t) / self.memoize('resourceDemand▸nominalDemandForProductDesigners', t),

  		'resourceDemand▸demandForFeatureQualification': lambda t : self.memoize('productPortfolio▸featureQualificationEffort', t) * self.memoize('productPortfolio▸targetFeatureQualificationRate', t),

  		'resourceDemand▸demandForFeatureQualificationPct': lambda t : 100 * self.memoize('resourceDemand▸demandForFeatureQualification', t) / self.memoize('resourceDemand▸nominalDemandForProductDesigners', t),

  		'resourceDemand▸nominalCustomerServiceDemand': lambda t : self.memoize('customers▸customerServiceRequests', t) * self.memoize('resourceDemand▸customerServiceEffortPerIncident', t),

  		'resourceDemand▸nominalDemandForProductDesigners': lambda t : self.memoize('resourceDemand▸demandForFeatureDesign', t) + self.memoize('resourceDemand▸demandForFeatureQualification', t),

  		'resourceDemand▸nominalDemandForProductDevelopers': lambda t : self.memoize('productPortfolio▸featureDevelopmentEffort', t) * self.memoize('productPortfolio▸featuresInDevelopment', t),

  		'resourceDemand▸nominalDemandForProductTesters': lambda t : self.memoize('productPortfolio▸featuresInTest', t) * self.memoize('productPortfolio▸featureTestEffort', t),

  		'resourceDemand▸productDesignerDemand': lambda t : self.memoize('resourceDemand▸nominalDemandForProductDesigners', t) / ( self.memoize('capabilities▸workforceCapabilityPct', t) / 100 ),

  		'resourceDemand▸productDeveloperDemand': lambda t : self.memoize('resourceDemand▸nominalDemandForProductDevelopers', t) / ( self.memoize('capabilities▸workforceCapabilityPct', t) / 100 ),

  		'resourceDemand▸productTesterDemand': lambda t : self.memoize('resourceDemand▸nominalDemandForProductTesters', t) / ( self.memoize('capabilities▸workforceCapabilityPct', t) / 100 ),

  		'resources▸customerServiceResourceGap': lambda t : self.memoize('resourceDemand▸customerServiceDemand', t) - self.memoize('resources▸customerService', t),

  		'resources▸employees': lambda t : self.memoize('resources▸customerService', t) + self.memoize('resources▸marketing', t) + self.memoize('resources▸productDevelopmentHeadcount', t) + self.memoize('resources▸managingDirectors', t),

  		'resources▸employeesHired': lambda t : self.memoize('resources▸customerServiceIn', t) + self.memoize('resources▸productDesignerIn', t) + self.memoize('resources▸producDeveloperIn', t) + self.memoize('resources▸productTesterIn', t),

  		'resources▸employeesLost': lambda t : self.memoize('resources▸customerServiceOut', t),

  		'resources▸featureDesignCapacity': lambda t : self.memoize('resources▸productDesignerCapacity', t) * self.memoize('resourceDemand▸demandForFeatureDesignPct', t) / 100,

  		'resources▸featureDevelopmentCapacity': lambda t : self.memoize('resources▸productDeveloperCapacity', t),

  		'resources▸featureQualificationCapacity': lambda t : self.memoize('resources▸productDesignerCapacity', t) * self.memoize('resourceDemand▸demandForFeatureQualificationPct', t) / 100,

  		'resources▸featureTestCapacity': lambda t : self.memoize('resources▸productTesterCapacity', t),

  		'resources▸initialEmployees': lambda t : self.memoize('resources▸initialCustomerService', t) + self.memoize('resources▸initialMarketing', t) + self.memoize('resources▸initialProductDevelopment', t),

  		'resources▸initialProductDevelopment': lambda t : self.memoize('resources▸initialProductDevelopers', t) + self.memoize('resources▸initialProductDesigner', t) + self.memoize('resources▸initialProductTester', t),

  		'resources▸productDesignerCapacity': lambda t : self.memoize('resources▸productDesigner', t) * self.memoize('resources▸worktime', t),

  		'resources▸productDesignerGap': lambda t : max( self.memoize('resourceDemand▸productDesignerDemand', t) - self.memoize('resources▸productDesignerCapacity', t), 0 ) / self.memoize('resources▸worktime', t),

  		'resources▸productDeveloperCapacity': lambda t : self.memoize('resources▸productDeveloper', t) * self.memoize('resources▸worktime', t),

  		'resources▸productDeveloperGap': lambda t : max( self.memoize('resourceDemand▸productDeveloperDemand', t) - self.memoize('resources▸productDeveloperCapacity', t), 0 ) / self.memoize('resources▸worktime', t),

  		'resources▸productDevelopmentHeadcount': lambda t : self.memoize('resources▸productDesigner', t) + self.memoize('resources▸productDeveloper', t) + self.memoize('resources▸productTester', t),

  		'resources▸productTesterCapacity': lambda t : self.memoize('resources▸productTester', t) * self.memoize('resources▸worktime', t),

  		'resources▸productTesterGap': lambda t : max( self.memoize('resourceDemand▸productTesterDemand', t) - self.memoize('resources▸productTesterCapacity', t), 0 ) / self.memoize('resources▸worktime', t),

  		'revenue▸netIncreaseInReceivables': lambda t : self.memoize('revenue▸receivablesIn', t) - self.memoize('revenue▸receivablesOut', t) - self.memoize('revenue▸defaults', t),

  		'revenue▸revenue': lambda t : self.memoize('productPortfolio▸serviceFee', t) * self.memoize('customers▸payingCustomers', t),

  		'taxes▸yearlyIncomeTax': lambda t : ( self.memoize('taxes▸incomeTaxRatePct', t) / 100 ) * max( ( self.memoize('earnings▸profitBeforeTaxYtd', t) + min( self.memoize('earnings▸earnings', t), 0 ) ), 0 ),
    # gf 
  		'capabilities▸learningCurve': lambda t : LERP(min( self.memoize('capabilities▸workforceExperience', t), 12 ),self.points['capabilities▸learningCurve']),
    #constants
  		'cash▸desiredMothsOfCoverage': lambda t : 2
      ,
  		'cashFlow▸investmentCashFlow': lambda t : 0
      ,
  		'cost▸customerServiceWage': lambda t : 3000
      ,
  		'cost▸equipmentDepreciation': lambda t : 0
      ,
  		'cost▸infrastructureCostPerCustomer': lambda t : 3
      ,
  		'cost▸marketingWage': lambda t : 3000
      ,
  		'cost▸mdWage': lambda t : 6000
      ,
  		'cost▸paymentTime': lambda t : 1
      ,
  		'cost▸paymentTransactionCost': lambda t : 0.2
      ,
  		'cost▸productDevelopmentWage': lambda t : 3000
      ,
  		'cost▸workplaceCostPerEmployee': lambda t : 500
      ,
  		'customers▸customerServiceRequestsPerCustomer': lambda t : 1
      ,
  		'customers▸desiredMinimumCashLevel': lambda t : 70000
      ,
  		'customers▸marketingBudget': lambda t : 10000
      ,
  		'customers▸marketingSuccessPct': lambda t : 0.01
      ,
  		'customers▸payingCustomerPct': lambda t : 100
      ,
  		'customers▸personsReachedPerEuro': lambda t : 100
      ,
  		'customers▸targetCustomerDilutionPct': lambda t : 100
      ,
  		'customers▸timeToAdjustDynamicMktBudget': lambda t : 1
      ,
  		'customers▸wordOfMouthContactRate': lambda t : 15
      ,
  		'customers▸wordOfMouthSuccessPct': lambda t : 0.05
      ,
  		'debt▸fractionBorrowed': lambda t : 1
      ,
  		'debt▸initialDebt': lambda t : 0
      ,
  		'debt▸yearlyInterestOnDebtPct': lambda t : 5
      ,
  		'equity▸initialShareholderStock': lambda t : 500000
      ,
  		'policy▸debtPolicy': lambda t : 0
      ,
  		'policy▸growthOn': lambda t : 1
      ,
  		'policy▸learnFromCustomerOn': lambda t : 0
      ,
  		'policy▸sophisticatedMarketingBudgetPolicy': lambda t : 1
      ,
  		'productPortfolio▸constantFeatureDevelopmentTarget': lambda t : 1
      ,
  		'productPortfolio▸customerFeatureRequestPct': lambda t : 1
      ,
  		'productPortfolio▸featureAcceptancePct': lambda t : 100
      ,
  		'productPortfolio▸featureCompleteTargetPct': lambda t : 100
      ,
  		'productPortfolio▸featureDesignEffort': lambda t : 0.5
      ,
  		'productPortfolio▸featureDevelopmentEffort': lambda t : 1
      ,
  		'productPortfolio▸featureQualificationEffort': lambda t : 0.5
      ,
  		'productPortfolio▸featureReleaseTime2marketTarget': lambda t : 6
      ,
  		'productPortfolio▸featureTestEffort': lambda t : 1
      ,
  		'productPortfolio▸serviceFee': lambda t : 20
      ,
  		'resources▸hiringTime': lambda t : 3
      ,
  		'resources▸initialCustomerService': lambda t : 2
      ,
  		'resources▸initialMarketing': lambda t : 0
      ,
  		'resources▸initialProductDesigner': lambda t : 1
      ,
  		'resources▸initialProductDevelopers': lambda t : 1
      ,
  		'resources▸initialProductTester': lambda t : 1
      ,
  		'resources▸leavingTime': lambda t : 12
      ,
  		'resources▸worktime': lambda t : 1
      ,
  		'revenue▸collectionTime': lambda t : 2
      ,
  		'revenue▸defaultPercentage': lambda t : 0
      ,
  		'taxes▸averageTimeBeforeTaxesBecomeDue': lambda t : 6
      ,
  		'taxes▸incomeTaxRatePct': lambda t : 30
      ,
  		'taxes▸paymentPeriods': lambda t : 12
      ,
    }

    self.points = {
  		'capabilities▸learningCurve': [ [0,30],[1,30],[2,32.9893238434164],[3,38.7188612099644],[4,47.4377224199288],[5,90],[6,96.7615658362989],[7,98.2562277580071],[8,100],[9,100],[10,100],[11,100],[12,100] ],
  	 }

    self.dimensions = {
  		'Subscript_Set_1': {
  			'labels': [ '1' ],
  			'variables': [  ]
  		},
  	 }

    self.stocks = ['capabilities▸totalWorkforceExperience','cash▸cash','cashFlow▸cashFlowYtd','cashFlow▸financingCashFlowYtd','cashFlow▸investmentCashFlowYtd','cashFlow▸operatingCashFlowYtd','cost▸cashExpensesYtd','cost▸expensesYtd','cost▸interestOnDebtYtd','cost▸marketingCostsYtd','cost▸nonCashExpensesYtd','cost▸payables','cost▸serviceCostsYtd','cost▸wagesYtd','cost▸workplaceCostYtd','customers▸customers','customers▸dynamicMarketBudget','customers▸marketingCustomers','customers▸potentialCustomers','customers▸wordOfMouthCustomers','debt▸debt','debt▸debtRepayments','debt▸interestOnDebt','debt▸interestReductionAmount','earnings▸earnings','equity▸stock','productPortfolio▸featureIdeas','productPortfolio▸featureReleaseCompletionStatus','productPortfolio▸featuresInDesign','productPortfolio▸featuresInDevelopment','productPortfolio▸featuresInLaunch','productPortfolio▸featuresInTest','productPortfolio▸timeSinceLastFeatureRelease','resources▸customerService','resources▸managingDirectors','resources▸marketing','resources▸productDesigner','resources▸productDeveloper','resources▸productTester','revenue▸receivables','revenue▸revenueYtd','taxes▸provisionsForTax','taxes▸taxPayment','taxes▸taxesDue']
    self.flows = ['capabilities▸gainingExperience','capabilities▸losingExperience','cash▸cashFromBorrowing','cash▸cashIn','cash▸cashOut','cashFlow▸cashFlowIn','cashFlow▸cashFlowReset','cashFlow▸financingCashFlowIn','cashFlow▸financingCashFlowReset','cashFlow▸investmentCashFlowIn','cashFlow▸investmentCashFlowReset','cashFlow▸operatingCashFlowIn','cashFlow▸operatingCashFlowReset','cost▸cashExpensesIn','cost▸cashExpensesReset','cost▸expensesIs','cost▸interestDebtIn','cost▸interestDebtReset','cost▸monthlyMarketingCost','cost▸monthlyServiceCost','cost▸monthlyWages','cost▸monthlyWorkplaceCosts','cost▸nonCashExpensesIn','cost▸nonCashExpensesReset','cost▸payablesIn','cost▸payablesOut','cost▸yearlyExpensesReset','cost▸yearlyMarketingCostReset','cost▸yearlyServiceCostReset','cost▸yearlyWageReset','cost▸yearlyWorkplaceCostReset','customers▸advCustIn','customers▸customerAcquisition','customers▸dynamicMarketBudgetRateOfChange','customers▸womCustIn','debt▸debtIn','debt▸debtOut','debt▸interestIn','debt▸interestOut','debt▸interestReductionIn','debt▸interestReductionOut','debt▸repaymentsIn','debt▸repaymentsOut','earnings▸yearlyEarnings','productPortfolio▸featureIdeasDocumented','productPortfolio▸featureReleaseTimerReset','productPortfolio▸featuresAccepted','productPortfolio▸featuresCompleted','productPortfolio▸featuresDesigned','productPortfolio▸featuresDeveloped','productPortfolio▸featuresDismissed','productPortfolio▸featuresLaunched','productPortfolio▸featuresTested','productPortfolio▸frcsReset','productPortfolio▸timePassing','resources▸customerServiceIn','resources▸customerServiceOut','resources▸producDeveloperIn','resources▸productDesignerIn','resources▸productTesterIn','revenue▸defaults','revenue▸receivablesIn','revenue▸receivablesOut','revenue▸revenueIn','revenue▸yearlyRevenueReset','taxes▸newPayments','taxes▸payingForTax','taxes▸paymentBeingMade','taxes▸taxProvisionsIn','taxes▸taxesBecomingDue']
    self.converters = ['assets▸assets','balance▸balance','balance▸debtEquityRatio','balance▸returnOnInvestment','balance▸totalLiabilitiesAndEquity','capabilities▸workforceCapabilityPct','capabilities▸workforceExperience','cash▸bankAccount','cash▸cashFlow','cash▸cashGap','cash▸cashPayments','cash▸desiredCash','cash▸excessCash','cashFlow▸cashFlow','cashFlow▸cashFlowBalance','cashFlow▸financingCashFlow','cashFlow▸operatingCashFlow','cost▸cashExpenses','cost▸customerServiceWages','cost▸expenses','cost▸infrastructureCost','cost▸marketingWages','cost▸mdWages','cost▸netIncreaseInPayables','cost▸nonCashExpenses','cost▸paymentProviderCost','cost▸productDevelopmentWages','cost▸serviceCost','cost▸wages','cost▸workplaceCost','customers▸acquisitionThroughMarketing','customers▸acquisitionThroughWordOfMouth','customers▸customerServiceRequests','customers▸effectiveMarketingBudget','customers▸indicatedMktBudget','customers▸market','customers▸marketSaturationPct','customers▸payingCustomers','customers▸potentialCustomersReachedThroughMarketing','customers▸potentialCustomersReachedThroughWordOfMouth','customers▸potentialMktBudget','customers▸targetMarketingBudget','debt▸cashBorrowed','debt▸debtAmortization','debt▸netIncreaseInDebt','debt▸numberOfRepaymentPeriods','earnings▸profitAfterTaxYtd','earnings▸profitBeforeTax','earnings▸profitBeforeTaxYtd','equity▸equity','liabilities▸liabilities','productPortfolio▸featureAcceptanceRate','productPortfolio▸featureCompleteTarget','productPortfolio▸featureDevelopmentPolicy','productPortfolio▸featureDevelopmentTarget','productPortfolio▸featureDismissalRate','productPortfolio▸featureIdeasFromCustomers','productPortfolio▸featureReleaseLaunchPolicy','productPortfolio▸featuresInPipeline','productPortfolio▸maximumFeatureQualificationRate','productPortfolio▸targetFeatureQualificationRate','resourceDemand▸customerServiceDemand','resourceDemand▸customerServiceEffortPerIncident','resourceDemand▸demandForFeatureDesign','resourceDemand▸demandForFeatureDesignPct','resourceDemand▸demandForFeatureQualification','resourceDemand▸demandForFeatureQualificationPct','resourceDemand▸nominalCustomerServiceDemand','resourceDemand▸nominalDemandForProductDesigners','resourceDemand▸nominalDemandForProductDevelopers','resourceDemand▸nominalDemandForProductTesters','resourceDemand▸productDesignerDemand','resourceDemand▸productDeveloperDemand','resourceDemand▸productTesterDemand','resources▸customerServiceResourceGap','resources▸employees','resources▸employeesHired','resources▸employeesLost','resources▸featureDesignCapacity','resources▸featureDevelopmentCapacity','resources▸featureQualificationCapacity','resources▸featureTestCapacity','resources▸initialEmployees','resources▸initialProductDevelopment','resources▸productDesignerCapacity','resources▸productDesignerGap','resources▸productDeveloperCapacity','resources▸productDeveloperGap','resources▸productDevelopmentHeadcount','resources▸productTesterCapacity','resources▸productTesterGap','revenue▸netIncreaseInReceivables','revenue▸revenue','taxes▸yearlyIncomeTax']
    self.gf = ['capabilities▸learningCurve']
    self.constants= ['cash▸desiredMothsOfCoverage','cashFlow▸investmentCashFlow','cost▸customerServiceWage','cost▸equipmentDepreciation','cost▸infrastructureCostPerCustomer','cost▸marketingWage','cost▸mdWage','cost▸paymentTime','cost▸paymentTransactionCost','cost▸productDevelopmentWage','cost▸workplaceCostPerEmployee','customers▸customerServiceRequestsPerCustomer','customers▸desiredMinimumCashLevel','customers▸marketingBudget','customers▸marketingSuccessPct','customers▸payingCustomerPct','customers▸personsReachedPerEuro','customers▸targetCustomerDilutionPct','customers▸timeToAdjustDynamicMktBudget','customers▸wordOfMouthContactRate','customers▸wordOfMouthSuccessPct','debt▸fractionBorrowed','debt▸initialDebt','debt▸yearlyInterestOnDebtPct','equity▸initialShareholderStock','policy▸debtPolicy','policy▸growthOn','policy▸learnFromCustomerOn','policy▸sophisticatedMarketingBudgetPolicy','productPortfolio▸constantFeatureDevelopmentTarget','productPortfolio▸customerFeatureRequestPct','productPortfolio▸featureAcceptancePct','productPortfolio▸featureCompleteTargetPct','productPortfolio▸featureDesignEffort','productPortfolio▸featureDevelopmentEffort','productPortfolio▸featureQualificationEffort','productPortfolio▸featureReleaseTime2marketTarget','productPortfolio▸featureTestEffort','productPortfolio▸serviceFee','resources▸hiringTime','resources▸initialCustomerService','resources▸initialMarketing','resources▸initialProductDesigner','resources▸initialProductDevelopers','resources▸initialProductTester','resources▸leavingTime','resources▸worktime','revenue▸collectionTime','revenue▸defaultPercentage','taxes▸averageTimeBeforeTaxesBecomeDue','taxes▸incomeTaxRatePct','taxes▸paymentPeriods']
    self.events = [
    	]

    self.memo = {}
    for key in list(self.equations.keys()):
      self.memo[key] = {}  # DICT OF DICTS!

  def specs(self):
    return self.starttime, self.stoptime, self.dt, 'Months', 'Euler'

  def setDT(self,v):
    self.dt = v

  def setStarttime(self,v):
    self.starttime = v

  def setStoptime(self,v):
    self.stoptime = v

