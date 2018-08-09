from __future__ import print_function
import BPTK_Py.config.config as config
from BPTK_Py.logger.logger import log
from ipywidgets import interact, interactive, fixed, interact_manual
import ipywidgets as widgets


#############################
### Class widgetDecorator ###
#############################

## This class simply decorates an output of "plotScenarios" of bptk with an arbitrary amount of sliders
## Later maybe even other interactive projects
## This is the core of the interactive plotting module
class widgetDecorator():
    def __init__(self, bptk):
        self.bptk = bptk
        log("[INFO] widgetFactory created")

    # This method will be passed over to the user and used to modify the graph output



    def generate_sliders(self, scenario_names, equations, scenario_managers=[], kind=config.configuration["kind"],
                         alpha=config.configuration["alpha"], stacked=config.configuration["stacked"],
                         freq="D", start_date="1/1/2018", title="", visualize_from_period=0, x_label="", y_label="",
                         series_names=[], strategy=True,
                         return_df=False, constants=[("cash.cash", 0, 10), ("earnings.earnings", 0, 10)]):

        self.scenarios = self.bptk.scenario_manager_factory.get_scenarios(scenario_managers=scenario_managers,
                                                                          scenario_names=scenario_names)

        ## Only store data and create sliders and pack them
        log("[INFO] Creating slider objects for interactive plot of scenarios {}".format(str(scenario_names)))

        self.constants = {}

        # Generate the slider objects
        sliders = {}
        for val in constants:
            name = val[0]
            start = val[1]
            end = val[2]

            if type(start) == float:
                slider = widgets.FloatSlider(min=start, max=end, value=start,description=name,style=config.configuration["slider_style"],layout=config.configuration["slider_layout"])
            else:
                slider = widgets.IntSlider(min=start, max=end, step=1, value=start, description=name,style=config.configuration["slider_style"],layout=config.configuration["slider_layout"])
            sliders[name] = slider
            self.constants[name] = start

        # @interact(a=sliders[0],b=sliders[1])

        # Actual method for building the slider objects and plotting.
        @interact(**sliders)
        def compute_new_plot(**kwargs):
            for key, value in kwargs.items():
                self.constants[key] = value

            extended_strategy = {
                "MakeYourStartUpGrow_strategy": {
                    1: self.constants
                }
            }
            self.bptk.modify_strategy_for_complex_strategy(scenarios=self.scenarios, extended_strategy=extended_strategy)
            for scenario in self.scenarios.values():
                for equation in scenario.model.memo.keys():

                    scenario.model.memo[equation] = {}


            ax = self.bptk.plot_scenarios(scenario_names=scenario_names, equations=equations,
                                          scenario_managers=scenario_managers, kind=kind, alpha=alpha,
                                          stacked=stacked,
                                          freq=freq, start_date=start_date, title=title,
                                          visualize_from_period=visualize_from_period, x_label=x_label,
                                          y_label=y_label,
                                          series_names=series_names, strategy=strategy,
                                          return_df=False)


            return None



