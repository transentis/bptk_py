#!/bin/python3
from BPTK_Py.bptk import bptk_wrapper as bptk
bptk_wrapper = bptk()
bptk_wrapper.plotOutputsForScenario(scenario_name="MakeYouStartUpGrow", equations=['cashFlow.cashFlowYtd','cash.cash'],stacked=False, freq="D", start_date="1/11/2018",title="Multiple Equations for one Scenario\n",x_label="Time",y_label="S0m3 Number")
