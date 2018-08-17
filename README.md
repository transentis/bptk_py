# Business Prototyping Toolkit for Python
Welcome to the Business Prototyping Toolkit for Python!

BPTK_Py is the implementation of a simulation and plotting engine for System Dynamics models. 
It gives you the power to simulate System Dynamics Models within python - and create beautiful plots of the simulation results for use in Jupyter notebooks/lab. 

It requires a python simulation model following the conventions given in the end of this Readme. 
Furthermore, it ships with [transentis' sdcc parser](https://bitbucket.org/transentis/sd-compiler) for generating python 
versions of simulation models from other engines (such as Stella Architect).

## Requirements and Installation
To install the package, just run `` pip install BPTK_Py ``.
Pip will install the package and make it available system-wide. It downloads its dependencies automatically. 
Now you can start working with the package.
In order to keep your system clean, you may want to use a [virtual environment](https://docs.python-guide.org/dev/virtualenvs/), a local copy of your Python distribution that stores all packages required and does not interfere with your system's packages. Following steps are required to set up the venv and and install BPTK_Py into it:
```
pip install virtualenv
virtualenv bptk_test 

# Enter the virtual environment. In the beginning of your prompt you should see "(bptk_test)"
source bptk_test/bin/activate  #  For UNIX/Linux
bptk_test\Scripts\activate.bat # For Windows

pip install BPTK_Py

## If you want Jupyter Lab as well: (HIGHLY RECOMMENDED)
pip install jupyterlab
jupyter labextension install @jupyter-widgets/jupyterlab-manager
```
If you executed the last line as well, you already have a functioning version of jupyter lab and can start working 
interactively using jupyter notebooks. Just type ``jupyter lab`` to get started.

### Package dependencies
If for any reason, you want to install the requirements manually or want to know why we need the packages, here comes the list. If you observe malfunctions in the framework and believe the reason may be incompatibilities with newer versions of the packages, please inform us.
So far, we tested the framework with Python 3.4, 3.6 and 3.7. It should be working fine with other Python 3.x versions.

Package name | What we use it for | Last tested version
--- | --- | ---
pandas |DataFrames and internal results storage | 0.23.4
matplotlib |Plotting environment | 2.2.2
ipywidgets |Widget environment for notebooks | 7.4.0
scipy |Linear interpolation for graphical functions  | 1.1.0
numpy |Linear interpolation and required by pandas | 1.15.0
jupyter lab extension for jupyter-widgets |Use ipywidgets in jupyter lab | 0.36.1


## Initialization in Python
To initialize the framework in your own python script / jupyter notebook and get access to the API methods (see later sections), use these lines:

**Required lines**
```
from BPTK_Py.bptk import bptk 

bptk = bptk()

```
**Optional lines**
```
# To Show all available scenarios and -managers:
print("Available Scenario Managers and Scenarios:\n")
managers = bptk.scenario_manager_factory.get_scenario_managers(scenario_managers_to_filter=[])

for key, manager in managers.items():
    print("")
    print("*** {} ***".format(key))

    for name in manager.get_scenario_names():
        print("\t {}".format(name))
```
On first run, the compiler may have to download some additional dependencies for model compilation. Please be patient for some seconds. This will only occur on first-time run.
Now you are ready to play around with the APIs!

## Plotting API
After initializing BPTK_Py, let us dive into the plotting API, the heart of the simulation framework.
For interactive examples, you may always refer to the example notebook. The main method for plotting and simulating is the ``plot_scenarios`` method.

You may use it to generate plots from your simulation models almost instantly. You can control all major settings for
```
bptk.plot_scenarios(
    scenarios,
    scenario_managers=[], 
    equations=[], 
    kind=config.kind, 
    alpha=config.alpha, 
    stacked=config.stacked, 
    freq="D", 
    start_date="1/1/2018", 
    title="", 
    visualize_from_period=0, 
    x_label="", 
    y_label="",
    series_names={"series_to_rename":"rename_to"},return_df=False)

```
The first plots one or multiple equations for one scenario ("scenario_name"). The scenario name is the one specified in the scenario JSON file. The other parameters are optional. Always use Python's list notations for the plural parameters (``scenario_names / equations / scenario_managers``).
The second method lets you plot one equation for multiple scenarios and uses the same parameter set.

* ``kind``: Kind of plot (area, line, bar, ...)
* ``alpha``: The alpha defines the opacity. Float 0.0 < alpha <= 1.0.
* ``freq``: Here we define the interval of the dates that we convert the ticks to. "D" means daily, "H" hourly, "M" monthly, "Y" annually and so on.
* ``start_date``: Date from which plot starts
* ``title``: Plot title
* ``visualize_from_period``: First t to visualize from (in case we want to cut off the first x periods)
* ```visualize_to_period```: Last t to visualize (to cut off later periods)
* ``x_label and y_label``: set the label names for the axis.
* ``scenario_managers``: You may use a list to filter the scenarios by the scenario managers. If not specified, ``bptk_py`` will look for the specified scenarios(s) within all scenario managers. You might receive duplicates. We handle this by adding a suffix for all duplicates based on their scenario manager's name.
* ``series_names``: The equation names are not the kind of names we want to show the customer. You may use the ``series_names`` parameter to rename them. Supply the equations to rename and their destination names. Use Python's dict notation: ``{ equation_name : rename_to }``. The dictionary serves as a set of replacement rules. To correctly rename the series, you have to understand how the framework sets the names of series to avoid ambiguity in series names. If you use more than one scenario manager for plotting, bptk_py applies the following series naming schema: ``"scenarioManager"_"scenario"_"equation"``. If you want to replace this, use ``series_names={"scenarioManager_scenario_equation": "new name"}``. You may as well define a rule that replaces the name of each scenario Manager with a whitespace. The number of rules is not limited.


**The scenario managers are used to group a set of scenarios. You may either plot one or multiple equations for a scenario manager or one specific scenario (of one scenario manager).**

The following lines of code show how to easily use the API to generate the example graph below:

```python
from BPTK_Py.bptk import bptk
bptk = bptk()
bptk.plot_scenarios(
    scenario_managers=["smSimpleProjectManagement"],
    scenarios=["scenario80"],
    equations=['openTasks',"closedTasks"],
    title="Example Graph\n",
    x_label="Time",
    kind="area",
    y_label="Some Number",
    start_date="1/11/2017",
    freq="D",
    series_names={"openTasks":"open  Tasks","closedTasks" : "Closed Tasks"}
)
```

![png](README/output_0_0.png)


```
CODE!
```



### Receive the results data
You might want to receive the scenario results as a table instead of seeing a plot only. There is the parameter ``return_df``. In default, this is set to ``False``. When adding it as parameter to the plotting methods, and setting it to ``True``, you will receive a [Pandas DataFrame](https://pandas.pydata.org/pandas-docs/stable/). You can use the powerful API of Pandas to analyze, crunch data and join the results of multiple scenarios and equations for gaining deeper insights into the simulation results.


## Interactive Plotting
An important part of modelling is to modify values on-the-fly, interactively with the customer. The API call ``bptk.plot_with_widgets`` has this functionality. It comes with a field "constants" that contains a list of widget definitions. Each widget is defined using a tuple.
The structure is:  ``("widget_type","name.of.constant",start_value,maximum_value)``. This allows you to see the results of the simulations instantly without having to re-run the simulation manually.

Currently, we support two types of widgets to control the process:
* **sliders**: Sliders allow you to select a value in an interval. Use "slider" as ``widget_type``. A slider requires ``start_value and maximum_value`` as described above. Example: ``("slider",'initialOpenTasks',100.0,1000.0)``
* **checkbox**: If you want a checkbox, use "checkbox" as ``widget_type``. You do not have to supply ``start_value / maximum_value``. Example: ``("checkbox","initialStaff")``
* **timerange**: This will give you a slider in which you can select time ranges within the graph to "zoom in/out" of certain parts of the graph. It gives you the power to further look into certain simulation periods. It is enough to just add the keyword "timerange" as ``widget_type``.

If you are using jupyter notebook, interactive plotting should work if you installed ``ipywidgets`` (should be installed as dependency). 
But if you are using jupyter lab, please install the required extension. This should do in the terminal:
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
Scenarios are the heart of each simulation. A scenario defines which simulation model to use, the source model and has a name. 
It may override model constants and define execution strategies. 
The latter change constants in different steps of the simulation. See the "strategy simulation" section for details.
You write scenarios in JSON format. Please store the scenarios in the ``scenarios`` subfolder of your current working directory so ``BPTK_Py`` is able to find it. 
If you wish to use another folder, feel free to change ``config.configuration["scenario_storage"]`` to a folder of your choice.
We group simulation scenarios by "scenario Managers". One scenario manager encapsulates one simulation model and has a name. Scenarios run this simulation model and modify constants.
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
                "cost.productDevelopmentWage": "5/10"
                }
            }
        }
    }
}

