from copy import deepcopy
try:
    from .sanitizeNames import sanitizeName
except:
    from plugins.sanitizeNames import sanitizeName

def makeExpressionAbsolute(model_name, expression,connects,entity,dimensions):

    seperator = '.'

    if type(expression) is str or type(expression) is float:
        return expression

    if type(expression) is list:
        for elem in expression:
            makeExpressionAbsolute(model_name, elem,connects,entity,dimensions)

    if type(expression) is dict:
        name = expression["name"]
        type_ = expression["type"]

        if "args" in expression.keys():
            makeExpressionAbsolute(model_name, expression["args"],connects,entity, dimensions)

        if type_ == "identifier" or type_ == "array":

            if name in dimensions.keys(): # ignore dimension names
                pass

            elif not seperator in name:
                expression["name"] = sanitizeName(model_name) + seperator + expression["name"] if len(model_name) > 0 else expression["name"]

            '''
            Check for a Connect to another model
            '''
            if expression["name"] in connects.keys():
                expression["name"] = connects[expression["name"]]

    return expression