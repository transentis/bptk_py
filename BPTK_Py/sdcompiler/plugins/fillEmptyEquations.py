#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2022-2026 transentis labs GmbH
# MIT License

def fillEmptyEquations(IR):
    '''
    An element without an equation computes 0
    '''
    for name, model in IR["models"].items():
        for entity_type, entities in model["entities"].items():
            for entity in entities:
                if  entity["equation_parsed"] == []:
                    entity["equation_parsed"] = ["0"]

    return IR
