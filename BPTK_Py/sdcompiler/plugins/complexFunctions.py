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

'''
XMILE allows modelling with pretty complex functions, such as SMOOTH and TREND. We like to avoid complex functions in the resulting model
as the implementation would be very different for each target language. Hence, we build additional stocks that make immediate computations.
The actual equation is then using these stocks for computing the actual function results "by hand".
'''
import itertools
from copy import deepcopy
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
    return arg


def find_function(expression, function_name, context):
    '''
    This function traverses the AST and replaces the function by the correct expression using the function in the context dict
    :param expression: Parsed Equation
    :param function_name: Name of function we search
    :param context: Contains the context (model, entity...) required for the Function that actually creates the required entities
    :return:
    '''

    if type(expression) is str or type(expression) is float:
        return expression

    if type(expression) is list:
        return [find_function(elem, function_name, context) for elem in expression]

    if type(expression) is dict:
        name_ = expression["name"]

        if "args" in expression.keys():
            expression["args"] = find_function(expression["args"], function_name, context)

        if name_.lower() == function_name:
            return context["create_function"](context["model"], context["entity_type"], context["entity"],context["dimensions"], expression)
        return expression

    return expression

def smoothFunction(model, entity_type, entity, dimensions, expression):
    """
    Build new stocks and equations for Smooth function expressions
    :param model:
    :param entity_type:
    :param entity:
    :param expression:
    :return:
    """
    new_entities = []
    input_function = deepcopy(expression["args"][0])
    averaging_time = deepcopy(expression["args"][1])
    initial_value = deepcopy(expression["args"][2])

    try:
        initial_value.remove(", ")
    except:
        pass

    try:
        averaging_time.remove(", ")
    except:
        pass

    try:
        input_function.remove(", ")
    except:
        pass

    try:
        initial_value.remove(",")
    except:
        pass

    try:
        averaging_time.remove(",")
    except:
        pass

    try:
        input_function.remove(",")
    except:
        pass

    if type(input_function) is list: input_function = input_function[0]
    if type(averaging_time) is list: averaging_time = averaging_time[0]


    ### CREATE REQUIRED EXPRESSIONS ###
    change_in_average = [
        {'args': [{'args': [{'args': [input_function,
                                      {'name': deepcopy(entity["name"]),
                                       'type': 'identifier'}],
                             'name': '-',
                             'type': 'operator'}],
                   'name': '()',
                   'type': 'operator'},
                  {'name': averaging_time["name"], 'type': 'identifier'}],
         'name': '/',
         'type': 'operator'}]

    exponential_average = {'args': [{'args': [{'args': [],
                                         'name': 'TIME',
                                         'type': 'call'},
                                        {'args': [],
                                         'name': 'STARTTIME',
                                         'type': 'call'}],
                               'name': '<=',
                               'type': 'operator'},
                              [initial_value],
                              {'args': [{'args': [{'name': entity["name"],
                                                   'type': 'identifier'}],
                                         'name': 'PREVIOUS',
                                         'type': 'call'},
                                        {'args': [{'args': [],
                                                   'name': 'DT',
                                                   'type': 'call'},
                                                  {'args': [{'args': [{'name': deepcopy(entity["name"]) + "_change_in_average",
                                                                       'type': 'identifier'}],
                                                             'name': '()',
                                                             'type': 'operator'}],
                                                   'name': 'PREVIOUS',
                                                   'type': 'call'}],
                                         'name': '*',
                                         'type': 'operator'}],
                               'name': '+',
                               'type': 'operator'}],
                     'name': 'IF',
                     'type': 'call'}

    ### CREATE ADDITIONAL STOCKS ###
    change_in_average_stock = {'name': deepcopy(entity["name"]) + "_change_in_average",
                               'access': '', 'equation': [], 'connects': {},
                               'non_negative': False, 'inflow': [],
                               'outflow': [], 'doc': None,
                               'gf': [], 'event_poster': [], 'dimensions': [], 'labels': [],
                               'equation_parsed': change_in_average}

    ## ADD NEW ENTITIES TO EXISTING MODEL ##
    new_entities += [change_in_average_stock]
    model["entities"][entity_type] += new_entities

    ### RETURN NEW EXPRESSION TO BE ADDED TO ABSTRACT SYNTAX TREE ####
    return  exponential_average



