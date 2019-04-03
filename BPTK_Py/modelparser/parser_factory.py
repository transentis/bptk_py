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

from ..logger import log
from .yaml_model_parser import YAMLModelParser
from .json_model_parser import JSONModelParser

parsers = {"yml": YAMLModelParser, "yaml": YAMLModelParser,"json": JSONModelParser}

def ParserFactory(filename):
    """
    Returns the correct parser class for the given file, depending on the filetype.
    For adding new parsers, please configure above Dictionary
    :param filename: Filename of file containing the model definition
    :return: None
    """
    ending = filename.split(".")[-1:][0].lower()

    try:

        return parsers[ending]
    except KeyError as e:
        log("[ERROR] No parser available for filetype {}".format(ending))

