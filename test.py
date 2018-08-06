#!/bin/python3
from BPTK_Py.bptk import bptk as bptk
#bptk = bptk()
#bptk.plotOutputsForScenario(scenario_name="", equations=['cashFlow.cashFlowYtd','cash.cash'],stacked=False, freq="D", start_date="1/11/2018",title="Multiple Equations for one Scenario\n",x_label="Time",y_label="S0m3 Number")
#bptk.plotScenarioForOutput(scenario_names=["MakeYourStartUpGrow","MakeYourStartUpGrow_strategy"], equation="customers.marketingBudget",title="Multiple Equations for one Scenario\n",x_label="Time",y_label="S0m3 Number",strategy=True)

#df =bptk.plotOutputsForScenario(scenario_name="MakeYourStartUpGrow_strategy", equations=["customers.marketingBudget"],title="Multiple Equations for one Scenario\n",x_label="Time",y_label="S0m3 Number",strategy=True, return_df=True)

from BPTK_Py.scenario_manager.scenario_manager import scenarioManager
scenarioManager = scenarioManager()
#scenarioManager.printAvailableScenarios()
print(scenarioManager.getAvailableScenarios()['MakeYourStartUpGrow_strategy'].dictionary)

#print(df)
#bptk.destroy() ## <--Should quit the execution

# bptk.plotScenarioForOutput(
#     scenario_names=["MakeYourStartUpGrow_2","MakeYourStartUpGrow"],
#     equation="cashFlow.cashFlowYtd",
#     stacked=False,
#     freq="M",
#     start_date="1/11/2017",
#     title="One Equation for multiple Scenarios",
#     x_label="Time",
#     y_label="Dollars",
#     series_names=["CashFlow1","CashFlow2"]
# )