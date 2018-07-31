

import matplotlib
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd



class visualizations():
    #Scenarios comes as scenario object dict, equations as a dict: { equation : [scenario1,scenario2...]}
    def visualizeMultipleScenarios(self,scenarios, equations):
        scenario_names = list(scenarios.keys())

        ## Generate df to plot
        series_list = []
        plot_df = pd.DataFrame()
        for scenario in scenarios:
            df = scenarios[scenario].result

            for equation in equations.keys():
                if scenarios[scenario].name in equations[equation]:

                    series = df[equation]
                    series.name = scenario + "_" + equation
                    plot_df[series.name] = series

        return plot_df

            ## Create plot


    def visualizeOneScenario(self,equations):
        print("TODO")

