import pandas as pd

class visualizations():
    #Scenarios comes as scenario object dict, equations as a dict: { equation : [scenario1,scenario2...]}
    def generatePlottableDF(self, scenarios, equations,start_date="1/1/2018",freq="D"):
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


        plot_df.index= pd.date_range(start_date, periods=len(plot_df),freq=freq)
        print(plot_df)
        return plot_df

            ## Create plot


    def visualizeOneScenario(self,equations):
        print("TODO")





