import pandas as pd
import BPTK_Py.config.config as config
from BPTK_Py.logger.logger import log

class Visualizations():
    #Scenarios comes as scenario object dict, equations as a dict: { equation : [scenario1,scenario2...]}
    def generate_plottable_df(self, scenarios, equations, start_date="1/1/2018", freq="D", series_names=[]):
        scenario_names = list(scenarios.keys())

        ## Generate df to plot
        plot_df = pd.DataFrame()

        if len(scenarios.keys()) > 1: # If we see more than one scenario, we will attach the scenario name to each Series name.
            for scenario in scenarios.keys():
                df = scenarios[scenario].result

                for equation in equations.keys():
                    if scenarios[scenario].name in equations[equation]:

                        series = df[equation]
                        series.name = scenario + "_" + equation
                        plot_df[series.name] = series
        else:
            scenario = scenarios[list(scenarios.keys())[0]]
            df = scenario.result

            for equation in equations.keys():
                if scenario.name in equations[equation]:
                    series = df[equation]
                    series.name = equation
                    plot_df[series.name] = series

        plot_df.index= pd.date_range(start_date, periods=len(plot_df),freq=freq)


        # Process series name overrides as specified by user. Will traverse the series as they are in the DF
        # Usually this shold follow the order of the equations!
        i = 0
        columns = list(plot_df.columns)
        new_columns = {}

        for name in series_names:
            try:
                if len(name) > 0:
                    new_columns[columns[i]] = name
                i += 1
            except:
                log("[WARN] User gave more series names than scenarios. This is usually not a problem.")
        plot_df.rename(columns=new_columns, inplace=True)



        return plot_df

    def update_plot_formats(self,ax):

        ylabels = [format(label, ',.0f') for label in ax.get_yticks()]
        ax.set_yticklabels(ylabels)

