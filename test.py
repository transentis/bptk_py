#!/bin/python3
from BPTK_Py.bptk import bptk_wrapper as bptk
bptk = bptk()
bptk.plotOutputsForScenario(scenario_name="MakeYourStartUpGrow", equations=['cashFlow.cashFlowYtd','cash.cash'],stacked=False, freq="D", start_date="1/11/2018",title="Multiple Equations for one Scenario\n",x_label="Time",y_label="S0m3 Number")
bptk.plotScenarioForOutput(scenario_names=["MakeYourStartUpGrow","MakeYourStartUpGrow_strategy"], equation="customers.marketingBudget",title="Multiple Equations for one Scenario\n",x_label="Time",y_label="S0m3 Number",strategy=True)

df =bptk.plotOutputsForScenario(scenario_name="MakeYourStartUpGrow_strategy", equations=["customers.marketingBudget"],title="Multiple Equations for one Scenario\n",x_label="Time",y_label="S0m3 Number",strategy=True, return_df=True)

from BPTK_Py.scenario_manager.scenario_manager import scenarioManager
scenarioManager = scenarioManager()
scenarioManager.printAvailableScenarios()

print(df)
bptk.destroy() ## <--Should quit the execution

scenarios = {
    1: {
        "name": "Scenario1",
        "from": 1,
        "to": 100,
        "dt": 1,
        "source": "simulation_models/make_your_startup_grow.itmx",
        "model": "simulation_models/model",

        "constants": {
            "cost.paymentTransactionCost": 0.75,
            "cost.productDevelopmentWage": 15000
        },

        "equationsToSimulate": [
            "cash.cash",
            "cashFlow.cashFlowYtd"
        ],

        "strategy": {
            "1": {
                "cost.paymentTransactionCost": 0.4,
                "customers.marketingBudget": 10000
            },
        }

    },
    2: {
        "name": "Scenario2",
        "from": 1,
        "to": 100,
        "dt": 1,
        "source": "simulation_models/make_your_startup_grow.itmx",
        "model": "simulation_models/model",

        "constants": {
            "cost.paymentTransactionCost": 0.75,
            "cost.productDevelopmentWage": 8700
        },

        "equationsToSimulate": [
            "cash.cash",
            "cashFlow.cashFlowYtd"
        ],

        "strategy": {
            "12": {
                "cost.paymentTransactionCost": 0.4,
                "customers.marketingBudget": 6500
            },
        }

    }
}

print(scenarios)