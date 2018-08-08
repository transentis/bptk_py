from BPTK_Py.bptk import bptk
from BPTK_Py.scenariomanager.scenario_manager_factory import ScenarioManagerFactory
import BPTK_Py.config.config as config
# C:\Users\dominik\Code\sd-compiler

factory = ScenarioManagerFactory()
#
managers = factory.get_scenario_managers(scenario_managers_to_filter=["ScenarioManager2"])

for key, manager in managers.items():
     print("")
     print("*** {} ***".format(key))

     for name in manager.get_scenario_names():
         print("\t {}".format(name))



#
# factory.reset_scenario("ScenarioManager1",scenario_name="MakeYourStartUpGrow")
# factory.destroy()



bptk= bptk()
bptk.scenario_manager_factory.reset_scenario(scenario_manager="ScenarioManager2",scenario_name="MakeYourStartUpGrow-x")
print(bptk.scenario_manager_factory.reset_all_scenarios())

bptk.plot_scenario_for_output(
    scenario_managers=["ScenarioManager2"],

    scenario_names=["MakeYourStartUpGrow_strategy", "MakeYourStartUpGrow"],
    kind="line",
    equation="cash.cash",
    stacked=False,
    strategy=True,
    freq="D",
    start_date="1/11/2017",
    title="Modified Lambda method as a \n Line Graph vs no modification",
    x_label="Time",
    y_label="Number",
)