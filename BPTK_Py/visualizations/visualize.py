

import BPTK_Py.config.config as config
import statistics
import pandas as pd

class visualizer():





    def plot(self,df,return_df,visualize_from_period,visualize_to_period,stacked,kind,title,alpha,x_label,y_label,start_date="1/1/2018", freq="D",series_names={}):

        if not start_date == "":
            df.index= pd.date_range(start_date, periods=len(df),freq=freq)

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
                ax = df.iloc[visualize_from_period:].plot(kind=kind, stacked=stacked, figsize=config.configuration["figsize"],
                                                 title=title,
                                                 alpha=alpha, color=config.configuration["colors"],
                                                 lw=config.configuration["linewidth"])

            elif visualize_from_period == visualize_to_period:
                print("[INFO] No data to plot for period t={} to t={}".format(str(visualize_from_period),str(visualize_to_period)))
                return None

            else:
                if visualize_to_period +1 > len(df):
                    visualize_to_period = len(df)

                ax = df.iloc[visualize_from_period:visualize_to_period].plot(kind=kind, stacked=stacked,
                                                     figsize=config.configuration["figsize"],
                                                     title=title,
                                                     alpha=alpha, color=config.configuration["colors"],
                                                     lw=config.configuration["linewidth"])
            ### Set axes labels and set the formats
            if (len(x_label) > 0):
                ax.set_xlabel(x_label)

            # Set the y-axis label
            if (len(y_label) > 0):
                ax.set_ylabel(y_label)

            for ymaj in ax.yaxis.get_majorticklocs():
                ax.axhline(y=ymaj, ls='-',alpha=0.05,color=(34.1 / 100, 32.9 / 100, 34.1 / 100))


            self.update_plot_formats(ax)

        ### If user wanted a dataframe instead, here it is!
        if return_df:
            if visualize_to_period == 0:
                return df.iloc[visualize_from_period:]
            elif visualize_from_period == visualize_to_period:
                print("[INFO] No data for period t={} to t={}".format(str(visualize_from_period + 1),
                                                                              str(visualize_to_period + 1)))
                return None
            else:
                return df.iloc[visualize_from_period:visualize_to_period]


    def update_plot_formats(self,ax):
        """
        Configure the plot formats for the labels. Generates the formatting for y labels
        :param ax:
        :return:
        """
        ylabels_mean = statistics.mean(ax.get_yticks())

        # Override the format based on the mean values
        if ylabels_mean <= 2.0 and ylabels_mean >= -2.0:
            ylabels = [format(label, ',.2f') for label in ax.get_yticks()]

        elif ylabels_mean <= 10.0 and ylabels_mean >= -10.0:
            ylabels = [format(label, ',.1f') for label in ax.get_yticks()]

        else:
            ylabels = [format(label, ',.0f') for label in ax.get_yticks()]

        ax.set_yticklabels(ylabels)

