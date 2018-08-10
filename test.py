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

from BPTK_Py.widgetdecorator.widget_decorator import widgetDecorator

widget_gen = widgetDecorator(bptk)

config.configuration["log_modes"]= [""]

bptk.plot_with_sliders(scenario_managers=["ScenarioManager1"],

                                scenario_names=["MakeYourStartUpGrow_strategy"],
                                kind="line",
                                equations=["cash.cash"],
                                stacked=False,
                                strategy=True,
                                freq="D",
                                start_date="1/11/2017",
                                title="Interactive Plotting",
                                x_label="Date",
                                y_label="€",
                                constants=[("cost.paymentTransactionCost",0.0, 1.0),("customers.marketingBudget",0,1000000)]
                                )

bptk.destroy()
