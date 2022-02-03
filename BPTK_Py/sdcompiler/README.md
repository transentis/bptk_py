# XMILE / SMILE COMPILER FOR PYTHON

## Goal
Generate Code in any arbitrary language from  XMILE / SMILE.

## How it works

This compiler works very similar to our first JS version of this tool. 
It converts XMILE / SMILE to an Intermediate Representation using a grammer, from which it creates concrete syntax for the target language. 
Finally, Jinja is used to fill templates for the target language.

For a deep dive into the functionality, refer to [Readme](https://bitbucket.org/transentis/sd-compiler/src/develop/README.md) of the original SD Compiler (Javascript).

## How to run

```
from compile import compile_xmile
compile_xmile(src="path/to/itmx.itmx", dest="path/to/output.py", target="<language>")
```

For now the compiler supports the following targets:

* ``py``: Python language
* ``json``: Returns the Intermediate Representation as unmodified JSON String. Any other compiler would require to implement a parser to get the model running in another language

The Python model is standalone and can be imported and run. Each stock / flow equation is stored in the ``equations`` dict. 
Simply use the high-level API for accessing these. The only required argument is the ``t`` you want to evaluate the model for.

Example for printing the simulation results of a stock using the ```test_models/test_time.stmx``` example model:

```python
from compile import compile_xmile
from numpy import arange

# Transpile the model to Python
compile_xmile(src="./test_models/test_time.stmx", dest="./test_models/test_time.py", target="py")

# Import the model and run one equation
from test_models.test_time import simulation_model

model = simulation_model()
starttime = model.starttime
stoptime = model.stoptime
dt = model.dt
equation = "basic.stock"

for t in arange(starttime, stoptime+dt, dt): # Iterate from start to stoptime and print the simulation results
    result_at_t = model.equation(equation, t)
    print("{}: \t{}".format(t, result_at_t ))
```

## Add new generators

Most of the time, you will touch this code if you need a new language export. Just write the required methods and builtins / Operators in [generator](generator).

Let the python generator be an inspiration: [generator/py/py.py](generator/py/py.py).

To make it visible to the compiler, simply export the method in [generator/\_\_init\_\_.py](generator/__init__.py)  with a catchy name that you also want to use for as target, e.g. "js" for Javascript. 
It is then automagically available as target in compile.

## Open Source Tools used

This compiler was only possible thanks to the following open source projects:

* [Parsimonious](https://github.com/erikrose/parsimonious)
* [Jinja2](https://palletsprojects.com/p/jinja/)

## License

[LICENSE](LICENSE)



