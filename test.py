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


bptk = bptk()
bptk.scenario_manager_factory.reset_scenario(scenario_manager="ScenarioManager2", scenario_name="MakeYourStartUpGrow-x")


scenarios = bptk.scenario_manager_factory.get_scenarios(
    scenario_names=["MakeYourStartUpGrow_strategy", "MakeYourStartUpGrow"], scenario_managers=["ScenarioManager2"])

from BPTK_Py.widgetdecorator.widget_manager import widgetFactory

widget_gen = widgetFactory(bptk)

config.configuration["log_modes"]= [""]

widget_gen.generate_widget(scenario_managers=["ScenarioManager1"],

                           scenario_names=["MakeYourStartUpGrow_strategy", "MakeYourStartUpGrow"],
                           kind="line",
                           equations=["cash.cash"],
                           stacked=False,
                           strategy=True,
                           freq="D",
                           start_date="1/11/2017",
                           title="Modified Lambda method as a \n Line Graph vs no modification",
                           x_label="Time",
                           y_label="Number",
                           constant= "cash.cash", interval=(0,100)
                           )

bptk.destroy()
