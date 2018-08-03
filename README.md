# Business Prototyping Toolkit for Python
Welcome to the Business Prototyping Toolkit for Python!

BPTK_Py is the implementation of a simulation and plotting engine for Stela System Dynamics models.  It gives you the power to simulate Stela System Dynamics Models within python - and create beautiful plots of the simulation results for use in Jupyter notebooks/lab.
It requires a python-parsed version of the model containing the set of equations. We employ [transentis' sdcc parser](https://bitbucket.org/transentis/sd-compiler)  for this. An example model is available in [simulation_models/](simulation_models/)

To initialize the framework and get access to the API methods (see later sections), use these lines:
```
from BPTK_Py.bptk import bptk_wrapper 
bptk = bptk_wrapper()
```


## Scenarios
Scenarios are the heart of each simulation. A scenario defines which simulation model to use, the source model and has a name. It may override model constants and define strategies. The latter change constants in different steps of the simulation. See the "strategy simulation" section for details.
You write scenarios in JSON format. A simple example may look like this:

```
{
  "constants": {
    "cost.paymentTransactionCost" : 0.5,
    "cost.productDevelopmentWage" : 10000
  },
  "source" : "simulation_models/make_your_startup_grow.itmx",
  "name": "MakeYouStartUpGrow_2",
  "from": 1,
  "until": 100,
  "dt": 1,
  "model": "simulation_models/model",
}
```
The ``constants`` list stores the overrides for the constants. The ``model`` parameter contains the relative path to the (python) simulation model. Please omit the ``.py`` file ending. The simulation will not start without a ``name``. You should consider using the ``source`` field. For each scenario, a file monitor will run in background to check for changes in the source model. The file monitor will automatically update the python model file whenever a change to the source model is detected! (See next section for more details)
The repo contains the **Scenario Manager** ipython notebook in the top level. You may use it to check for available scenarios and write your own ones. (For now the tool is very basic, extensions to come soon)

## Monitoring of itmx source models
Whenever you instantiate a *bptk* object and plot at least one scenario, one thread per ``sourceModel`` will monitor the scource ITMX file. It checks for modifications each second. Whenever a modification is detected, a bash script will be called that executes the node.js transpiler: [https://bitbucket.org/transentis/sd-compiler](https://bitbucket.org/transentis/sd-compiler)

For this to work, make sure you set the parameter ``sd_py_compiler_root`` to the absolute path of the transpiler's root directory in [BPTK_Py/config/config.py](BPTK_Py/config/config.py), e.g. ``sd_py_compiler_root = "~/Code/sd-compiler/"``
The simple bash script calling the transpiler lies in [BPTK_Py/shell_scripts/update_model.sh](BPTK_Py/shell_scripts/update_model.sh). It takes the transpiler path and the relative path of the simulation models as taken from the scenario config's ``sourceModel`` field and executes the parser once.

**Attention:** If you use the BPTK engine within a larger software project, please do not forget to issue ``bptk.destroy()``. This command stops all monitoring threads. If you don't use it, don't be surprised if your script never terminates ;-). If you're using BPTK within a framework such as the infamous [Jupyter Lab](https://jupyter.org/), do not worry. The thread runs within the Notebook kernel and will die when you shutdown the notebook kernel. 

## API calls
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

## Strategy simulation
The simulator is also able to simulate various strategies. A strategy defines which constants change at which point in time of the simulation. For defining a strategy, use the ``strategy`` key in your scenario definition and give (key,value) sets for the constants you'd like to change. Note that the ``constants`` field in the strategy will also be parsed at ``t=0`` for initial modifications of the strategies.
```
"strategy": {
    "1": {
        "cost.paymentTransactionCost": 0.4,
        "customers.marketingBudget": 5000
    },
    "2": {
        "cost.paymentTransactionCost": 0.8,
        "customers.marketingBudget": 10000
    },
    "50": {
        "cost.paymentTransactionCost": 0.65,
        "customers.marketingBudget": 0
    },
    "76": {
        "cost.paymentTransactionCost": 0.7,
        "customers.marketingBudget": 2000
    },
    "100": {
        "cost.paymentTransactionCost": 0.99,
        "customers.marketingBudget": 99000
    }
}
```
This strategy modifies the constants ``cost.paymentTransactionCost`` and ``customers.marketingBudget`` at time steps 1, 2, 50 and 76. The full scenario for this strategy is available in [scenarios/make_your_startup_grow_with_strategy.json](scenarios/make_your_startup_grow_with_strategy.json). To apply a strategy for a scenario, use the parameter ``strategy=True``. 

**Note:** If you set the ``strategy=True`` but there is not strategy defined in the scenario, the simulator will just issue a Warning in the logfile and execute the simulation(s) without a strategy. 

## Look-and-Feel
BPTK Py uses transentis' color and font style for the plots. You might not own our font or simply dislike the colors and font sizes. In that case, the plot will fall back to the ~~ugly~~ beautiful DejaVu Sans. Override the style by modifying [BPTK_Py/config/config.py](BPTK_Py/config/config.py). 

## Interactive Readme
Check out the iPython notebook *Interactive Readme* in the top level of the repo for an interactive approach to learning how to use the framework as an analyst.





