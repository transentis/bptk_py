from BPTK_Py.bptk import bptk
from BPTK_Py.scenariomanager.scenario_manager import scenarioManager
import BPTK_Py.config.config as config
# C:\Users\dominik\Code\sd-compiler
config.configuration["sd_py_compiler_root"] = "C:\\Users\\dominik\\Code\\sd-compiler"  ## <--- Please change this path to the git repo of the sd_compiler package!

bptk = bptk()

bptk.plot_outputs_for_scenario(
    scenario_managers=["ScenarioManager2"],
    scenario_name="MakeYourStartUpGrow_stjhrategy",
    equations=['cashFlow.cashFlowYtd','cash.cash'],
    title="Multiple Equations for one Scenario\n",
    x_label="Time",
    y_label="S0m3 Number",
)