# Business Prototyping Toolkit for Python
Welcome to the Business Prototyping Toolkit for Python!

BPTK_Py is the implementation of a simulation and plotting engine for [Stela Architect](https://www.iseesystems.com/store/products/stella-architect.aspx) System Dynamics models.  It gives you the power to simulate Stela System Dynamics Models within python - and create beautiful plots of the simulation results for use in Jupyter notebooks/lab. You even may as well reuse the simulation results within python!
It requires a python-parsed version of the model containing the set of equations. We employ [transentis' sdcc parser](https://bitbucket.org/transentis/sd-compiler)  for this. An example model is available in [simulation_models/](simulation_models/)

## Installation
To install the package, cd to the directory of the package (the git repo's root) and type ``pip install .`` . Pip will install the package and make it available system-wide. Now you can start working with the package.
In order to keep your system clean, you may want to use a [virtual environment](https://docs.python-guide.org/dev/virtualenvs/). Following steps are required to set up the venv and and install BPTK_Py into it:
```
pip install virtualenv
virtualenv bptk_test # This will create a subfolder with a minimal python environment
# Enter the virtual environment. In the beginning of your prompt you should see "(bptk_test)"
source bptk_test/bin/activate  #  For UNIX/Linux
bptk_test\Scripts\activate.bat # For Windows
cd /path/to/BPTK_Py_repo
pip install .  # Install the package

## If you want Jupyter Lab as well: (HIGHLY RECOMMENDED)
pip install jupyterlab
```
Pip will make sure to download all required dependencies and now you are ready to play around with BPTK_Py! 
If you executed the last line as well, you already have a functioning version of jupyter lab and can start working interactively using jupyter notebooks. Just type ``jupyter lab`` to get started.

## Initialization in Python
To initialize the framework in your own python script / jupyter notebook and get access to the API methods (see later sections), use these lines:
```
# Set the path to the sd-compiler repo root:

import BPTK_Py.config.config as config
config.configuration["sd_py_compiler_root"] = "~/Code/sd-compiler/"  ## <--- Please change this path to the git repo of the sd_compiler package!

## For Windows PC's, please use \\ for seperating folders and add additional \" to add quotation marks inside the string:
config.configuration["sd_py_compilter_root"] = "\"C:\\Users\\Henrique Beck\\Code\\sd-compiler\""
from BPTK_Py.bptk import bptk 

bptk = bptk()
```
Now you are ready to play around with the APIs!

## Plotting API
After initializing BPTK_Py, let us dive into the plotting API, the heart of the simulation framework.
For interactive examples, you may always refer to the example notebook. The main method for plotting and simulating is the ``plot_scenarios`` method.
```
bptk.plot_scenarios(scenarios,scenario_managers=[], equations=[], kind=config.kind, alpha=config.alpha, stacked=config.stacked, freq="D", start_date="1/1/2018", title="", visualize_from_period=0, x_label="", y_label="",series_names=["names","name2"],return_df=False)

```
The first plots one or multiple equations for one scenario ("scenario_name"). The scenario name is the one specified in the scenario JSON file. The other parameters are optional. Always use Python's list notations for the plural parameters (``scenario_names / equations / scenario_managers``).
The second method lets you plot one equation for multiple scenarios and uses the same parameter set.

* ``kind``: Kind of plot (area, line, bar, ...)
* ``alpha``: The alpha defines the opacity. Float 0.0 < alpha <= 1.0.
* ``freq``: Here we define the interval of the dates that we convert the ticks to. "D" means daily, "H" hourly, "M" monthly, "Y" annually and so on.
* ``start_date``: Date from which plot starts
* ``title``: Plot title
* ``visualize_from_period``: First index field to visualize from (in case we want to cut off the first x periods)
* ``x_label and y_label``: set the label names for the axis.
* ``series_names``: This optional parameter allows you to override the series names (in the order of the equations). Use Python's list notation: ``[ ]``. Without this parameter, BPTK will just use the equation and scenario names. If you have 3 equations and only specify one value in the list, will only modify the name of the first series. You may also use an empty string in the list to change the name of the second (or third..) series: ``[ "", "nameToChangeTo" ]`` 
* ``scenario_managers``: You may use a list to filter the scenarios by the scenario managers. If not specified, ``bptk_py`` will look for the specified scenarios(s) within all scenario managers. You might receive duplicates. We handle this by adding a suffix for all duplicates based on their scenario manager's name.

**The scenario managers are used to group a set of scenarios. You may either plot one or multiple equations for a scenario manager or one specific scenario (of one scenario manager).**

### Receive Data - not plot
In some cases you might want to receive the scenario results as a table instead of seeing a plot only. There is the parameter ``return_df``. In default, this is set to ``False``. When adding it as parameter to the plotting methods, and setting it to ``True``, you will receive a [Pandas DataFrame](https://pandas.pydata.org/pandas-docs/stable/). You can use the powerful API of Pandas to analyze, crunch data and join the results of multiple scenarios and equations for gaining deeper insights into the simulation results.

## Interactive Plotting
An important part of modelling is to modify values on-the-fly, interactively with the customer. The API call ``bptk.plot_with_widgets`` has this functionality. It comes with a field "constants" that contains a list of widget definitions. Each widget is defined using a tuple.
The structure is:  ``("widget_type","name.of.constant",start_value,maximum_value)``. This allows you to see the results of the simulations instantly without having to re-run the simulation manually. See a working example in the following plot.

Currently, we support two types of widgets to control the process:
* **sliders**: Sliders allow you to select a value in an interval. Use "slider" as ``widget_type``. A slider requires ``start_value and maximum_value`` as described above. Example: ``("slider",'initialOpenTasks',100.0,1000.0)``
* **checkbox**: If you want a checkbox, use "checkbox" as ``widget_type``. You do not have to supply ``start_value / maximum_value``. Example: ``("checkbox","initialStaff")``

For interactive plotting to work, you need to install an extension to jupyter lab. If you followed the above guide for initial setup, this should do in the terminal:
```
souce bptk_test/bin/activate
jupyter labextension install @jupyter-widgets/jupyterlab-manager
```


## Override the configuration
The configuration file contains some standard settings such as relative paths where BPTK_Py looks for scenarios and simulation models. It also stores the style settings for the plots. If you wish to override these settings, you can do so:
```
import BPTK_Py.config.config as config

# Override setting "config_key":
config.configuration["config_key"] = "VALUE"

# Get available configuration keys:
for key, value in config.configuration.items():
    print("{} : {}".format(key,str(value)))

```

## Scenarios
Scenarios are the heart of each simulation. A scenario defines which simulation model to use, the source model and has a name. It may override model constants and define strategies. The latter change constants in different steps of the simulation. See the "strategy simulation" section for details.
You write scenarios in JSON format. We group simulation scenarios by "scenario Managers". One scenario manager encapsulates one simulation model and has a name. Scenarios run this simulation model and modify constants.
One JSON file may contain more than one scenario manager and hence a key is required to distinguish the different scenarios. A simple example may look like this:

```
{
    "ScenarioManager1": {
        "model": "simulation_models/model",
        "source": "simulation_models/make_your_startup_grow.itmx",
        "scenarios": {
            "MakeYourStartUpGrow": {
                "constants": {
                "cost.paymentTransactionCost": 0.0
                }
            },
            "MakeYourStartUpGrow_2": {
            "constants": {
                "cost.paymentTransactionCost": 0.5,
                "cost.productDevelopmentWage": 10000
                }
            }
        }
    }
}

```
We start with the name of the scenario manager's name which stores all the scenarios. If you use the same name for a scenario manager in another file, this will be detected and the scenario will be added to the scenario manager. The scenario manager stores the model (source file and python file) as well as all scenarios that belong to it. The ``model`` parameter contains the relative path to the (python) simulation model The scenarios follow in the ``scenarios`` tag.
For each scenario, you have to supply a unique name as well. JSON does not support integer keys. When you use the same name multiple times, the simulator will only retain the latest one
The ``constants`` list stores the overrides for the constants. . Please omit the ``.py`` file ending.  You should consider using the ``source`` field in the scenario manager tag. For each source file, a file monitor will run in background to check for changes in the source model. The file monitor will automatically update the python model file whenever a change to the source model is detected! (See next section for more details)
The repo contains the **Scenario Manager** ipython notebook in the top level. You may use it to check for available scenarios and write your own ones. (For now the tool is very basic, extensions to come soon)

### Changing scenario files during runtime
If you changed a JSON scenario file during runtime and wish to reload the scenario(s), use the following method:

```
bptk.reset_scenario(scenario_manager="NAMEOFSCENARIOMANAGER",scenario_name="NAMEOFSCENARIO")
```

### Modifying points of graphical functions
You may have defined graphical functions within stela Architect but a scenario may change these if you want. Internally, a graphical function is nothing else but a set of points and values. Hence, you may easily modify these points using the scenario JSON file. All you ened is the name of the graphical function, e.g. ``'capabilities.learningCurve'`` and the set of points for the function with their respective x and y values as list: `` [x,y] ``.
Let us modify the previous scenario example and add some points:

```
{
"ScenarioManager1": {
    "model": "simulation_models/model",
    "source": "simulation_models/make_your_startup_grow.itmx",
    "scenarios": {
        "MakeYourStartUpGrow_2": {
            "constants": {
                "cost.paymentTransactionCost": 0.5,
                "cost.productDevelopmentWage": 10000
                }
                "points":{
                    'capabilities.learningCurve':
                    [
                        [0,1], [1,2], [2,3], [3,4]
                    ]
                    }
            }
        }
    }
}

```

Now we defined four points for the function. The simulator will make sure to interpolate the values if an equation requires the y-value for decimal x values.

## Monitoring of itmx source models
Whenever you instantiate a *bptk* object and plot at least one scenario, one thread per ``sourceModel`` will monitor the scource ITMX file. It checks for modifications each second. Whenever a modification is detected, a bash script will be called that executes the node.js transpiler: [https://bitbucket.org/transentis/sd-compiler](https://bitbucket.org/transentis/sd-compiler)

For this to work, make sure you set the parameter ``sd_py_compiler_root`` to the absolute path of the transpiler's root directory in [BPTK_Py/config/config.py](BPTK_Py/config/config.py), e.g. ``sd_py_compiler_root = "~/Code/sd-compiler/"``

The simple bash script calling the transpiler lies in [BPTK_Py/shell_scripts/update_model.sh](BPTK_Py/shell_scripts/update_model.sh). It takes the transpiler path and the relative path of the simulation models as taken from the scenario config's ``sourceModel`` field and executes the parser once.

**Attention:** If you use the BPTK engine within a larger software project, please do not forget to issue ``bptk.destroy()``. This command stops all monitoring threads. If you don't use it, don't be surprised if your script never terminates ;-). If you're using BPTK within a framework such as the infamous [Jupyter Lab](https://jupyter.org/), do not worry. The thread runs within the Notebook kernel and will die when you shutdown the notebook kernel. 

#### Attention Mac OS X user
For now there is a bug, that requires you to use node version 8 to successfully download the extension. If you are using homebrew, issue these commands:
```
brew uninstall node yarn
brew install node@8 # --> might have to set path to link node to node8
```

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

## Advanced background: Scenario Managers and the factory
As you observed, the simulator uses scenario managers to decouple scenarios from each other and group them. For this purpose, a ``scenarioManagerFactory`` is part of the package. It organizes the scenarios and scenario managers. Each scenario manager has a name and stores all scenarios that belong to it. The factory makes sure everything is organized correctly during runtime. If you want to receive all available scenario managers, issue this code:
```
scenario_managers = bptk.scenario_manager_factory.scenario_managers
```

This is a dictionary (name : object) of all available scenario managers. The scenario managers store a dictionary for all the scenarios, with the scenario names as keys. You may manually browse through the objects or just use the API methods as described above and use the names of the scenario managers. The factory will correctly identify the right scenarios. To obtain a scenario object or a list of all scenarios (for a specific scenario) manager manually, issue this code:
```
scenarios = bptk.scenario_manager_factory.get_scenarios(scenario_managers=[],scenario_names=[])
```
As you see, the parameters are lists. It is possible to filter by both. It will output duplicates (using the scenario managers' name as a suffix for each match) or nothing if it does not find any match. You see that complex queries are possible.

Upon modifications of scenarios (JSON file) or to flush the simulation results, you may use the following code to reset:

```
scenario_manager_factory = bptk.scenario_manager_factory

## Reload one specific scenario:
scenario_manager_factory.reset_scenario(scenario_manager="ScenarioManager2",scenario_name="MakeYourStartUpGrow-x")

## Reset all scenarios (Returns the new scenario managers)
bptk.scenario_manager_factory.reset_all_scenarios()

```
## Resetting the simulation
After a while of simulating, modifying strategies and constants and generating beautiful plots, you may realize that you want to go back and reset the simulation. For this purpose, you have three methods available:
* ``reset_scenario(scenario_manager, scenario)``: This deletes a specific scenario from memory and reloads it from file. Requires the scenario manager's name and the scenario name.
* ``reset_all_scenarios()``: Reset all scenarios and re-read from file
* ``reset_simulation_model(scenario_manager, scenario="")``: For runtime optimizations, the simulator will cache the simulation results. In some rare cases, this cache may not be flushed upon scenario modification. Hence, this method resets the simulation model's cache.

## Advanced: Extended Strategies
Extended strategies give the user a lot of power over the simulation but are rather complex. The goal of such strategies is to replace certain equations of the model with custom lambda functions during runtime at specific times in the simulation. This is for advanced use only and currently considered unstable.

First we need to obtain the scenarios and their corresponding simulation models and replace the given equations with the new lambda. 
An extended strategy is just another dictionary. In general, it looks like this:
```
scenarios = bptk.ScenarioManager.getAvailableScenarios()

extended_strategy= {
    "MakeYourStartUpGrow_strategy" : {
        1 : { 
            "cashFlow.cashFlowYtd" : lambda t : 85000 if t<= 1 else scenarios["MakeYourStartUpGrow_strategy"].model.memoize("cashFlow.cashFlowYtd",t-1),
            "cash.cash" : lambda t : 8000000 if t <= scenarios["MakeYourStartUpGrow_strategy"].model.starttime else scenarios["MakeYourStartUpGrow_strategy"].model.memoize("cash.cash",t-1)+ 80000,
        },
        75 : {
            "cash.cash" : lambda t : 0
            }
        }    
}
```
You see that this concept is rather complex and requires understanding of Python. First we have to load all available scenarios into the ``scenarios`` variable. The dictionary contains *pointers* to the specific scenario objects that we loaded from the scenario files. They are stored in the ``ScenarioManager`` object instance of the ``bptk`` object. The lambda functions now have to use these pointers to receive the pointers to the ``model`` object (and therefore the equations) of the simulation model. 
We will overwrite the specific equations with the given lambda function(s) in the previously-described strategy dictionary of the scenario. It is possible to store lambda functions just like this as strings in JSON **but** the complexity is even higher when it comes to adding it to the model during run-time. As the bptk object uses the same set of scenarios, it will use the same object pointers when we finally issue ``bptk.plotOutputsForScenario(... ,strategy=True)``

The above strategy plays a around with the equations ``cashFlow.cashFlowYtd`` and ``cash.cash``. Look at ``cash.cash``. It will return 80,000 if at starttime of the model. Otherwise, it return the value of t-1 + 80,000 and generate a linear function. Instead of ``t-1`, we might even use the model's ``dt``: ``scenarios["MakeYourStartUpGrow_strategy"].model.dt`` instead of -1. But this would make the code line too complex. Make sure to use dt however, if you intend to work in productive mode!

After defining the strategy, you have to store the lambdas in the function. ``bptk`` comes with a method for this. The code is as follows:
```
bptk.modify_strategy_for_complex_strategy(scenarios=scenarios,extended_strategy=extended_strategy)`

bptk.plotScenarioForOutput(
    ...,
    strategy=True
)
```
The method  ``modify_strategy_for_complex_strategy`` requires the scenarios object as the lambdas reference to the objects inside them and the extended strategy. It will then just modify each scenario's strategy. 
You see that you can use the well-described method for plotting the scenario(s) with the modified strategies. Just do not forget to set the parameter ``strategy=True``.  This is due to the power of the pointers. There is no additional method for plotting required as the plotting methods use the same ``scenarios`` objects as stored within the ``scenarioManager``.

Of course you may as well use this approach to only modify constants. If you intend to modify an initial constant, just enter it for t=0.

### Complex strategy for an interval
If you want to set another lambda function only for an interval and reset to the old one, this is easily possible. Check the following strategy. It will replace the "cash.cash" function between t=20 to 50 and then restore the one from the model:
```
extended_strategy= {
    "MakeYourStartUpGrow_strategy" : {
        20 : { 
            "cashFlow.cashFlowYtd" : lambda t : 85000 if t<= 1 else scenarios["MakeYourStartUpGrow_strategy"].model.memoize("cashFlow.cashFlowYtd",t-1),
            "cash.cash" : lambda t : 70000000 if t <= scenarios["MakeYourStartUpGrow_strategy"].model.starttime else 70000000,
        },
    50 : {
        "cash.cash" : scenarios["MakeYourStartUpGrow_strategy"].model.equations["cash.cash"]
        }
    }    
}
```

### Thoughts on recursion and memoization
The models we use are very complex and generate large "tail-recursions" when running in a naive fashion. Most results depend on the results of previous simulation periods. This is why we use "memoization". The model's memo stores previous results for each equation. So e.g. when an equation requires a the result of itself from the previous period t-1, the model will first check if this result is available in the memo rather than re-computing it. When you now modify an equation in timestep 20, the simulator will run the simulation upto t=19, modify the lambda function and continue the simulation. This means, the model keeps all of its results upto t=19 in its memo. This is the desired behavior and does not require you to add any additional complex code. However, this requires you to always use the model's ``memoize(equation_name, t-dt)`` function call and not directly access the ``equations`` object of the model. The following are wrong and correct examples but omitting the outer dictionary structure.

**Right:**  ``"cashFlow.cashFlowYtd" : lambda t : 85000 if t<= 1 else scenarios["MakeYourStartUpGrow_strategy"].model.memoize("cashFlow.cashFlowYtd",t-1)``
**Wrong:**  ``"cashFlow.cashFlowYtd" : lambda t : 85000 if t<= 1 else scenarios["MakeYourStartUpGrow_strategy"].model.equations["cashFlow.cashFlowYtd"](t-1)``

## Create Scenarios during Runtime
It is possible to add scenarios during runtime. For convenience, here is some example code you may use as a template to generate your own scenarios during runtime. If you define multiple scenarios for the same ``scenario_manager``, this is no problem. 

First define the details for the scenario manager and then set up the name of the scenario, the strategy and the constants. The strategy may as well be one of the complex ones as described above. But be careful to define everything correctly.

```
scenario_manager = {
    "name" : "ScenarioManager_temp",
    "model" : "simulation_models/sd_simple_project",
    "source" : "simulation_models/sd_simple_project.itmx"
    }


name = "scenario_160"
strategy = {
    "20": {
        "deadline" : 2000
        } 
}
constants = {
    "deadline" : 160,
    "effortPerTask" : 0.1
}


dictionary ={ scenario_manager["name"]:  
{
    "model": scenario_manager["model"],
    "source": scenario_manager["source"],
    name:{
        "constants" : constants, 
        "strategy" : strategy
        } 
    } 
}


bptk.add_scenario(dictionary=dictionary)
```

When you successfully registered the new scenario, you can easily plot it as you are used to!

## Model Checking
To verify the behavior of the simulator and of the simulation model, it is important to check certain assertions. ``bptk_py`` comes with a simple model checker to verify ``lambda`` functions, small functions stored in a variable.
The function is supposed to only return True or False and receives a data parameter. For example ``lambda data : sum(data)/len(data) < 0`` tests if the average of the data is below 0. We can get the raw output data instead of the plot if we use the parameter ``return_df=True``. This returns a dataFrame object. The following example generates this dataframe and uses the model checker to test if the ``productivity`` series' mean is below 0. Otherwise it will return the specified message.

```
df =bptk.plot_scenarios(
    scenario_managers=["smSimpleProjectManagement"],
    scenarios=["scenario120"],
    kind="line",
    equations=["productivity"],
    stacked=False, 
    strategy=True,
    freq="D", 
    start_date="1/11/2017",
    title="Added scenario during runtime",
    x_label="Time",
    y_label="Number",
    return_df=True
    )

check_function = lambda data : sum(data)/len(data) < 0

bptk.model_check(df["productivity"],check_function,message="Productivity is not <0")
```



## Look-and-Feel
BPTK Py uses transentis' color and font style for the plots. You might not own our font or simply dislike the colors and font sizes. In that case, the plot will fall back to the ~~ugly~~ beautiful DejaVu Sans. Override the style by modifying [BPTK_Py/config/config.py](BPTK_Py/config/config.py).  The main settings for the style are in the dictionary ``matplotlib_rc_settings`

## Interactive Readme
Check out the iPython notebook *Interactive Readme* in the top level of the repo for an interactive approach to learning how to use the framework as an analyst. It also applies the example for the extended strategies.

## Limitations
* For now, the simulator may only simulate using the Euler method
* The SD model transpiler supports all builtin functions apart from RANDOM with seed




