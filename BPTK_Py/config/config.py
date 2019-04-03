#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018 transentis labs GmbH
# MIT License


import os

from ipywidgets import Layout

import BPTK_Py



##################################
## BPTK_Py Global Configuration ##
##################################

### Plot Style settings
## matplotlib style setting
matplotlib_rc_settings = {
    "font.family": "DejaVu Sans",
    "axes.titlesize": 35,
    "axes.labelsize": 25,
    "lines.linewidth": 3,
    "lines.markersize": 15,
    "xtick.labelsize": 15,
    "ytick.labelsize": 15,
    "figure.figsize": (20, 10),
    'legend.fontsize': 17,
}

transentis_colors = {
    "blue": (0 / 100, 33.3 / 100, 45.1 / 100),
    "olive": (60.8 / 100, 60.8 / 100, 5.9 / 100),
    "orange": (100 / 100, 51 / 100, 0 / 100),
    "grey": (34.1 / 100, 32.9 / 100, 34.1 / 100),
    "red": (70.6 / 100, 0 / 100, 23.5 / 100),
    "beige": (68.6 / 100, 60.8 / 100, 39.2 / 100),
    "turquoise": (0 / 100, 58.8 / 100, 58.8 / 100),

}

sd_py_compiler_root = str(os.path.dirname(BPTK_Py.__file__)) + "/sd-compiler"

configuration = {
    "sd_py_compiler_root": sd_py_compiler_root,
    "bptk_Py_module_path": os.path.dirname(BPTK_Py.__file__),

    # Graphic settings
    "matplotlib_rc_settings": matplotlib_rc_settings,
    "colors": [color for color in transentis_colors.values()],
    "kind": "area",
    "stacked": False,
    "figsize": matplotlib_rc_settings["figure.figsize"],
    "alpha": 0.25,
    "linewidth": matplotlib_rc_settings["lines.linewidth"],

    # Relative path to scenario storage
    "scenario_storage": "scenarios/",
    "slider_style": {'description_width': '50%'},
    "slider_layout": Layout(width='100%', position="left"),

    # Log mode. List of strings. Possible values: "print" / "logfile"
    "log_modes": ["logfile"],
    "log_file": "bptk_py.log"
}





loglevel = "WARN"