```
We start with the name of the scenario manager's name which stores all the scenarios. If you use the same name for a scenario manager in another file, this will be detected and the scenario will be added to the scenario manager. 
The scenario manager stores the model (source file and python file) as well as all scenarios that belong to it. 
The ``model`` parameter contains the (relative) path to the (python) simulation model. If using a relative path, keep in mind that ``BPTK_Py`` looks for the file from your current working directory, i.e. the path of your script or jupyter notebook. The actual scenarios follow in the ``scenarios`` tag.
For each scenario, you have to supply a unique name as well. JSON does not support integer keys. The ``constants`` list stores the overrides for the constants. 
You may either define numerical values such as ``0.5`` or use strings to define expressions such as ``"5/10"``which will be evaluated to `0.5`` by the framework.

You should consider using the ``source`` field in the scenario manager tag. It specifies the (relative) path to the original model file of 3rd party applications. 
For now, the framework supports automatic conversion of .itmx/.stmx files from Stella Architect. 
For each source file, a file monitor will run in background to check for changes in the source model. 
The file monitor will automatically update the python model file whenever a change to the source model is detected! 
(See next section for more details)


### Changing scenario files during runtime
If you changed a JSON scenario file during runtime and wish to reload the scenario(s), use the following method:

```
bptk.reset_scenario(scenario_manager="NAMEOFSCENARIOMANAGER",scenario_name="NAMEOFSCENARIO")
```

