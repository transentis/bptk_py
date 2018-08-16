#                                                       /`-
# _                                  _   _             /####`-
#| |                                | | (_)           /########`-
#| |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
#| __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
#| |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018 transentis labs GmbH
#

## IMPORTS
from __future__ import print_function
import BPTK_Py.config.config as config
from BPTK_Py.logger.logger import log
from ipywidgets import interact, interactive, fixed, interact_manual

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
                          freq="D", start_date="1/1/2018", title="", visualize_from_period=0, x_label="", y_label="",
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

        widget_constants = [ val[1] for val in constants ]

        ## Only store data and create widgets and pack them
        log("[INFO] Creating widget objects for interactive plot of scenarios {}".format(str(scenarios)))

        # Generate the widget objects
        widgets = {}
        for val in constants:
            widget_type = val[0]
            name = val[1]


            if widget_type.lower() == "checkbox":
                widget = py_widgets.Checkbox(description=name, value=False, disabled=False,style=config.configuration["slider_style"],
                                                 layout=config.configuration["slider_layout"])


            elif widget_type.lower() == "slider":
                start = val[2]
                end = val[3]

                if type(start) == float:

                    widget = py_widgets.FloatSlider(min=start, max=end, value=(end - start) / 2, description=name,
                                                 style=config.configuration["slider_style"],
                                                 layout=config.configuration["slider_layout"],continuous_update=False)
                else:
                    widget = py_widgets.IntSlider(min=start, max=end, step=1, value=(end - start) / 2, description=name,
                                           style=config.configuration["slider_style"],
                                           layout=config.configuration["slider_layout"],continuous_update=False)
            widgets[name] = widget

        # Actual method for building the widget objects and plotting.

        widget_names = list(widgets.keys())
        widget_list = list(widgets.values())

        if len(widgets) == 1:

            @interact(widget1=widget_list[0])
            def compute_new_plot(widget1):

                if type(widget1) == bool:
                    widget1 = 1 if widget1 == True else 0

                for name, scenario_obj in self.scenarios.items():
                    scenario_obj.model.equations[widget_names[0]] = lambda t: widget1
                    scenario_obj.constants[widget_names[0]] = widget1
                    
                    self.bptk.reset_simulation_model(scenario_manager=scenario_obj.group, scenario=name)

                self.bptk.plot_scenarios(scenarios=scenarios, equations=equations,
                                         scenario_managers=scenario_managers, kind=kind, alpha=alpha,
                                         stacked=stacked,
                                         freq=freq, start_date=start_date, title=title,
                                         visualize_from_period=visualize_from_period, x_label=x_label,
                                         y_label=y_label,
                                         series_names=series_names, strategy=strategy,
                                         return_df=return_df)

                return None

        if len(widgets) == 2:
            @interact(widget1=widget_list[0], widget2=widget_list[1])
            def compute_new_plot(widget1, widget2):

                if type(widget1) == bool:
                    widget1 = 1 if widget1 == True else 0
                if type(widget2) == bool:
                    widget2 = 1 if widget2 == True else 0

                for name, scenario_obj in self.scenarios.items():
                    scenario_obj.model.equations[widget_names[0]] = lambda t: widget1
                    scenario_obj.constants[widget_names[0]] = widget1

                    scenario_obj.model.equations[widget_names[1]] = lambda t: widget2
                    scenario_obj.constants[widget_names[1]] = widget2

                    self.bptk.reset_simulation_model(scenario_manager=scenario_obj.group, scenario=name)

                self.bptk.plot_scenarios(scenarios=scenarios, equations=equations,
                                         scenario_managers=scenario_managers, kind=kind, alpha=alpha,
                                         stacked=stacked,
                                         freq=freq, start_date=start_date, title=title,
                                         visualize_from_period=visualize_from_period, x_label=x_label,
                                         y_label=y_label,
                                         series_names=series_names, strategy=strategy,
                                         return_df=return_df)



        if len(widgets) == 3:
            @interact(widget1=widget_list[0], widget2=widget_list[1], widget3=widget_list[2])
            def compute_new_plot(widget1, widget2, widget3):

                if type(widget1) == bool:
                    widget1 = 1 if widget1 == True else 0
                if type(widget2) == bool:
                    widget2 = 1 if widget2 == True else 0
                if type(widget3) == bool:
                    widget3 = 1 if widget3 == True else 0

                for name, scenario_obj in self.scenarios.items():
                    scenario_obj.model.equations[widget_names[0]] = lambda t: widget1
                    scenario_obj.constants[widget_names[0]] = widget1

                    scenario_obj.model.equations[widget_names[1]] = lambda t: widget2
                    scenario_obj.constants[widget_names[1]] = widget2

                    scenario_obj.model.equations[widget_names[2]] = lambda t: widget3
                    scenario_obj.constants[widget_names[2]] = widget3

                    self.bptk.reset_simulation_model(scenario_manager=scenario_obj.group, scenario=name)

                self.bptk.plot_scenarios(scenarios=scenarios, equations=equations,
                                         scenario_managers=scenario_managers, kind=kind, alpha=alpha,
                                         stacked=stacked,
                                         freq=freq, start_date=start_date, title=title,
                                         visualize_from_period=visualize_from_period, x_label=x_label,
                                         y_label=y_label,
                                         series_names=series_names, strategy=strategy,
                                         return_df=return_df)

                return None

        if len(widgets) == 4:
            @interact(widget1=widget_list[0], widget2=widget_list[1], widget3=widget_list[2], widget4=widget_list[3])
            def compute_new_plot(widget1, widget2, widget3, widget4):

                if type(widget1) == bool:
                    widget1 = 1 if widget1 == True else 0
                if type(widget2) == bool:
                    widget2 = 1 if widget2 == True else 0
                if type(widget3) == bool:
                    widget3 = 1 if widget3 == True else 0
                if type(widget4) == bool:
                    widget4 = 1 if widget4 == True else 0



                for name, scenario_obj in self.scenarios.items():
                    scenario_obj.model.equations[widget_names[0]] = lambda t: widget1
                    scenario_obj.constants[widget_names[0]] = widget1

                    scenario_obj.model.equations[widget_names[1]] = lambda t: widget2
                    scenario_obj.constants[widget_names[1]] = widget2

                    scenario_obj.model.equations[widget_names[2]] = lambda t: widget3
                    scenario_obj.constants[widget_names[2]] = widget3

                    scenario_obj.model.equations[widget_names[3]] = lambda t: widget4
                    scenario_obj.constants[widget_names[3]] = widget4

                    self.bptk.reset_simulation_model(scenario_manager=scenario_obj.group, scenario=name)

                self.bptk.plot_scenarios(scenarios=scenarios, equations=equations,
                                         scenario_managers=scenario_managers, kind=kind, alpha=alpha,
                                         stacked=stacked,
                                         freq=freq, start_date=start_date, title=title,
                                         visualize_from_period=visualize_from_period, x_label=x_label,
                                         y_label=y_label,
                                         series_names=series_names, strategy=False,
                                         return_df=return_df)

                return None

        if len(widgets) == 5:
            @interact(widget1=widget_list[0], widget2=widget_list[1], widget3=widget_list[2], widget4=widget_list[3],
                      widget5=widget_list[4])
            def compute_new_plot(widget1, widget2, widget3, widget4, widget5):

                if type(widget1) == bool:
                    widget1 = 1 if widget1 == True else 0
                if type(widget2) == bool:
                    widget2 = 1 if widget2 == True else 0
                if type(widget3) == bool:
                    widget3 = 1 if widget3 == True else 0
                if type(widget4) == bool:
                    widget4 = 1 if widget4 == True else 0
                if type(widget5) == bool:
                    widget5 = 1 if widget5 == True else 0

                for name, scenario_obj in self.scenarios.items():
                    scenario_obj.model.equations[widget_names[0]] = lambda t: widget1
                    scenario_obj.constants[widget_names[0]] = widget1

                    scenario_obj.model.equations[widget_names[1]] = lambda t: widget2
                    scenario_obj.constants[widget_names[1]] = widget2

                    scenario_obj.model.equations[widget_names[2]] = lambda t: widget3
                    scenario_obj.constants[widget_names[2]] = widget3

                    scenario_obj.model.equations[widget_names[3]] = lambda t: widget4
                    scenario_obj.constants[widget_names[3]] = widget4

                    scenario_obj.model.equations[widget_names[4]] = lambda t: widget5
                    scenario_obj.constants[widget_names[4]] = widget5

                    self.bptk.reset_simulation_model(scenario_manager=scenario_obj.group, scenario=name)

                self.bptk.plot_scenarios(scenarios=scenarios, equations=equations,
                                         scenario_managers=scenario_managers, kind=kind, alpha=alpha,
                                         stacked=stacked,strategy=False,
                                         freq=freq, start_date=start_date, title=title,
                                         visualize_from_period=visualize_from_period, x_label=x_label,
                                         y_label=y_label,
                                         series_names=series_names,
                                         return_df=return_df)

                return None
