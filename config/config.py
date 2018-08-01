import sys
import numpy as np
import matplotlib.pyplot as plt
until = 1000

log_modes = ["print","logfile"]
log_modes = ["print"]
log_file = "simulator_log.csv"
root = "./"

## Setting the recursion limit. Python is usually very conservative here. Please be careful with this setting!
## Only change it if you observer an error regarding the recursion limit! Usually only appears if until is very high as the
## Recursion depth highly depends on this! For small simulations, no need to set it! Only if you exceed a recursion level or 1,000
#sys.setrecursionlimit(until*5)


colors = [(156/255.0,153/255.0,32/255.0),(2/255.0,86/255.0,114/255.0),(254/255.0,128/255.0,27/255.0)]