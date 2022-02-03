from copy import deepcopy


def resolve(expression, entity):
    '''
    This function traverses the AST and replaces the dimensions by the label by the entity's name
    '''


    if type(expression) is str or type(expression) is float:
        return expression

    if type(expression) is list:
        return [resolve(elem, entity) for elem in expression]


    if type(expression) is dict:
        name_ = expression["name"]
        type_ = expression["type"]
        label_ = deepcopy(entity["labels"])
        dimensions_ =deepcopy(entity["dimensions"])

        if len(dimensions_)  > 0:
            if type_ == "label":
                if name_ in dimensions_:
                    if type(label_) is str:
                        label_=[label_]
                    expression["name"] = deepcopy(label_[dimensions_.index(name_)])

        if "args" in expression.keys():

            try:
                args = deepcopy(expression["args"])
                expression["args"] = resolve(args, entity)
            except RecursionError as e:
                print("Recursion error for entity '{}'".format(entity["name"]))

                #raise e


        return expression
    return expression

def fixLabels(IR):
    '''
    This plugin fixes labels by replacing dimension names by the respective labels for the given dimension
    '''
    for name, model in IR["models"].items():
        for entity_type, entities in model["entities"].items():
            for entity in entities:
                entity["equation_parsed"] = resolve(entity["equation_parsed"], entity)
    return IR