### Modifying points of graphical functions
You may have defined graphical functions within stela Architect but a scenario may change these if you want. Internally, a graphical function is nothing else but a set of points and values. Hence, you may easily modify these points using the scenario JSON file. All you need is the name of the graphical function, e.g. ``'capabilities.learningCurve'`` and the set of points for the function with their respective x and y values as list: `` [x,y] ``.
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

## Monitoring of 3rd party source models
For now, we are able to translate Stella Architect Models to python using transentis' [sd-compiler](https://bitbucket.org/transentis/sd-compiler).
Whenever you instantiate a `bptk`` object and plot at least one scenario, one thread per ``sourceModel`` will monitor the scource ITMX file if the scenario specifies a ``source`` field. It checks for modifications each second. Whenever a modification is detected, a bash script will be called that executes the transpiler.

For this to work, make sure you set the parameter ``sd_py_compiler_root`` to the absolute path of the transpiler's root directory in [BPTK_Py/config/config.py](BPTK_Py/config/config.py), e.g. ``sd_py_compiler_root = "~/Code/sd-compiler/"``

The simple bash script calling the transpiler lies in [BPTK_Py/shell_scripts/update_model.sh](BPTK_Py/shell_scripts/update_model.sh). It takes the transpiler path and the relative path of the simulation models as taken from the scenario config's ``sourceModel`` field and executes the parser once.

**Attention:** If you use the BPTK engine within a larger software project, please do not forget to issue ``bptk.destroy()``. This command stops all monitoring threads. If you don't use it, don't be surprised if your script never terminates ;-). If you're using BPTK within a framework such as the infamous [Jupyter Lab](https://jupyter.org/), do not worry. The thread runs within the Notebook kernel and will die when you shutdown the notebook kernel. 

#### Attention Mac OS X user
For now there is a bug, that requires you to use node version 8 to successfully download the extension. If you are using homebrew, issue these commands:
```
brew uninstall node yarn
brew install node@8 # --> might have to set path to link node to node8
```

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

## Resetting the simulation
After a while of simulating, modifying strategies and constants and generating beautiful plots, you may realize that you want to go back and reset the simulation. For this purpose, you have three methods available:
* ``reset_scenario(scenario_manager, scenario)``: This deletes a specific scenario from memory and reloads it from file. Requires the scenario manager's name and the scenario name.
* ``reset_all_scenarios()``: Reset all scenarios and re-read from file
* ``reset_simulation_model(scenario_manager, scenario="")``: For runtime optimizations, the simulator will cache the simulation results. In some rare cases, this cache may not be flushed upon scenario modification. Hence, this method resets the simulation model's cache.

## Advanced: Extended Strategies
Extended strategies give the user a lot of power over the simulation but are rather complex. 
An extended strategy replaces certain equations of the model using lambda expressions. For now, you may only insert strategies during runtime.
This feature is for advanced use only and currently considered unstable.

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
The method  ``modify_strategy`` requires the scenarios object as the lambdas reference to the objects inside them and the extended strategy. It will then just modify each scenario's strategy. 
You see that you can use the well-described method for plotting the scenario(s) with the modified strategies. Just do not forget to set the parameter ``strategy=True``.  This is due to the power of the pointers. There is no additional method for plotting required as the plotting methods use the same ``scenarios`` objects as stored within the ``scenarioManager``.

Of course you may as well use this approach to only modify constants. If you intend to modify an initial constant, just enter it for t=0.

### Extended strategy only for an interval
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


## Look-and-Feel
BPTK Py uses transentis' color and font style for the plots. You might not own our font or simply dislike the colors and font sizes. 
In that case, the plot will fall back to the ~~ugly~~ beautiful DejaVu Sans. Override the style by modifying [BPTK_Py/config/config.py](BPTK_Py/config/config.py).  The main settings for the style are in the dictionary ``matplotlib_rc_settings`

