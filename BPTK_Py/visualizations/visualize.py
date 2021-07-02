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
import pandas as pd


class visualizer():
    """
    Class for building plots from dataframes. Includes capabilities to produce time series data.
    Can also only modify dataframes to generate time series and return the modified dataframe
    """

    def __init__(self,config=None):
        self.config = config

    def plot(self, df, return_df, visualize_from_period, visualize_to_period, stacked, kind, title, alpha, x_label,
             y_label, start_date="1/1/2018", freq="D", series_names={}):
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
        :return: DataFrame or Matplotlib Subplot, depends on return_df flag
        """

        if not kind:
            kind=self.config.configuration["kind"]

        if not stacked:
            stacked = self.config.configuration["stacked"]

        if not alpha:
            alpha = self.config.configuration["alpha"]

        if not start_date == "":
            df.index = pd.date_range(start_date, periods=len(df), freq=freq)

        series_names_keys = series_names.keys()

        if len(series_names) > 0:


            new_columns = {}
            for column in df.columns:
                for series_names_key in series_names_keys:
                    if series_names_key in column:
                        new_column = column.replace(series_names_key, series_names[series_names_key])
                        new_columns[column] = new_column

            df.rename(columns=new_columns, inplace=True)

        ## If user did not set return_df=True, plot the simulation results (default behavior)
        if not return_df:

            ### Get the plot object
            if visualize_to_period == 0:

                ax = df.iloc[visualize_from_period:].plot(kind=kind, stacked=stacked,
                                                          figsize=self.config.configuration["figsize"],
                                                          title=title,
                                                          alpha=alpha, color=self.config.configuration["colors"],
                                                          lw=self.config.configuration["linewidth"])

            elif visualize_from_period == visualize_to_period:
                print("[INFO] No data to plot for period t={} to t={}".format(str(visualize_from_period),
                                                                              str(visualize_to_period)))
                return None

            else:
                if visualize_to_period + 1 > len(df):
                    visualize_to_period = len(df)

                ax = df.iloc[visualize_from_period:visualize_to_period].plot(kind=kind, stacked=stacked,
                                                                             figsize=self.config.configuration["figsize"],
                                                                             title=title,
                                                                             alpha=alpha,
                                                                             color=self.config.configuration["colors"],
                                                                             lw=self.config.configuration["linewidth"])
                ### Set axes labels and set the formats
            if (len(x_label) > 0):
                ax.set_xlabel(x_label)

                # Set the y-axis label
            if (len(y_label) > 0):
                ax.set_ylabel(y_label)

            for ymaj in ax.yaxis.get_majorticklocs():
                ax.axhline(y=ymaj, ls='-', alpha=0.05, color=(34.1 / 100, 32.9 / 100, 34.1 / 100))

            self.update_plot_formats(ax)
            return

        ### If user wanted a dataframe instead, here it is!
        elif return_df:
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