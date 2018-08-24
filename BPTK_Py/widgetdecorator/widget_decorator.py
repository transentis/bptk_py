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
import ipywidgets as py_widgets
import numpy as np


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

    def dashboard(self, scenarios, equations, scenario_managers=[], kind=config.configuration["kind"],
                  alpha=config.configuration["alpha"], stacked=config.configuration["stacked"],
                  freq="D", start_date="", title="", visualize_from_period=0, visualize_to_period=0,
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
        :param visualize_to_period; visualize until a specific period
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

        ## Only store data and create widgets and pack them
        log("[INFO] Creating widget objects for interactive plot of scenarios {}".format(str(scenarios)))

        # Generate the widget objects
        widgets = {}
        for val in constants:
            try:
                if type(val) is tuple:
                    widget_type = val[0]
                else:
                    widget_type = val

                name = ""

                if widget_type.lower() == "checkbox":
                    if len(val) < 2:
                        raise IndexError("Too few arguments for {}".format(widget_type))

                    name = val[1]
                    widget = py_widgets.Checkbox(description=name, value=False, disabled=False,
                                                 style=config.configuration["slider_style"],
                                                 layout=config.configuration["slider_layout"])

                elif widget_type.lower() == "timerange":
                    name = "timerange"
                    start = 0
                    end = 0

                    if visualize_from_period > 0:
                        start = visualize_from_period - 1

                    if visualize_to_period > 0:
                        end = visualize_to_period

                    else:
                        #### Find highest stoptime values
                        managers = self.bptk.scenario_manager_factory.scenario_managers
                        scenario_objects = []
                        for manager in managers.values():
                            scenario_objects += list(manager.scenarios.values())

                        for scenario in scenario_objects:
                            if scenario.model.stoptime > end:
                                end = scenario.model.stoptime

                        ### Search done

                    dates = [i for i in range(start, end + 1)]
                    options = dates
                    widget = py_widgets.SelectionRangeSlider(
                        options=options,
                        index=(start, end - start),
                        description='Period:',
                        disabled=False,
                        continuous_update=False,
                        style=config.configuration["slider_style"],
                        layout=config.configuration["slider_layout"]
                    )



                elif widget_type.lower() == "slider":
                    if len(val) < 4:
                        raise IndexError("Too few arguments for {}".format(widget_type))
                    name = val[1]
                    start = val[2]
                    end = val[3]


                    if type(start) == float and len(val) == 5:
                        step = val[4]
                        precision = len(str(step).split(".")[1])

                        options = [round(x, precision) for x in list(np.arange(start, end+step, step))]
                        value = options[int((len(options)-1)/2) if (len(options)-1)%2 == 0 else int((len(options)-1)/2)+1 ]

                        widget = py_widgets.SelectionSlider(options=options,
                                                            value=value,
                                                            description=name,
                                                            style=config.configuration["slider_style"],
                                                            layout=config.configuration["slider_layout"],
                                                            continuous_update=False)

                    elif type(start) == float and len(val) < 5:
                        step = 0.1
                        widget = py_widgets.FloatSlider(min=start,
                                                        max=end,
                                                        value=(end - start) / 2,
                                                        description=name,
                                                        step=step,
                                                        style=config.configuration["slider_style"],
                                                        layout=config.configuration["slider_layout"],
                                                        continuous_update=False)
                    else:
                        step = 1
                        widget = py_widgets.IntSlider(min=start,
                                                      max=end,
                                                      step=step,
                                                      value=(end - start - step) / 2,
                                                      description=name,
                                                      style=config.configuration["slider_style"],
                                                      layout=config.configuration["slider_layout"], continuous_update=False)

                widgets[name] = widget

            except TypeError as e:
                log(
                    "[ERROR] Problem creating widget with a TypeError. Please do only use numbers for the widget limits and text in double quotes for names and widget type! Message: \"{}\"".format(
                        str(e)))
            except IndexError as e:
                log("[ERROR] Problem creating widget with a ValueError. Did you supply all required fields? Message: \"{}\"".format(str(e)))
            except Exception as e:
                log("[ERROR] Problem creating widget: \"{}\". Error type:  {}".format(str(e),str(type(e))))

        param_visualize_from = visualize_from_period
        param_visualize_to = visualize_to_period

        @interact(**widgets)
        def compute_new_plot(**kwargs):
            """
            Actual method that we hand over to interact. Evaluates the widget values and creates the plots
            :param kwargs: widgets dict : {name : value}
            :return: None
            """
            visualize_from_period = param_visualize_from
            visualize_to_period = param_visualize_to
            for widget_name, widget in kwargs.items():

                if type(widget) == tuple:
                    visualize_from_period = widget[0]
                    visualize_to_period = widget[1] + 1

                elif type(widget) == bool:
                    widget_val = 1 if widget == True else 0

                    for name, scenario_obj in self.scenarios.items():
                        scenario_obj.model.equations[widget_name] = lambda t: widget_val
                        scenario_obj.constants[widget_name] = widget_val
                else:
                    widget_val = widget
                    for name, scenario_obj in self.scenarios.items():
                        scenario_obj.model.equations[widget_name] = lambda t: widget_val
                        scenario_obj.constants[widget_name] = widget_val

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

            if return_df:
                return ax

        # return interact(compute_new_plot,**widgets)
