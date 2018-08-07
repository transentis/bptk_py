##################################
## BPTK_Py Global Configuration ##
##################################


### LOG MODES. Simple list. Default: ["logfile"], not outputting the log to stdout. Use "print" to log to stdout
log_modes = ["print", "logfile"]
log_modes = ["logfile"]

### File to log to
log_file = "simulator_log.log"

## Location of the scenarios (relative path from top level of working dir)
scenario_storage = "scenarios/"

### SD-Py-Compiler Location


### Style settings
## matplotlib style setting
matplotlib_rc_settings = {
    "font.family": 'AutographScriptEFOP-Lig',
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

#colors = [transentis_colors[color] for color in transentis_colors.keys()]
#kind = "area"
#stacked = False
#figsize = matplotlib_rc_settings["figure.figsize"]
#alpha = 0.25
#linewidth = matplotlib_rc_settings["lines.linewidth"]

configuration = {
    "sd_py_compiler_root" : "~/Code/sd-compiler/",
    "matplotlib_rc_settings": matplotlib_rc_settings,
    "colors": [transentis_colors[color] for color in transentis_colors.keys()],
    "kind": "area",
    "stacked": False,
    "figsize": matplotlib_rc_settings["figure.figsize"],
    "alpha": 0.25,
    "linewidth": matplotlib_rc_settings["lines.linewidth"],
}
