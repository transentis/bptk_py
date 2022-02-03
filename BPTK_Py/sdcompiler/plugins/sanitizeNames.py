#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2019 transentis labs GmbH
# MIT License

import re

def sanitizeName(name):
    """
    Make the name beautiful
    :param name:
    :return:
    """

    def snake_to_camel(word):
        lowercase_first_letter = lambda s: s[:1].lower() + s[1:] if s else ''
        return lowercase_first_letter(''.join(x.capitalize() for x in word.split('_')))

    name = name\
        .replace("\n", " ") \
        .replace('\\n', " ")\
        .replace(".",'.')\
        .replace("\"","")\
        .replace("-","")\
        .replace("'","")\
        .replace(" ","_")

    name = re.sub(r"_+","_",name) # Replace multiple underscore with one underscore
    name = re.sub(r"[ ]+", ' ', name) # Many whitespaces to exactly one


    # No leading "."
    if len(name) > 0 and  name[0] == ".": name = name[1:]

    ## Camel Casing
    name = snake_to_camel(name)

    return name

