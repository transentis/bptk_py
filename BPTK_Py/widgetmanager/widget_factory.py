from __future__ import print_function
import BPTK_Py.config.config as config
from BPTK_Py.visualizations.visualize import Visualizations
from BPTK_Py.logger.logger import log

from ipywidgets import interact, interactive, fixed, interact_manual
import ipywidgets as widgets

class widgetFactory():
    def __init__(self, bptk):
        self.bptk = bptk
        self.results = {}

        ## Plot config
        self.kind = config.configuration["kind"],
        self.alpha = config.configuration["alpha"]
        self.stacked = config.configuration["stacked"]
        self.freq = "D"
        self.title = ""
        self.visualize_from_period = 0
        self.x_label = ""
        self.y_label = ""





    # This method will be passed over to the user and used to modify the graph output
    def get_value(self, x):
        visualize = Visualizations()
        ax = self.results[x][self.visualize_from_period:].plot(kind=self.kind, stacked=self.stacked, figsize=config.configuration["figsize"],
                                             title=self.title,
                                             alpha=self.alpha, color=config.configuration["colors"],
                                             lw=config.configuration["linewidth"])

        ### Set axes labels and set the formats
        if (len(self.x_label) > 0):
            ax.set_xlabel(self.x_label)

        # Set the y-axis label
        if (len(self.y_label) > 0):
            ax.set_ylabel(self.y_label)

        visualize.update_plot_formats(ax)

        return None



    def generate_slider(self, scenario_names, equations, scenario_managers=[], kind=config.configuration["kind"],
                        alpha=config.configuration["alpha"], stacked=config.configuration["stacked"],
                        freq="D", start_date="1/1/2018", title="", visualize_from_period=0, x_label="", y_label="",
                        series_names=[], strategy=True,
                        return_df=False, constant="cash.cash", interval=(0, 10)):
        ## I create the results now for all values in the interval
        log("[INFO] Attempting to generate widget for scenarios: {}".format(str(scenario_names)))
        scenarios = self.bptk.scenario_manager_factory.get_scenarios(scenario_names=scenario_names,
                                                                     scenario_managers=scenario_managers)

        self.kind = kind
        self.alpha = alpha
        self.stacked = stacked
        self.freq = freq
        self.title = title
        self.visualize_from_period = visualize_from_period
        self.x_label = x_label
        self.y_label = y_label

        for i in range(interval[0], interval[1]+1):


            for scenario_name, scenario in scenarios.items():
                scenario.model.memo[constant] = {}
                scenario.model.equations[constant] = lambda t: t * i

                if scenario_name not in self.results.keys():
                    self.results[scenario_name] = {}

                self.results[i] =self.bptk.plot_scenarios( scenario_names=scenario_names, equations=equations, scenario_managers=scenario_managers, kind=kind, alpha=alpha, stacked=stacked,
                       freq=freq, start_date=start_date, title=title, visualize_from_period=visualize_from_period, x_label=x_label, y_label=y_label,
                       series_names=series_names, strategy = True,
                       return_df=True)

                scenario.model.memo[constant] = {}
        slider = widgets.IntSlider(min=interval[0],max=interval[1],step=1,value=interval[0],description=constant)
        interact(self.get_value,x=slider)
        return (slider,self.get_value)



