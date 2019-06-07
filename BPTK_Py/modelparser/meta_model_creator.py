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




class ModelCreator():
    """
    This class creates a meta model for the scenario. You can export this model to BPTK-Compliant JSON format for further processing. It comes wiht its own serialization mechanism
    For now, it only supports ABM models. SD support is planned for the future!
    """

    def __init__(self, name, type="abm", model="model", silent=False,json_dict = None):
        """

        :param name: Name of the scenario manager
        :param type: ABM or SD
        :param model: link to model file, if any. Uses Python dot notation
        :param silent: If True, no output will be made during parsing
        """

        self.name = name

        self.type = type
        self.datacollector = None

        self.json_dict = json_dict

        # Handle cases where the user does not give a package link, rather than a class name only
        if len(model) == 1:
            model = "model." + model

        self.model = model
        self.silent = silent

        self.properties = []
        self.scenarios = {
        }

    def add_scenario(self, name, starttime, stoptime, dt,properties={},datacollector=None):
        self.scenarios[name] = {
            "runspecs": {
                "starttime": starttime,
                "stoptime": stoptime,
                "dt": dt

            },
            "agents": [],
            "properties": properties
        }
        self.datacollector = datacollector
        return self

    def add_agent(self, agent, scenario):
        """
        Add one serializable agent object
        :param agent: Instance of Serializable Agent
        :param scenario: Name of scenario to add agent to
        :return:
        """
        self.scenarios[scenario]["agents"] += [agent]

    def create_model(self):
        """
        Serialization method. Outputs the model and all of its components as dictionary
        :return: Dictionary
        """

        if self.type == "sd" or self.type=="undefined":
            return None, self.json_dict

        def import_class(name):
            components = name.split('.')
            mod = __import__(components[0])
            for comp in components[1:]:
                mod = getattr(mod, comp)
            return mod

        from copy import deepcopy
        model_to_dump = deepcopy(self)

        def serialize(obj):
            output = {}
            try:
                elems = vars(obj)
            except:
                elems = obj
                output = elems

            if type(elems) == list:
                output = []
                for elem in elems:
                    output += [serialize(elem)]

            elif type(elems) == dict:
                for key, value in elems.items():
                    output[key] = serialize(value)

            return output

        model = model_to_dump.model


        ### Create the import statements for the Model
        agents = []

        for key, value in model_to_dump.scenarios.items():
            agents += value["agents"]


        ##  Agent factories erzeugen
        from BPTK_Py import Model
        from BPTK_Py.logger import log
        BPTK_Mod = None

        try:
            if (model!=model_to_dump.name):
                import importlib
                split = model.split(".")
                className = split[len(split) - 1]
                packageName = '.'.join(split[:-1])


                mod = importlib.import_module(packageName)
                class_object = getattr(mod,className)


                if self.datacollector:
                    BPTK_Mod = class_object(data_collector=self.datacollector if self.datacollector else None)
                else:
                    BPTK_Mod = class_object()
        except Exception as e:
            print(e)
            print("ERROR")
            log("[WARN] Could not load specific model class. Using standard Model")
            if self.datacollector:
                BPTK_Mod = Model(data_collector=self.datacollector)
            else:
                BPTK_Mod = Model()

        classes_to_type = {}

        for agent in agents:
            class_obj = agent.classname
            name = agent.name

            class agent_Fac():
                """
                Helper class that encapsulates the agent factory method. Needed to store agent type object
                """

                def __init__(self,class_obj,agent_type):
                    import copy
                    self.className=copy.deepcopy(class_obj)
                    self.agent_type = copy.deepcopy(agent_type)

                def factory(self, agent_id, model, properties):
                    """
                    Actual Agent factory method
                    :param agent_id: int, given by Model
                    :param model: BPTK_py.Model
                    :param properties: Dictionary of Python properties for agent
                    :return: Agent instance
                    """


                    from BPTK_Py.logger import log
                    import importlib
                    split = self.className.split(".")
                    className = split[len(split) - 1]
                    packageName = '.'.join(split[:-1])


                    try:
                        mod = importlib.import_module(packageName)
                    except ModuleNotFoundError as e:
                        log(
                            "[ERROR] File {}.py not found. Probably this is due to a faulty configuration or you forget to delete one. Skipping.".format(
                                packageName.replace(".", "/")))
                        return
                    try:
                        scenario_class = getattr(mod, className)
                    except AttributeError as e:
                        log(
                            "[ERROR] Could not find class {} in {}. Probably there is still a configuration that you do not use anymore. Skipping.".format(
                                class_obj, packageName))
                        return

                    return scenario_class(agent_id=agent_id,model=model,properties=properties,agent_type=self.agent_type)


            fac = agent_Fac(class_obj,name)
            BPTK_Mod.register_agent_factory(name,
                                            fac.factory)

        # We also return this serialized model as Dictionary as many internal mechanisms rely on dictionary data
        return BPTK_Mod, {self.name: serialize(model_to_dump)}


##################
### AGENT SPECS ##
##################

'''
The following code wraps the agent specs for each agent type. To add your own agent, instantiate sub classes with specific predefined properties
'''


class serializable_agent():
    """
    This class wraps certainagent properties that will be evaluated by BPTK-Py during runtime-
    """

    def __init__(self, name, count, step, properties=None, classname=None, previous=None, target=None, silent=False):
        import copy
        self.count = count
        self.step = step
        self.name = name
        self.properties = {} if properties is None else copy.deepcopy(properties)
        self.classname = "BPTK_Py.Agent" if not classname else classname
        self.silent = silent

        if previous:
            self.set_previous(previous)

        if target:
            self.set_target(target)

    def set_previous(self, name):
        """
        For graphs of agents: Set previous agent group
        :param name:
        :return:
        """
        return self.set_property(name="previous", type="String", value=name)

    def set_target(self, name):
        """
        For graphs of agents: Set next agent group
        :param name:
        :return:
        """
        return self.set_property(name="target", type="String", value=name)

    def set_property(self, name, type, value):
        """
        Set a property
        :param name: Name of property
        :param type: Type of property
        :param value: Value of property
        :return:
        """
        if not self.silent:
            print("Setting {} of {} to {}".format(name, self.name, value))
        self.properties[name] = {"type": type, "value": value}
        return self