#                                                       /`-
# _                                  _   _             /####`-
#| |                                | | (_)           /########`-
#| |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
#| __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
#| |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018 transentis labs GmbH
# MIT License


import numpy as np
from scipy.interpolate import interp1d


# linear interpolation between a set of points
def LERP(x, points):
    """
    Linear interpolation between a set of points. Required for SD Lookup functions, where the stepsize is smaller than
    the interval of the points
    :param x: X value to find point for
    :param points: Points of the graphical functions
    :return: Y-value for given X
    """
    x_vals = np.array([x[0] for x in points])
    y_vals = np.array([x[1] for x in points])

    if x <= x_vals[0]:
        return y_vals[0]

    if x >= x_vals[len(x_vals)-1]:
        return y_vals[len(x_vals)-1]

    f = interp1d(x_vals, y_vals)
    return float(f(x))

