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

from .meta_model_creator import ModelCreator


class JSONModelParser():
    """
    Very simple JSON parser. JSON parsing is already builtin to BPTK-Py. Hence, this parser only opens the file and returns the dict
    """

    def parse_model(self, filename, silent=False):
        """
        Simple parsing method. Only loads the JSON and instantiates the Metamodel with the JSON dictionary
        :param filename: filename for JSON File
        :param silent: If True, no output
        :return:
        """
        import json

        with open(filename, 'r') as stream:
            model = json.load(stream)

        return ModelCreator(type="undefined", name="unimportant", model="unimportant", silent=silent, json_dict=model)
