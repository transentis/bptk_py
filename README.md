# Business Prototyping Toolkit for Python
## Contents
1. [BPTK_Py](#BPTK_Py)

## BPTK_Py
BPTK_Py is the implementation of a simulation engine and plotting for Stela System Dynamics models. 
It requires a python-parsed version of the model containing the set of equations. We employ transentis' sdcc parser for this. An example model is available in [simulation_models/](simulation_models/)

An initial setup (that also employs the transentis color style) contains these lines:
```
from BPTK_Py.bptk import bptk_wrapper 
bptk = bptk_wrapper()
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
The ``constants`` list stores the overrides for the constants. The other fields are self-explaining. The only required field is the ``name``, the simulation will exit with an error if no name is given. The ``equationsToSimulate`` contains equations that the simulator is supposed to simulate. In this way, you do not need to specify the equations to simulate in the API (just leave the ``equation(s)`` parameters empty then. It serves as a fallback if the equations are not specified in code.

### API calls
The ipython example notebook contains examples for the API calls. For now, we use two methods:
```
bptk.plotOutputsForScenario(scenario_name, equations=[], kind=config.kind, alpha=config.alpha, stacked=config.stacked, freq="D", start_date="1/1/2018", title="", visualize_from_period=0, x_label="", y_label="",series_names=["names","name2"],return_df=False)

bptk.plotScenarioForOutput(scenario_names, equation, kind=config.kind, alpha=config.alpha, stacked=config.stacked, freq="D", start_date="1/1/2018", title="", visualize_from_period=0, x_label="", y_label="",series_names=["names","name2"],return_df=False):
```

The first, plots one or multiple equations for one scenario ("scenario_name"). The scenario name is the one specified in the scenario JSON file. The other parameters are optional. Always use Python's list notations for the plural parameters (``scenario_names / equations``).

* ``kind``: Kind of plot (area, line, bar, ...)
* ``alpha``: The alpha defines the opacity. Float 0.0 < alpha <= 1.0.
* ``freq``: Here we define the interval of the dates that we convert the ticks to. "D" means daily, "H" hourly, "M" monthly, "Y" annually and so on.
* ``start_date``: Date from which plot starts
* ``title``: Plot title
* ``visualize_from_period``: First index field to visualize from (in case we want to cut off the first x periods)
* ``x_label and y_label``: set the label names for the axis.
* ``series_names``: This optional parameter allows you to override the series names (in the order of the equations). Use Python's list notation: ``[ ]``. Without this parameter, BPTK will just use the equation and scenario names. If you have 3 equations and only specify one value in the list, will only modify the name of the first series. You may also use an empty string in the list to change the name of the second (or third..) series: ``[ "", "nameToChangeTo" ]`` 

## TODO
* Monitoring: We need to monitor changes to specified itmx files and parse to python file
* Plotting: Probably more plots and ideas
* Tool for defining scenarios


