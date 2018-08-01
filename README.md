# Business Prototyping Toolkit for Python
## Contents
1. [BPTK_Py](#BPTK_Py)

## BPTK_Py
BPTK_Py is the implementation of a simulation engine and plotting for Stela System Dynamics models. 
It requires a python-parsed version of the model containing the set of equations. We employ transentis' sdcc parser for this. An example model is available in [simulation_models/](simulation_models/)

An initial setup (that also employs the transentis color style) contains these lines:
```
import BPTK_Py.bptk as bptk
import BPTK_Py.config.config as config
import importlib
import matplotlib as plt
for key in config.matplotlib_rc_settings.keys():
    plt.rcParams[key] = config.matplotlib_rc_settings[key]
```

Override the style by modifying [BPTK_Py/config/config.py](BPTK_Py/config/config.py)

### Scenarios
You write scenarios in JSON format. Example:

```
{
  "constants": {
    "cost.paymentTransactionCost" : 0.5,
    "cost.productDevelopmentWage" : 10000
  },
  "name": "MakeYouStartUpGrow_2",
  "from": 1,
  "until": 100,
  "dt": 1,
  "model": "simulation_models/model",
  "equationsToSimulate": [
    "capabilities.totalWorkforceExperience",
    "cash.cash",
    "cashFlow.cashFlowYtd",
    "cashFlow.financingCashFlowYtd",
    "cashFlow.investmentCashFlowYtd",
    "cashFlow.operatingCashFlowYtd"
  ]
}
```
The ``constants`` list stores the overrides for the constants. The other fields are self-explaining. The ``equationsToSimulate`` contains equations that the simulator is supposed to simulate. In this way, you do not need to specify the equations to simulate in the API (just leave the ``equation(s)`` parameters empty then. It serves as a fallback if the equations are not specified in code.

### API calls
The ipython example notebook contains examples for the 



