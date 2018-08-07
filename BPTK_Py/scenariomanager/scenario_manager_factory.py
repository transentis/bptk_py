
class ScenarioManagerFactory():
    def __init__(self):
        self.scenario_managers= {}

        def readScenario(self, filename=""):
            if len(filename) > 0:
                json_data = open(filename, encoding="utf-8").read()
                json_dict = dict(json.loads(json_data))
                scenarios = {}
                for group_name in json_dict.keys():

                    group = group_name
                    model_name = json_dict[group_name]["model"]
                    scen_dict = json_dict[group_name]["scenarios"]
                    source = ""
                    if "source" in json_dict[group_name].keys():
                        source = json_dict[group_name]["source"]
                    ## Replace string keys as int

                    for scenario_name in scen_dict.keys():
                        sce = simulationScenario(group=group, model_name=model_name,
                                                 dictionary=scen_dict[scenario_name], name=scenario_name, source=source)
                        scenarios[scenario_name] = sce

                return scenarios
            else:
                print("[ERROR] Attempted to load a scenario manager without giving a filename. Skipping!")

        def get_available_scenarios(self, path=config.configuration["scenario_storage"], scenario_managers=[]):
            scenarios = {}
            for infile in glob.glob(os.path.join(path, '*.json')):
                if len(scenarios.keys()) > 0:
                    scenarios_new = self.__readScenario(infile)
                    for key in scenarios_new.keys():
                        scenarios[key] = scenarios_new[key]
                else:
                    scenarios = self.__readScenario(infile)

                # If the scenario contains a model and we do not already have a monitor for the scenario, start a new one and store it
                for name, scenario in scenarios.items():

                    if not scenario.source is None and not scenario.source in self.scenario_monitors.keys():
                        self.__add_monitor(scenario.source, scenario.model_name)
                    log("[INFO] Successfully loaded scenario {} from {}".format(scenario.name, str(infile)))

                    if not name in self.scenarios.keys():
                        self.scenarios[name] = scenario

            if len(scenario_managers) > 0:
                return {key: value for key, value in self.scenarios.items() if value.group in scenario_managers}

            else:
                return self.scenarios