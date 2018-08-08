from BPTK_Py.bptk import bptk
from BPTK_Py.scenariomanager.scenario_manager_factory import ScenarioManagerFactory
import BPTK_Py.config.config as config
# C:\Users\dominik\Code\sd-compiler

factory = ScenarioManagerFactory()

managers = factory.get_available_scenarios()

for key, manager in managers.items():
    print("")
    print("*** {} ***".format(key))

    for name, scenario in manager.scenarios.items():
        print("\t {}".format(name))


factory.reset_scenario("ScenarioManager1",scenario_name="MakeYourStartUpGrow")
factory.destroy()