def trendFunction(model, entity_type, entity,dimensions, expression):
    """
    Build the necessary entities and expression for Trend Function
    :param model: Instance of the model, required for adding the new entities
    :param entity_type: Entity type we are currently traversing
    :param entity: Original Entity instance in IR
    :param expression: Parsed Original equation
    :return:
    """
    new_entities = []
    input_function = deepcopy(expression["args"][0])
    averaging_time = deepcopy(expression["args"][1])
    initial_value = deepcopy(expression["args"][2])
    if not type(initial_value) is list:
        initial_value = [initial_value]
    initial_value += [1.0]


    try:
        initial_value.remove(", ")
    except:
        pass

    try:
        averaging_time.remove(",")
    except:
        pass

    try:
        averaging_time.remove(",")
    except:
        pass

    try:
        input_function.remove(", ")
    except:
        pass

    try:
        input_function.remove(",")
    except:
        pass

    if type(input_function) is list: input_function = input_function[0]
    if type(averaging_time) is list: averaging_time = averaging_time[0]

    ### CREATE REQUIRED EXPRESSIONS ###


    change_in_average = [
        {'args': [{'args': [{'args': [input_function,
                                          {'name': deepcopy(entity["name"]) + "_exponential_average",
                                           'type': 'identifier'}],
                                 'name': '-',
                                 'type': 'operator'}],
                       'name': '()',
                       'type': 'operator'},
                      {'name': averaging_time["name"], 'type': 'identifier'}],
            'name': '/',
            'type': 'operator'}]


    exponential_average = {'args': [{'args': [{'args': [], 'name': 'TIME', 'type': 'call'},
                                              {'args': [], 'name': 'STARTTIME', 'type': 'call'}],
                                     'name': '<=',
                                     'type': 'operator'},
                                    [{'args': [2.0,
                                               {'args': [{'args': initial_value,
                                                          'name': '+',
                                                          'type': 'operator'}],
                                                'name': '()',
                                                'type': 'operator'}],
                                      'name': '/',
                                      'type': 'operator'}],
                                    {'args': [{'args': [
                                        {'name': deepcopy(entity["name"]) + "_exponential_average",
                                         'type': 'identifier'}],
                                        'name': 'PREVIOUS',
                                        'type': 'call'},
                                        {'args': [{'args': [], 'name': 'DT', 'type': 'call'},
                                                  {'args': [
                                                      {'args': [{'name': deepcopy(
                                                          entity["name"]) + "_change_in_average",
                                                                 'type': 'identifier'}],
                                                       'name': '()',
                                                       'type': 'operator'}],
                                                      'name': 'PREVIOUS',
                                                      'type': 'call'}],
                                         'name': '*',
                                         'type': 'operator'}],
                                        'name': '+',
                                        'type': 'operator'}],
                           'name': 'IF',
                           'type': 'call'}

    trend_function = [{'args': [{'args': [{'args': [input_function,
                                                    {'name': deepcopy(entity["name"]) + "_exponential_average",
                                                     'type': 'identifier'}],
                                           'name': '-',
                                           'type': 'operator'}],
                                 'name': '()',
                                 'type': 'operator'},
                                {'args': [{'args': [{'name': deepcopy(entity["name"]) + "_exponential_average",
                                                     'type': 'identifier'},
                                                    averaging_time],
                                           'name': '*',
                                           'type': 'operator'}],
                                 'name': '()',
                                 'type': 'operator'}],
                       'name': '/',
                       'type': 'operator'}]


    ### CREATE ADDITIONAL STOCKS ###
    exponential_average_stock = {'name': deepcopy(entity["name"]) + "_exponential_average",
                                 'access': '', 'equation': [], 'connects': {},
                                 'non_negative': False, 'inflow': ['changeInAverage'],
                                 'outflow': [], 'doc': None,
                                 'gf': [], 'event_poster': [], 'dimensions': [], 'labels': [],
                                 'equation_parsed': exponential_average}

    change_in_average_stock = {'name': deepcopy(entity["name"]) + "_change_in_average",
                         'access': '', 'equation': [], 'connects': {},
                         'non_negative': False, 'inflow': [],
                         'outflow': [], 'doc': None,
                         'gf': [], 'event_poster': [], 'dimensions': [], 'labels': [],
                         'equation_parsed': change_in_average}

    ## ADD NEW ENTITIES TO EXISTING MODEL ##
    new_entities += [exponential_average_stock]
    new_entities += [change_in_average_stock]

    model["entities"][entity_type] += new_entities

    ### RETURN NEW EXPRESSION TO BE ADDED TO ABSTRACT SYNTAX TREE ####
    return trend_function

