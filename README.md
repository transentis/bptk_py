# Business Prototyping Toolkit for Python
Welcome to the Business Prototyping Toolkit for Python!

## BPTK_Py
BPTK_Py is the implementation of a simulation engine and plotting for Stela System Dynamics models.  It gives you the power to simulate Stela System Dynamics Models within python - and create beautiful plots of the simulation results for use in Jupyter notebooks.
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
  "sourceModel" : "simulation_models/make_your_startup_grow.itmx",
  "name": "MakeYouStartUpGrow_2",
  "from": 1,
  "until": 100,
  "dt": 1,
  "model": "simulation_models/model",
  "equationsToSimulate": [
    "capabilities.totalWorkforceExperience",
    "cash.cash",
  ]
}
```
The ``constants`` list stores the overrides for the constants. The ``model`` parameter contains the relative path to the simulation model. Please omit the ``.py`` file ending. The simulation will not start without a ``name``, the simulation will exit with an error if no name is given. The ``equationsToSimulate`` contains equations that the simulator is supposed to simulate. In this way, you do not need to specify the equations to simulate in the API (just leave the ``equation(s)`` parameters empty then). It serves as a fallback if the equations are not specified in code. You should also consider using the ``sourceModel`` field as for each scenario, a file monitor will run in background to check for changes in the source model. The file monitor will automatically update the python model file whenever a change to the source model is detected!
The repo contains the **Scenario Manager** ipython notebook in the top level. You may use it to check for available scenarios and write your own ones. (For now the tool is very basic, extensions to come soon)

### API calls
The ipython example notebook contains examples for the API calls. For now, there are two methods analysts can use:
```
bptk.plotOutputsForScenario(scenario_name, equations=[], kind=config.kind, alpha=config.alpha, stacked=config.stacked, freq="D", start_date="1/1/2018", title="", visualize_from_period=0, x_label="", y_label="",series_names=["names","name2"],return_df=False)

bptk.plotScenarioForOutput(scenario_names, equation, kind=config.kind, alpha=config.alpha, stacked=config.stacked, freq="D", start_date="1/1/2018", title="", visualize_from_period=0, x_label="", y_label="",series_names=["names","name2"],return_df=False):
```

The first plots one or multiple equations for one scenario ("scenario_name"). The scenario name is the one specified in the scenario JSON file. The other parameters are optional. Always use Python's list notations for the plural parameters (``scenario_names / equations``).
The second method lets you plot one equation for multiple scenarios and uses the same parameter set.

* ``kind``: Kind of plot (area, line, bar, ...)
* ``alpha``: The alpha defines the opacity. Float 0.0 < alpha <= 1.0.
* ``freq``: Here we define the interval of the dates that we convert the ticks to. "D" means daily, "H" hourly, "M" monthly, "Y" annually and so on.
* ``start_date``: Date from which plot starts
* ``title``: Plot title
* ``visualize_from_period``: First index field to visualize from (in case we want to cut off the first x periods)
* ``x_label and y_label``: set the label names for the axis.
* ``series_names``: This optional parameter allows you to override the series names (in the order of the equations). Use Python's list notation: ``[ ]``. Without this parameter, BPTK will just use the equation and scenario names. If you have 3 equations and only specify one value in the list, will only modify the name of the first series. You may also use an empty string in the list to change the name of the second (or third..) series: ``[ "", "nameToChangeTo" ]`` 

## Interactive Readme
Check out the iPython notebook *Interactive Readme* in the top level of the repo for an interactive approach to learning how to use the framework as an analyst.

## TODO
* Monitoring: Whenever we change a specific model in stela, the changes should be written back to the model file. When BPTK_Py is initiated, a file monitor starts if a ``sourceModel`` is given in the scenario configuration. **Still pending the integration of the model parser.**




