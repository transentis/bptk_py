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

from copy import deepcopy


def DimJoinedExpression(names, operator,dim):
    dims = str(deepcopy(dim)).replace("(", "").replace(")", "").replace("[", "").replace("]", "")

    if not type(operator) is str:
        raise TypeError("Operator not provided")

    if not type(names) is list:
        return {"name": '', "type": 'nothing'}
    if len(names) == 0:
        return {"name": '', "type": 'nothing'}

    if len(names) == 1:
        return {"name": names[0]+"[{}]".format(dims), "type": 'identifier'}

    elif len(names) == 2:

        return {
            "name": operator,
            "type": 'operator',
            "args": [
                {"name": names[0]+"[{}]".format(dims), "type": 'identifier'},
                {"name": names[1]+"[{}]".format(dims), "type": 'identifier'}
            ]
        }


    elif len(names) > 2:
        tail = names[-2:]
        rest = names[:-2]

        already_reduced = initial = {
            "name": operator,
            "type": 'operator',
            "args": [
                {"name": tail[0]+"[{}]".format(dims), "type": 'identifier'},
                {"name": tail[1]+"[{}]".format(dims), "type": 'identifier'}
            ]
        }

        def reduce(already_reduced, name):
            return {
                "name": operator,
                "type": 'operator',
                "args": [{"name": name+"[{}]".format(dims), "type": 'identifier'}, already_reduced]
            }

        for index, elem in enumerate(reversed(rest)):
            already_reduced = reduce(already_reduced, elem)

        return already_reduced

def JoinedExpression(names, operator):
    if not type(operator) is str:
        raise TypeError("Operator not provided")

    if not type(names) is list:
        return {"name": '', "type": 'nothing'}
    if len(names) == 0:
        return {"name": '', "type": 'nothing'}

    if len(names) == 1:
        return {"name": names[0], "type": 'identifier'}

    elif len(names) == 2:
        return {
            "name": operator,
            "type": 'operator',
            "args": [
                {"name": names[0], "type": 'identifier'},
                {"name": names[1], "type": 'identifier'}
            ]
        }

    elif len(names) > 2:
        tail = names[-2:]
        rest = names[:-2]

        already_reduced = initial = {
			"name": operator,
			"type": 'operator',
			"args": [
				{ "name": tail[0], "type": 'identifier' },
				{ "name": tail[1], "type": 'identifier' }
			]
		}

        def reduce(already_reduced, name):
            return {
                "name": operator,
                "type": 'operator',
                "args": [{"name": name, "type": 'identifier'}, already_reduced]
            }

        for index, elem in enumerate(reversed(rest)):
            already_reduced = reduce(already_reduced,elem)

        return already_reduced



def StockExpressions(IR):
    """
    The actual plugin. This plugin creates the expressions for inflows and outflows ( expression - outflows + inflows)
    :param IR:
    :return:
    """
    for name, model in IR["models"].items():

        for entity_type, entities in model["entities"].items():
            if entity_type != "stock":
                continue
            for entity in entities:

                inflows = JoinedExpression(entity["inflow"], "+")  # WRITE UP JOINED EXPRESSION!
                outflows = JoinedExpression(entity["outflow"], "+")  # WRITE UP JOINED EXPRESSION
                sum = 0

                if (not inflows["type"] == "nothing") and (outflows["type"] == "nothing"):  # Only inflows
                    sum = {"name": "()", "type": 'operator', "args": [inflows]}
                elif (inflows["type"] == "nothing") and (not outflows["type"] == "nothing"): # Only outflows

                    sum = {"name": '()', "type": 'operator', "args": [
                        {"name": '*', "type": 'operator', "args": [
                            -1,
                            {"name": '()', "type": 'operator', "args": [outflows]}
                        ]}
                    ]}
                elif inflows["type"]==outflows["type"] == "nothing":
                    sum = 0
                else:
                    sum = {"name": '()', "type": 'operator', "args": [
                        {"name": '-', "type": 'operator', "args": [
                            inflows,
                            {"name": '()', "type": 'operator', "args": [outflows]}
                        ]}
                    ]}

                # stock(t) = if t < starttime then initial else stock(t-1) + dt * ∑Flows

                expression = {"name": 'IF', "type": 'call', "args": [
                    {"name": '<=', "type": 'operator', "args": [
                        {"name": 'TIME', "type": 'call', "args": []},
                        {"name": 'STARTTIME', "type": 'call', "args": []}
                    ]},
                    deepcopy(entity["equation_parsed"]),  # initial
                    {"name": '+', "type": 'operator', "args": [
                        {"name": 'PREVIOUS', "type": 'call', "args": [
                            {"name": entity["name"], "type": 'identifier'}
                        ]},
                        {"name": '*', "type": 'operator', "args": [
                            {"name": 'DT', "type": 'call', "args": []},
                            {"name": 'PREVIOUS', "type": 'call', "args": [sum]}
                        ]}
                    ]}
                ]}

                entity["equation_parsed"] = expression
    return IR

