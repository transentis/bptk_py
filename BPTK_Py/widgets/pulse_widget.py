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


import ipywidgets as widgets
import numpy as np

from IPython.display import clear_output, display


class PulseDashboard():
    """
    Class to create dashboard for PULSE functions
    """

    def flatten(self, l):
        """
        Flatten a list of lists
        :param l: list
        :return: list
        """
        if type(l) == list:
            output = []
            for elem in l:
                output = output + self.flatten(elem)
            return output
        else:
            return [l] if l is not None else [""]

    def del_duplicates(self, l):
        """
        Delete duplicates of a list
        :param l: list
        :return: list
        """
        returns = []
        for val in l:
            if val not in returns:
                returns += [val]

        return returns

    def __init__(self, scenarios, scenario_managers, bptk):
        """

        :param scenarios: name of scenarios
        :param scenario_managers: name of scenario managers
        :param bptk: bptk instance
        """
        self.output = widgets.Output()
        self.scenarios = scenarios
        self.bptk = bptk
        self.scenario_managers = scenario_managers

        self.scenario_objs = self.bptk.scenario_manager_factory.get_scenarios(scenario_managers=scenario_managers,
                                                                              scenarios=scenarios)

        constant_list = self.del_duplicates(
            self.flatten([list(scenario_obj.model.equations.keys()) for scenario_obj in self.scenario_objs.values()]))

        constant_list = sorted(constant_list.copy())

        self.variable = widgets.Dropdown(options=constant_list)
        self.number_initial = widgets.Text(placeholder="initial value")
        self.number_pulse_value = widgets.Text(placeholder="pulse value")
        self.number_frequency = widgets.Text(placeholder="frequency")
        self.number_first_tick = widgets.Text(placeholder="first activation")
        self.keep_strategy = widgets.Checkbox(value=True, description="Keep existing strategy")

        self.number_items = [self.number_initial, self.number_pulse_value, self.number_frequency,
                             self.number_first_tick]

        button_layout = widgets.Layout(width="100%")

        self.button_start = widgets.Button(description="Apply Strategy", layout=button_layout)
        self.button_start.on_click(self.on_click)

        vbox_left = widgets.VBox([widgets.Label("Variable"), self.variable])
        vbox_middle_1 = widgets.VBox([widgets.Label("initial value"), self.number_initial])
        vbox_middle_2 = widgets.VBox([widgets.Label("pulse value"), self.number_pulse_value])
        vbox_middle_3 = widgets.VBox([widgets.Label("frequency"), self.number_frequency])
        vbox_right = widgets.VBox([widgets.Label("first activation"), self.number_first_tick])
        vbox_placeholder = widgets.VBox([widgets.Label(""), self.keep_strategy])

        hbox_top = widgets.HBox([vbox_left, vbox_middle_1, vbox_middle_2, ])
        hbox_middle = widgets.HBox([vbox_middle_3, vbox_right, vbox_placeholder])

        main_vbox = widgets.VBox([hbox_top, hbox_middle, ])
        self.out_vbox = widgets.VBox([main_vbox, self.button_start, self.output])

    def show(self):
        display(self.out_vbox)

    def on_click(self, b):
        """
        Onclick method for button. Create strategies and aadd to BPTK
        :param b: button
        :return: None
        """
        with self.output:
            clear_output()
        error = False

        # Error messages for human
        for elem in self.number_items:
            try:
                val = float(elem.value)
            except ValueError as e:
                with self.output:
                    print("[Error] No valid numeric value given for {}".format(elem.placeholder))

                error = True

        # Overwrite existing strategy
        if not self.keep_strategy.value:
            for manager in self.scenario_managers:
                for scenario in self.scenarios:
                    self.bptk.reset_scenario(scenario=scenario, scenario_manager=manager)

            # Get the updated objects!
            self.scenario_objs = self.bptk.scenario_manager_factory.get_scenarios(
                scenario_managers=self.scenario_managers,
                scenarios=self.scenarios, scenario_manager_type="sd")

        # Create strateg(ies)
        if not error:
            strategies = {}
            equation = self.variable.value

            # Create actual strategy
            for scenario in self.scenarios:
                strategies[scenario] = {}

                first_moment = float(self.number_first_tick.value)
                pulse_frequency = float(self.number_frequency.value)
                strategies[scenario]['0'] = {}
                strategies[scenario]['0'][equation] = float(self.number_initial.value)

                for i in np.arange(first_moment,
                                   self.scenario_objs[scenario].model.stoptime + self.scenario_objs[scenario].model.dt,
                                   pulse_frequency):
                    t = round(i, 2)
                    dt = self.scenario_objs[scenario].model.dt
                    strategies[scenario][t] = {}
                    strategies[scenario][t + dt] = {}
                    strategies[scenario][t][equation] = float(self.number_pulse_value.value)
                    strategies[scenario][t + dt][equation] = float(self.number_initial.value)

            # Add strategy
            self.bptk.modify_strategy(scenarios=self.scenario_objs, extended_strategy=strategies)

            # Reset memo of simulations
            for manager in self.scenario_managers:
                for scenario in self.scenarios:
                    self.bptk.reset_simulation_model(scenario_manager=manager, scenario=scenario)

            # print output
            with self.output:
                print("Pulse function created for variable {}".format(str(equation)))
                print(
                    "scenarios: {}".format(str(self.del_duplicates(self.scenarios)).replace("[", "").replace("]", "")))
                print("scenario managers:".format(str(self.scenario_managers)))

                if self.keep_strategy.value:
                    print("Keeping the existing strategy. May not overwrite previously-created PULSE functions!")
