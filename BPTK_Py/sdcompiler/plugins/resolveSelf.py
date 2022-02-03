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

        if name_ == "self" and type_ =="identifier":
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