from copy import deepcopy
import re

def resolve(expression, entity, dimensions):
    '''
    This function traverses the AST and replaces the dimensions by the label by the entity's name
    '''

    if type(expression) is str or type(expression) is float:
        return expression

    if type(expression) is list:
        return [resolve(elem, entity, dimensions) for elem in expression]


    if type(expression) is dict:
        name_ = expression["name"]
        type_ = expression["type"]

        # Fix name usage such as countries.germany (<dimension>.<label>)
        # Identify whether this looks like a <dimension>.<label> and make it a label
        pattern = r"[a-zA-Z_]*\.[a-zA-Z_]*"

        clean = re.compile(pattern)
        match = clean.match(expression["name"])

        if match and match.group(0) == expression["name"] and expression["name"].split(".")[0] in dimensions.keys():
            # Now remove leading dimension
            expression["name"] = expression["name"].split(".")[1]
            expression["type"] = "label"

        if type_ == "call" and name_ == "size": # Size function
                args_ = expression["args"]

                if args_[0]["type"] == "identifier" and args_[0]["name"] in dimensions:
                    expression = len(dimensions[args_[0]["name"]]["labels"])

                else: # If no dimension hit was made, simply keep on traversing
                    expression["args"] = resolve(expression["args"], entity, dimensions)

        elif "args" in expression.keys():
            expression["args"] = resolve(expression["args"], dimensions=dimensions, entity=entity)

        return expression
    return expression

def replaceDimensionNames(IR):
    '''
    This plugin replaces dimension names by the correct values, e.g. SIZE(<dimension>) will be resolved to the actual size of the dimension
    '''

    for name, model in IR["models"].items():
        for entity_type, entities in model["entities"].items():
            for entity in entities:
                entity["equation_parsed"] = resolve(entity["equation_parsed"], entity=entity, dimensions=IR["dimensions"])

    return IR