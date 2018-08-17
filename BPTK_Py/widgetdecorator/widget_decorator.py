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

## IMPORTS
from __future__ import print_function
import BPTK_Py.config.config as config
from BPTK_Py.logger.logger import log
from ipywidgets import interact, interactive, fixed, interact_manual
from ipywidgets import Layout
import ipywidgets as py_widgets


##

#############################
### Class widgetDecorator ###
#############################


class widgetDecorator():
    """
    This class simply decorates an output of "plotScenarios" of bptk with an arbitrary amount of sliders
    Later maybe even other interactive projects
    This is the core of the interactive plotting module

    """

    def __init__(self, bptk):
        """

        :param bptk: A live instance of bptk
        """
        self.bptk = bptk
        log("[INFO] widgetDecorator created")

    # This method will be passed over to the user and used to modify the graph output

    def plot_with_widgets(self, scenarios, equations, scenario_managers=[], kind=config.configuration["kind"],
                          alpha=config.configuration["alpha"], stacked=config.configuration["stacked"],
                          freq="D", start_date="1/1/2018", title="", visualize_from_period=0, visualize_to_period=0,
                          x_label="", y_label="",
                          series_names=[], strategy=False,
                          return_df=False, constants=[]):
        """
        Generic method for plotting with interactive widgets
        :param scenarios: names of scenarios to plot
        :param equations:  names of equations to plot
        :param scenario_managers: names of scenario managers to plot
        :param kind: type of graph to plot
        :param alpha:  transparency 0 < x <= 1
        :param stacked: if yes, use stacked (only with kind="bar")
        :param freq: frequency of time series
        :param start_date: start date for time series
        :param title: title of plot
        :param visualize_from_period: visualize from specific period onwards
        :param x_label: label for x axis
        :param y_label: label for y axis
        :param series_names: names of series to modify
        :param strategy: set True if you want to use the scenarios' strategies
        :param return_df: set True if you want to receive a dataFrame instead of the plot
        :param constants: constants to modify and type of widget (widget_type, equation_name, from, to ) --> from, to only for sliders
        :return: None
        """

        self.scenarios = self.bptk.scenario_manager_factory.get_scenarios(scenario_managers=scenario_managers,
                                                                          scenarios=scenarios)

        widget_constants = [val[1] for val in constants]

        ## Only store data and create widgets and pack them
        log("[INFO] Creating widget objects for interactive plot of scenarios {}".format(str(scenarios)))

        # Generate the widget objects
        widgets = {}
        for val in constants:
            if type(val) is tuple:
                widget_type = val[0]
            else:
                widget_type = val

            name = ""

            if widget_type.lower() == "checkbox":
                name = val[1]
                widget = py_widgets.Checkbox(description=name, value=False, disabled=False,
                                             style=config.configuration["slider_style"],
                                             layout=config.configuration["slider_layout"])

            elif widget_type.lower() == "timerange":
                name = "timerange"
                start = 0
                end = 0

                #### Find highest stoptime values
                managers = self.bptk.scenario_manager_factory.scenario_managers
                scenario_objects= []
                for manager in managers.values():
                    scenario_objects += list(manager.scenarios.values())


                for scenario in scenario_objects:
                     if scenario.model.stoptime > end:
                         end =scenario.model.stoptime

                ### Search done


                dates = [i for i in range(start + 1, end + 1)]
                options = dates
                widget = py_widgets.SelectionRangeSlider(
                    options=options,
                    index=(0, end-1),
                    description='Period:',
                    disabled=False,
                    continuous_update=False,
                    style=config.configuration["slider_style"],
                    layout=config.configuration["slider_layout"]
                )



            elif widget_type.lower() == "slider":
                name = val[1]
                start = val[2]
                end = val[3]

                if type(start) == float:

                    widget = py_widgets.FloatSlider(min=start,
                                                    max=end,
                                                    value=(end - start) / 2,
                                                    description=name,
                                                    style=config.configuration["slider_style"],
                                                    layout=config.configuration["slider_layout"],
                                                    continuous_update=False)
                else:
                    widget = py_widgets.IntSlider(min=start,
                                                  max=end,
                                                  step=1,
                                                  value=(end - start) / 2,
                                                  description=name,
                                                  style=config.configuration["slider_style"],
                                                  layout=config.configuration["slider_layout"], continuous_update=False)


            widgets[name] = widget

        # Actual method for building the widget objects and plotting.


        @interact(**widgets)
        def compute_new_plot(**kwargs):

            for widget_name, widget in kwargs.items():

                if type(widget) == tuple:
                    visualize_from_period = widget[0] - 1
                    visualize_to_period = widget[1] - 1

                elif type(widget) == bool:
                    val = 1 if widget == True else 0

                    for name, scenario_obj in self.scenarios.items():
                        scenario_obj.model.equations[widget_name] = lambda t: val
                        scenario_obj.constants[widget_name] = val
                else:
                    val = widget
                    for name, scenario_obj in self.scenarios.items():
                        scenario_obj.model.equations[widget_name] = lambda t: val
                        scenario_obj.constants[widget_name] = val

                        self.bptk.reset_simulation_model(scenario_manager=scenario_obj.group, scenario=name)

            ax = self.bptk.plot_scenarios(scenarios=scenarios, equations=equations,
                                          scenario_managers=scenario_managers, kind=kind, alpha=alpha,
                                          stacked=stacked,
                                          freq=freq, start_date=start_date, title=title,
                                          visualize_from_period=visualize_from_period,
                                          visualize_to_period=visualize_to_period, x_label=x_label,
                                          y_label=y_label,
                                          series_names=series_names, strategy=strategy,
                                          return_df=return_df)

            return ax

        #return interact(compute_new_plot,**widgets)