## Interactive Readme
Check out the iPython notebook *Interactive Readme* for an interactive approach to learning how to use the framework as an analyst. 
The notebook comes with a set of scenarios and simulation models and supports you in getting started with the framework. It applies each of the described concepts and shows you how to play around with simulations.

## Limitations
* For now, the simulator may only simulate using the Euler method
* The SD model transpiler supports the following builtin functions:
    * size, stddev, sum, mean, rank, previous, abs, max, min, int, sin, cos, round, savediv, if, delay, init, normal, random, pulse, step


# Creating Own Simulation models
Instead of reading 3rd party simulation models, you may define your own simulation model. 
A simulation model is a self-contained python script. 
This means, it can be executed as its own file without any dependencies. 
Well, only for some methods you may require some python packages, but feel free to rewrite if you want to omit these.

Here is a stub of a simulation model python file:


```python
import statistics
import math
import random
import numpy as np
from scipy.interpolate import interp1d

# linear interpolation between a set of points
def LERP(x,points):
    x_vals = np.array([ x[0] for x in points])
    y_vals = np.array([x[1] for x in points])

    if x<= x_vals[0]:
        return y_vals[0]

    if x >= x_vals[len(x_vals)-1]:
        return y_vals[len(x_vals)-1]

    f = interp1d(x_vals, y_vals)
    return float(f(x))


class simulation_model():
  def memoize(self, equation, arg):
    mymemo = self.memo[equation]
    if arg in mymemo.keys():
      return mymemo[arg]
    else:
      result = self.equations[equation](arg)
      mymemo[arg] = result

    return result

  def __init__(self):
    # Simulation Buildins
    self.dt = 0.25
    self.starttime = 1
    self.stoptime = 120
    self.equations = {
  	# Stocks 
  		
    # flows 

    # gf 
        
    #constants

    }

    self.points = {
  	 }

    self.dimensions = {
  		'Dim_Name_1': {
  			'labels': [  ],
  			'variables': [  ]
  		},
  	 }

    self.memo = {}
    for key in list(self.equations.keys()):
      self.memo[key] = {}  # DICT OF DICTS!

  def specs(self):
    return self.starttime, self.stoptime, self.dt, 'Days', 'Euler'

  def setDT(self,v):
    self.dt = v

  def setStarttime(self,v):
    self.starttime = v

  def setStoptime(self,v):
    self.stoptime = v

```

