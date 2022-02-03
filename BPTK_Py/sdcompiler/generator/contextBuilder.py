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

def generate(IR, template, parseExpression):
    """
    The generator for python.

    a) Build the Export Context
    b) Render the template using the export Context and JINJA
    :param IR:
    :param template: Jinja template as str
    :param parseExpression: Function that parses the IR expressions to the specific target language
    :return:
    """
    from jinja2 import Template
    template = Template(template)

    ## generate context from IR
    context = build_context(IR, parseExpression)

    ## Fill template
    output = template.render(stocks=context["stocks"],
                             specs=IR["specs"],
                             flows=context["flows"],
                             converters=context["converters"],
                             gfs=context["gfs"],
                             constants=context["constants"],
                             dimensions=context["dimensions"],
                             notmemoized=context["notmemoized"])

    return output

def remove_nesting(arg):
    '''
    Simply removes nesting level of list of lists. This can be required for args (handed over to functions multiple times and hence deeply-nested)
    [[a,b ]] --> [a,b]
    :param arg:
    :return:
    '''
    if type(arg) is list and len(arg) == 1:
        return remove_nesting(arg[0])
    if type(arg) is tuple and len(arg) == 1:
        return remove_nesting(arg[0])
    if type(arg) is dict:
        return [arg]

    if type(arg) is float or type(arg) is str or type(arg) is int:
        return [arg]
    return arg

def build_context(IR, parseExpression):
    '''
    This method builds the export context for the Jinja template. Requires a parser function for the IR
    :param IR: Intermediate Representation of the Model(s)
    :param parseExpression: Parser function
    :return: Context (dict)
    '''
    context =  {
            "stocks": [],
            "flows": [],
            "converters": [],
            "constants": [],
            "gfs": [],
            "events": [],
            "specs": IR["specs"],
            "dimensions": IR["dimensions"],
            "header": '',
            "notmemoized": []
        }

    for name, model in IR["models"].items():
        for entity_type, entities in model["entities"].items():

            for entity in entities:
                name = entity["name"]

                if "notmemoized" in entity.keys() and entity["notmemoized"]:
                    context["notmemoized"] += [name]

                if type(entity["equation_parsed"]) is list and len(entity["equation_parsed"]) == 1 and type(entity["equation_parsed"][0]) is str:
                    expr = 0.0 # Comments
                else:
                    expr = "0" if parseExpression(entity["equation_parsed"]) == '' else parseExpression(entity["equation_parsed"])

                # Main Entity representation for the context

                ent = {"name": name,
                         "expression": expr,
                         }

                # Labels
                if len(entity["labels"]) > 0:
                    if type(entity["labels"]) is str or type(entity["labels"]) is float or type(entity["labels"]) is int:
                        entity["labels"] = [entity["labels"]]
                    try:
                        labels = ",".join(entity["labels"])
                        ent["labels"] = labels
                    except:
                        pass


                # Stocks and Flows
                if entity_type == "stock" or entity_type =="flow":

                    context[entity_type + "s"] += [ent]

                # Aux
                elif entity_type == "aux":

                    if type(expr) is float or type(expr) is int:
                        context["constants"] += [ent]

                    if len(entity["gf"]) > 0:
                        ent["points"] = entity["gf"]
                        context["gfs"] += [ent]

                    else:
                        context["converters"] += [ ent ]

    return context