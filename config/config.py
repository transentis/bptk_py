import sys
import numpy as np
import matplotlib.pyplot as plt

until = 1000

log_modes = ["print", "logfile"]
log_modes = []
log_file = "simulator_log.csv"
root = "./"

## Setting the recursion limit. Python is usually very conservative here. Please be careful with this setting!
## Only change it if you observer an error regarding the recursion limit! Usually only appears if until is very high as the
## Recursion depth highly depends on this! For small simulations, no need to set it! Only if you exceed a recursion level or 1,000
# sys.setrecursionlimit(until*5)

## Style setting
transentis_colors = {
    "orange":       (100 / 100, 51 / 100, 0 / 100),
    "grey":         (34.1 / 100, 32.9 / 100, 34.1 / 100),
    "blue":         (0 / 100, 33.3 / 100, 45.1 / 100),
    "turquoise":    (0 / 100, 58.8 / 100, 58.8 / 100),
    "red":          (70.6 / 100, 0 / 100, 23.5 / 100),
    "beige":        (68.6 / 100, 60.8 / 100, 39.2 / 100),
    "olive":        (60.8 / 100, 60.8 / 100, 5.9 / 100)
}

colors = [transentis_colors[color] for color in transentis_colors.keys()]
kind = "area"
stacked = True
figsize = (10, 10)
alpha = 0.3
linewidth = 4


## matplotlib style setting


matplotlib_rc_settings = {
    'font.family': "AutographScriptEFOP-Lig",
    "axes.titlesize": 18,
    "axes.labelsize": 10,
    "lines.linewidth": 3,
    "lines.markersize": 10,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "figure.figsize": (12, 10)
}
