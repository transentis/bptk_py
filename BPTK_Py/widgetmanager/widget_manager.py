import BPTK_Py.config.config as config


class widgetGenerator():
    def __init__(self, bptk):
        self.bptk = bptk
        self.results = {}

    def get_value(self, x):
        return self.results[x].plot()

    def generate_widget_data(self, scenario_names, equations, scenario_managers=[], kind=config.configuration["kind"],
                             alpha=config.configuration["alpha"], stacked=config.configuration["stacked"],
                             freq="D", start_date="1/1/2018", title="", visualize_from_period=0, x_label="", y_label="",
                             series_names=[], strategy=False,
                             return_df=False, constant="cash.cash", interval=(0, 10)):
        ## I create the results now for all values in the interval
        scenarios = self.bptk.scenario_manager_factory.get_scenarios(scenario_names=scenario_names,
                                                                     scenario_managers=scenario_managers)

        extended_strategy = {}
        for i in range(interval[0], interval[1]):

            for scenario_name, scenario in scenarios.items():
                scenario.model.equations[constant] = lambda t: i

                if scenario_name not in self.results.keys():
                    self.results[scenario_name] = {}


                self.results[i] =self.bptk.plot_scenarios( scenario_names=scenario_names, equations=equations, scenario_managers=scenario_managers, kind=kind, alpha=alpha, stacked=stacked,
                       freq=freq, start_date=start_date, title=title, visualize_from_period=visualize_from_period, x_label=x_label, y_label=y_label,
                       series_names=series_names, strategy = True,
                       return_df=True)

                scenario.model.memo[constant] = {}




