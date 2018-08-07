from BPTK_Py.scenario_manager.scenario_manager import scenarioManager
from BPTK_Py.bptk import bptk
bptk = bptk()
from BPTK_Py.scenario_manager.scenario_manager import scenarioManager
scenarioManager = bptk.ScenarioManager
scenarioManager.get_scenario_managers()

bptk.plotOutputsForScenario(
    scenario_managers=["ScenarioManager2"],
    scenario_name="MakeYourStartUpGrow_stjhrategy",
    equations=['cashFlow.cashFlowYtd','cash.cash'],
    title="Multiple Equations for one Scenario\n",
    x_label="Time",
    y_label="S0m3 Number"
)

bptk.plotScenarioForOutput(scenario_names=["MakeYourStartUpGrow","MakeYourStartUpGrow_strategy"],
                           series_names=["Cashflow without strategy", "Cashflow with strategy"],
                           start_date="01-01-2017",
                           freq="M",
                           equation='cashFlow.cashFlowYtd',
                           title="Cashflow with and without strategy\n",
                           x_label="Time",y_label="Cashflow (USD)",strategy=True
                          )