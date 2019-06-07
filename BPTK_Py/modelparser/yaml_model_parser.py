#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018 transentis labs GmbH
#

import copy

from .meta_model_creator import serializable_agent
from .meta_model_creator import ModelCreator

from BPTK_Py.logger import log


class YAMLModelParser():
    """
    Parser for YAML/YML files. Returns a modelCreator instance and the instantiated Model object
    """
    PROPMAP = {float: "Double", str: "String", int: "Integer", dict: "Dictionary"}

    def parse_model(self, filename, silent=False):
        def import_class(name):
            components = name.split('.')
            mod = __import__(components[0])
            for comp in components[1:]:
                mod = getattr(mod, comp)
            return mod

        def fullname(o):
            module = o.__class__.__module__
            if module is None or module == str.__class__.__module__:
                return o.__class__.__name__  # Avoid reporting __builtin__
            else:
                return module + '.' + o.__class__.__name__

        import yaml

        with open(filename, 'r') as stream:
            model = yaml.load(stream, Loader=yaml.FullLoader)["Model"]

        # IN CASE, USER DID NOT WRITE THE MODEL DESTINATION

        if "type" not in model.keys():
            model["type"] = "abm"

        ## HANDLE SD MODELS
        if model["type"] == "sd":

           return ModelCreator(type="sd",name="unimportant",model="unimportant",silent=silent,json_dict= model)


        if "model" not in model.keys():
            model["model"] = model["name"].lower() + "." + model["name"]

        job = ModelCreator(name=model["name"], model=model["model"], silent=silent)


        datacollector = None if "datacollector" not in model.keys() else import_class(model["datacollector"])()

        for scenario in model["scenarios"]:

            scenario_name = list(scenario.keys())[0]
            params = scenario[scenario_name]
            starttime = params["starttime"]
            duration = params["duration"]
            dt = params["dt"]


            scenario_properties =  {} if "properties" not in scenario[scenario_name].keys() else scenario[scenario_name]["properties"]


            # Let's keep it generic.
            if "nodes" in params.keys():
                params["agents"] = copy.deepcopy(params["nodes"])
                params["nodes"] = {}

            agents = {} if not "agents" in params.keys() else params["agents"]

            job.add_scenario(name=scenario_name, starttime=starttime, stoptime=duration, dt=dt,properties=scenario_properties,datacollector=datacollector)

            if agents:
                for agent in agents:
                    name = list(agent.keys())[0]
                    try:
                        agent_type = "" if "type" not in agent[name].keys() else agent[name]["type"]
                    except KeyError as e:
                        log("[ERROR] Missing type declaration for node {}".format(name))
                        raise e
                    count = 1 if "count" not in agent[name].keys() else agent[name]["count"]
                    step = 1 if "step" not in agent[name].keys() else agent[name]["step"]


                    properties = [key for key in agent[name].keys() if
                                  key.lower() not in ["type", "count", "step","classname"]]

                    try:

                        agent_class = import_class(agent_type)

                        agent_obj = agent_class(name=name, count=count, step=step, silent=silent)
                    except Exception as e:
                        agent_class = serializable_agent
                        log("[WARN] Error instantiating model. Trying the classname directive")
                        agent_obj = agent_class(name=name, count=count, step=step, silent=silent,
                                                classname=agent[name]["classname"])

                    job.add_agent(scenario=scenario_name, agent=agent_obj)

                    for property in properties:
                        prop_val = str(agent[name][property]) if type(agent[name][property]) == dict else agent[name][
                            property]

                        if type(prop_val) == str:
                            try: # We need to find dictionaries. They might be coded as String. Hence, try to find it with eval()
                                prop_type = YAMLModelParser.PROPMAP[type(eval(prop_val))]
                            except:
                                prop_type = YAMLModelParser.PROPMAP[type(prop_val)]

                        else:
                            prop_type = YAMLModelParser.PROPMAP[type(prop_val)]
                        agent_obj.set_property(property, prop_type, prop_val)


        return job