The imports are quite convenient to give you access to methods for different functions such as mathematical and scientific functions using ```math and scipy``` as well as statistical functions. Feel free to remove imports or add imports. 
This is no convention. Just make sure that you import all packages the model requires to function properly. As said before, the model should be self-contained.

The ``LERP`` methods is required for interpolation of graphical functions. For simplicity, we use ``interpol1d`` from the scipy package. Feel free to replace it. 
Then you see that we start a class ``simulation_model``. For the framework to recognize the model, **do only use** this class name. 


The ``__init__`` configures the model properties such as the start time, stop time, dt and the equations. ``equations`` is a python ``dict`` that stores all equations.
 An equation has a key and is a ``lambda`` function of the following format:
 ```
    "name_of_equations" : lambda t : do something
 ```
 
 
 Even constants have to be a lambda. For each t it just returns the same value. This means, a valid constant looks like this : `` "constant_name" : lambda t : 10000 ``.
 
 An equation usually refers to past values. This is why the most important method is the ``memoize`` method. It uses the concept of memoization to cache simulation results for each equation and point in time to avoid endless recursion.
For each equation, it fills a dictionary inside the ``self.memo``. To avoid tail-recursion you need a stop-criterion for each lambda, usually this is the start time.
To ease the understanding of the concepts used, refer to this simple example with two equations:

```
def __init__(self):
    ....
    # Setup all other things
    
    self.equations = {
        "equation_1" : lambda t : self.memoize("costant",t) if t <= self.starttime else 100 + self.memoize("equation_1",t-self.dt),
        
        "constant_1" : lambda t : 10000
    }
        
```

The ``constant_1`` equation always returns 10,000. ``equation_1`` returns 10,000 if the given t is below or equal the 
model's start time or otherwise recurse by calling the memoize method for itself and ``t-self.dt`` and add 100 to that result.
The memoize method either returns its cached value for t-dt or call the equation if the cache for t-dt is not built yet.

For storing graphical functions, we make use of the dict ``self.points``. It stores lists of (x,y) values you may use in your equations for linear interpolation 
by calling the ``LERP`` function for arbitrary x values. In this way, you avoid defining very complex functions in equations. The x values may even be the result of other equations.

Example set of points:
```
self.points = {
  		'productivity': [ [0,0.4],[0.25,0.444],[0.5,0.506],[0.75,0.594],[1,1.03400735294118],[1.25,1.119],
  		    [1.5,1.1625],[1.75,1.2125],[2,1.2375],[2.25,1.245],[2.5,1.25] ],
  	 }
```


**ATTENTION:** Please always do use the following lines to initialize the simulation model's memo as shown in the example:
```
for key in list(self.equations.keys()):
      self.memo[key] = {}
``` 

This code initializes the model's memo for each equation with an empty dictionary.
You are now able to define your own simulation model quickly. If something is missing, please do contact us!
