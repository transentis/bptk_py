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

def resolve(expression, entity):
    '''
    This function traverses the AST and replaces the SELF identifier by the entity's name
    '''

    if type(expression) is str or type(expression) is float:
        return expression

    if type(expression) is list:
        return [resolve(elem, entity) for elem in expression]

    if type(expression) is dict:
        name_ = expression["name"]
        type_ = expression["type"]

        # SELF in a module has the module's name in front of it by now: `inner.self`
        if (name_ == "self" or name_.endswith(".self")) and type_ in ("identifier", "array"):
            expression["name"] = entity["name"]

        if "args" in expression.keys():
            expression["args"] = resolve(expression["args"], entity)
        return expression
    return expression

def resolveSelf(IR):
    '''
    This plugin replaces self by the respective entity's name
    '''
    for name, model in IR["models"].items():
        for entity_type, entities in model["entities"].items():
            for entity in entities:
                entity["equation_parsed"] = resolve(entity["equation_parsed"], entity)

    return IR
