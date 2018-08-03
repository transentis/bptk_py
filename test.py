#!/bin/python3
from BPTK_Py.bptk import bptk_wrapper as bptk
bptk = bptk()
#bptk.plotOutputsForScenario(scenario_name="MakeYourStartUpGrow", equations=['cashFlow.cashFlowYtd','cash.cash'],stacked=False, freq="D", start_date="1/11/2018",title="Multiple Equations for one Scenario\n",x_label="Time",y_label="S0m3 Number")
bptk.plotScenarioForOutput(scenario_names=["MakeYourStartUpGrow","MakeYourStartUpGrow_strategy"], equation="customers.marketingBudget",title="Multiple Equations for one Scenario\n",x_label="Time",y_label="S0m3 Number",strategy=True)

df =bptk.plotOutputsForScenario(scenario_name="MakeYourStartUpGrow_strategy", equations=["customers.marketingBudget"],title="Multiple Equations for one Scenario\n",x_label="Time",y_label="S0m3 Number",strategy=True, return_df=True)

#bptk.destroy()
#bptk.run_simulations_with_strategy(scenario_name="MakeYourStartUpGrow_strategy")['MakeYourStartUpGrow_strategy'].result
#df.to_csv("output.csv")

bptk.destroy()

