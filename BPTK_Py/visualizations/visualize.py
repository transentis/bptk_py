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



import statistics
from contextlib import contextmanager

import pandas as pd

from ..logger import log


PLOTTING_EXTRA_HINT = (
    "Plotting requires the plotting extra. "
    "Install it with: pip install bptk-py[plotting]"
)


#: The keys of `config.configuration` that describe how a chart is drawn, as opposed to
#: where models and logs live. Everything in this list belongs to `plotting_config`.
PLOT_SETTING_KEYS = ("kind", "stacked", "alpha", "colors", "figsize", "linewidth")

#: Two of those exist under two names: a convenience key in `configuration` and a
#: matplotlib rc setting. They are kept in step, in both directions, so that setting
#: either form reaches the chart.
MIRRORED_SETTINGS = {"figsize": "figure.figsize", "linewidth": "lines.linewidth"}


class PlottingConfig:
    """The single source of truth for how BPTK draws.

    Every plot method reads this - `Element.plot()`, `Visualizer.plot()` and
    `AgentDataCollector.plot_agent_stats()` alike. Before, they disagreed: the two
    methods that had no `bptk()` in reach read the package defaults out of
    `BPTK_Py.config.config`, while `Visualizer` read a deepcopy held by whichever
    `bptk()` instance owned it, so `bptk(configuration=...)` reached one and not the
    others. The matplotlib rc settings appeared to reach all three only because the
    constructor wrote them into the global `plt.rcParams`, which restyled unrelated
    charts as a side effect.

    Process-wide by design: `bptk(configuration=...)` writes here, so a configuration
    given to one instance applies to every plot in the process, whichever object draws
    it. Where a single chart should differ, pass `matplotlib_rc_settings` to that plot
    call instead - it is laid over this configuration for the one draw and leaves it
    alone. `reset()` gets back to the package defaults.

    What stays out of it: charts drawn outside BPTK. The settings are applied through
    `plt.rc_context` around our own drawing calls, never written into the global
    `plt.rcParams`.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        """Restore the package defaults. Mainly for tests and notebooks."""
        from copy import deepcopy
        from BPTK_Py.config import config as default_config

        self.matplotlib_rc_settings = deepcopy(default_config.matplotlib_rc_settings)
        self.settings = {key: deepcopy(default_config.configuration[key]) for key in PLOT_SETTING_KEYS}

    def update(self, configuration):
        """Take over the plot-relevant entries of a `configuration` dictionary.

        The two mirrored settings are kept in step here: `figsize` and `figure.figsize`
        name the same thing, as do `linewidth` and `lines.linewidth`. Whichever form is
        given wins, and the convenience key wins over the rc form when a call gives both.
        """
        if not configuration:
            return
        for key in PLOT_SETTING_KEYS:
            if key in configuration:
                self.settings[key] = configuration[key]
        if "matplotlib_rc_settings" in configuration:
            self.matplotlib_rc_settings = dict(configuration["matplotlib_rc_settings"])
            # The rc form reaches the draw only through the mirror: the plot calls pass
            # figsize and lw as explicit arguments, and an explicit argument beats an rc
            # setting. Without this, setting figure.figsize did nothing at all.
            for key, rc_key in MIRRORED_SETTINGS.items():
                if rc_key in self.matplotlib_rc_settings:
                    self.settings[key] = self.matplotlib_rc_settings[rc_key]
        for key, rc_key in MIRRORED_SETTINGS.items():
            if key in configuration:
                self.settings[key] = configuration[key]
                self.matplotlib_rc_settings[rc_key] = configuration[key]

    def resolved(self, matplotlib_rc_settings=None):
        """The effective settings for one drawing call.

        Same mirror as `update`, for the per-call overrides: `matplotlib_rc_settings` on a
        plot call can name `figure.figsize` or `lines.linewidth`, and those have to reach
        the explicit arguments the call passes on.
        """
        settings = dict(self.settings)
        if matplotlib_rc_settings:
            for key, rc_key in MIRRORED_SETTINGS.items():
                if rc_key in matplotlib_rc_settings:
                    settings[key] = matplotlib_rc_settings[rc_key]
        return settings

    def __getitem__(self, key):
        return self.settings[key]


#: Process-wide plotting configuration. `bptk(configuration=...)` updates it.
plotting_config = PlottingConfig()


@contextmanager
def bptk_style(matplotlib_rc_settings=None):
    """Apply the matplotlib settings from `plotting_config` for one drawing call.

    Scoped to the draw rather than to the process, which is what keeps charts drawn
    outside BPTK untouched: constructing a `bptk()` no longer restyles them, and our own
    plots look right whether or not such an object was ever built.

    Args:
        matplotlib_rc_settings: Dict (Default None).
            Settings for this one call, laid over the central configuration rather than
            replacing it - pass only the keys that should differ. `plotting_config` stays
            as it is, so the next plot is styled centrally again.
    """
    import matplotlib.pyplot as plt

    settings = plotting_config.matplotlib_rc_settings
    if matplotlib_rc_settings:
        settings = {**settings, **matplotlib_rc_settings}

    with plt.rc_context(settings):
        yield


def require_matplotlib():
    """Raise a self-explanatory error when matplotlib is not installed.

    matplotlib ships as `bptk-py[plotting]`. Plotting itself goes through
    `df.plot()`, so without this check a missing extra surfaces as an ImportError
    from inside pandas rather than as an instruction.

    Mirrors `compile_xmile` in `BPTK_Py/sdcompiler/__init__.py`: the package that
    owns an optional capability owns the message for it.
    """
    try:
        import matplotlib  # noqa: F401
    except ImportError as error:
        raise ImportError(PLOTTING_EXTRA_HINT) from error


class visualizer():
    """
    Class for building plots from dataframes. Includes capabilities to produce time series data.
    Can also only modify dataframes to generate time series and return the modified dataframe
    """

    def __init__(self,config=None):
        self.config = config

    def plot(self, df, return_df, visualize_from_period, visualize_to_period, stacked, kind, title, alpha, x_label,
             y_label, start_date="1/1/2018", freq="D", series_names={},format="plot",
             matplotlib_rc_settings=None):
        """
        Plot method. Creates plots from dataframes
        :param df: DataFrame input
        :param return_df: Flag. If true return a dataFrame and do not plot (default: False)
        :param visualize_from_period: visualize from a specific t (default: 0)
        :param visualize_to_period:  visualize until a specific t (default: model's stoptime)
        :param stacked: If True, use stacked series (default: False)
        :param kind: 'area' or 'line' plot (ldefault: area)
        :param title: Title of plot
        :param alpha: Alpha of series (default: see config!)
        :param x_label: x_label of plot
        :param y_label: y_label of plot
        :param start_date: Start date for time series
        :param freq: Frequency setting for time series
        :param series_names: series renaming patterns
        :param matplotlib_rc_settings: matplotlib settings for this call only, laid over
            the central plotting_config rather than replacing it (default: None)
        :return: depends on format flag: either just a plot, which formally returns nothing, or Matplotlib axes, or a dataframe
        """

        if not kind:
            kind=plotting_config["kind"]

        if not stacked:
            stacked = plotting_config["stacked"]

        if not alpha:
            alpha = plotting_config["alpha"]

        if not start_date == "":
            df.index = pd.date_range(start_date, periods=len(df), freq=freq)

        series_names_keys = series_names.keys()

        if len(series_names) > 0:


            new_columns = {}
            matched = set()
            for column in df.columns:
                for series_names_key in series_names_keys:
                    if series_names_key in column:
                        new_column = column.replace(series_names_key, series_names[series_names_key])
                        new_columns[column] = new_column
                        matched.add(series_names_key)

            # A key that matches no column renames nothing, and the chart keeps its raw
            # column name - which is how seven keys in the documentation went unnoticed
            # for months. A column of a multi-scenario result is called
            # `manager_scenario_equation`, so a key naming a manager the call does not
            # use, or an equation it does not plot, silently does nothing.
            unmatched = [k for k in series_names_keys if k not in matched]
            if unmatched:
                log(
                    "[WARN] series_names: {} matched no column, so nothing was renamed. "
                    "The columns are: {}".format(
                        ", ".join(repr(k) for k in sorted(unmatched)),
                        ", ".join(repr(c) for c in df.columns),
                    )
                )

            df.rename(columns=new_columns, inplace=True)

        ## If user did not set return_df=True, plot the simulation results (default behavior)
        if not (return_df or format=="df"):

            # matplotlib ships as bptk-py[plotting]. Only this branch needs it -
            # the dataframe branch below stays available without it, which is
            # what a headless server uses.
            require_matplotlib()

            # Where the axes come from. `df.plot()` goes through pyplot, which keeps
            # every figure it creates in a global registry until someone closes it -
            # fine for a script that ends, fatal for a notebook cell the reader runs
            # again and again: in Pyodide the accumulated figures exhaust the WASM
            # heap and the kernel dies mid-session, which cost the documentation 28
            # pages that stopped answering after a few clicks.
            #
            # Only for `format="axes"`, where the caller receives the axes and its own
            # environment renders them. The default path has to stay on pyplot: a
            # script or a Jupyter cell shows the figure *because* it is registered.
            # One style block around both draw branches. It has to be active while the
            # axes are built: figure size, line width and the tick label sizes are read
            # at creation, so update_plot_formats() below could not put them right.
            settings = plotting_config.resolved(matplotlib_rc_settings)
            with bptk_style(matplotlib_rc_settings):
                if format == "axes":
                    from matplotlib.figure import Figure

                    figure = Figure(figsize=settings["figsize"])
                    target_axes = figure.add_subplot(111)
                else:
                    target_axes = None

                ### Get the plot object
                if visualize_to_period == 0:

                    ax = df.iloc[visualize_from_period:].plot(kind=kind, stacked=stacked,
                                                              figsize=settings["figsize"],
                                                              title=title, ax=target_axes,
                                                              alpha=alpha, color=settings["colors"],
                                                              lw=settings["linewidth"])

                elif visualize_from_period == visualize_to_period:
                    print("[INFO] No data to plot for period t={} to t={}".format(str(visualize_from_period),
                                                                                  str(visualize_to_period)))
                    return None

                else:
                    if visualize_to_period + 1 > len(df):
                        visualize_to_period = len(df)

                    ax = df.iloc[visualize_from_period:visualize_to_period].plot(kind=kind, stacked=stacked,
                                                                                 figsize=settings["figsize"],
                                                                                 title=title, ax=target_axes,
                                                                                 alpha=alpha,
                                                                                 color=settings["colors"],
                                                                                 lw=settings["linewidth"])
                    ### Set axes labels and set the formats
                if (len(x_label) > 0):
                    ax.set_xlabel(x_label)

                    # Set the y-axis label
                if (len(y_label) > 0):
                    ax.set_ylabel(y_label)

                for ymaj in ax.yaxis.get_majorticklocs():
                    ax.axhline(y=ymaj, ls='-', alpha=0.05, color=(34.1 / 100, 32.9 / 100, 34.1 / 100))

            self.update_plot_formats(ax)

            if format=="axes":
                return ax
            else:
                return

        ### If user wanted a dataframe instead, here it is!
        elif return_df or format=="df":
            if visualize_to_period == 0:
                return df.iloc[visualize_from_period:]
            elif visualize_from_period == visualize_to_period:
                print("[INFO] No data for period t={} to t={}".format(str(visualize_from_period + 1),
                                                                      str(visualize_to_period + 1)))
                return None
            else:
                return df.iloc[visualize_from_period:visualize_to_period]



    def update_plot_formats(self, ax):
        """
        Configure the plot formats for the labels. Generates the formatting for y labels
        :param ax:
        :return:
        """
        ylabels_mean = statistics.mean(ax.get_yticks())


        # Override the format based on the mean values

        import matplotlib.ticker as ticker

        def label_format(x,pos):
            if ylabels_mean <= 2.0 and ylabels_mean >= -2.0:
                label = format(x, ',.2f')

            elif ylabels_mean <= 10.0 and ylabels_mean >= -10.0:
                label = format(x, ',.1f')

            else:
                label = format(x, ',.0f')

            return label


        ax.yaxis.set_major_formatter(ticker.FuncFormatter(func=label_format))

        ## Quick fix for incompatibility of scientific notation and ticklabels
        try:
            ax.ticklabel_format(style='plain')
        except:
            pass