def findLabels(dimensions, stockname):
    labels= []
    for name, dim in dimensions.items():
        if name == "order":
            continue
        for variable in dim["variables"]:
            if variable["name"] == stockname:
                labels += [dim["labels"]]

    return labels

def size(model, entity_type, entity, dimensions, expression):

    return expression

def cartesian_product(listoflists):
    """
    Helper for Cartesian product
    :param listoflists:
    :return:
    """
    if len(listoflists) == 1:
        return listoflists[0]
    res = list(itertools.product(*listoflists))

    if len(res) == 1:
        return res[0]

    return res
def arrayFunction(model, entity_type, entity, dimensions, expression):
    """
    This plugin fixes arguments of array functions. E.g. if the argument is a multidimensional stock
    """
    if type(expression["args"] == dict):
        expression["args"] = [deepcopy(expression["args"])]

    expression["args"] = remove_nesting(expression["args"])
    for elem in expression["args"]:
        try:
            elem.remove(", ")
        except:
            pass
    for elem in deepcopy(expression["args"]):

        if (type(elem)) is list:
            try:
                elem.remove(", ")
            except:
                pass
            elem = elem[0]

        if type(elem) is float or type(elem) is str:
            continue

        type_ = elem["type"]
        name_ = elem["name"]

        '''
        Replace identifiers by stock labels if no labels are given. This is required for calls such as SUM(Stock). Converts to SUM(Stock[1], Stock[2] ... )
        '''


        if type_ == "identifier":

            # Find the labels for the stock
            labels = findLabels(dimensions,name_)

            if (expression["name"] == "size") and labels:
                expression["args"].remove(elem)
                expression["args"] += [len(cartesian_product(labels))]
                entity["dimensions"] = []

            elif labels:

                number_dimensions = len(labels)
                new_args = ["*" for i in range(0,number_dimensions)]
                expression["args"].remove(elem)
                expression["args"] += [{"name": name_, "type": "array", "args": new_args}]


        '''
        Handle the asterisk operator: SUM(Stock[*]) becomes SUM(Stock[1], Stock[2] ... )
        '''

    return expression

def irr(model, entity_type, entity, dimensions, expression):
    """
    For internal rate of return (IRR) function, we add the entity name as an argument
    This allows us to use IRR(t-1) as initial interest rate for IRR(t)
    :param model:
    :param entity_type:
    :param entity:
    :param dimensions:
    :param expression:
    :return:
    """
    if len(expression["args"]) == 1:
        expression["args"] += ["None"]
    expression["args"] += [entity["name"]]
    return expression


def FindComplexFunctions(IR):
    """
    Actual plugin. Add links to the creation functions for additional complex functions
    :param IR:
    :return:
    """

    complex_functions = {"trend": trendFunction,"irr" : irr, "smth1": smoothFunction, "size":arrayFunction, "mean": arrayFunction, "max": arrayFunction, "min": arrayFunction, "sum":arrayFunction, "prod":arrayFunction, "stddev":arrayFunction} # This Dict links to the functions required for building new stocks

    for function_name, func_obj in complex_functions.items():
        for name, model in IR["models"].items():

            for entity_type, entities in model["entities"].items():
                for entity in entities:
                    '''
                    The context contains the create function and the model context to manipulate
                    '''

                    context = { "model" : model, "entity_type": entity_type, "entity": entity, "dimensions": IR["dimensions"],"create_function" : complex_functions[function_name]}

                    if type(entity["equation_parsed"]) is float:
                        entity["equation_parsed"] = [entity["equation_parsed"]]

                    if type(entity["equation_parsed"]) is str:
                        entity["equation_parsed"] = [entity["equation_parsed"]]


                    for index, elem in deepcopy(enumerate(entity["equation_parsed"])):

                        entity["equation_parsed"][index] = find_function(expression=elem, function_name=function_name,
                                                                             context=context)


    return IR
