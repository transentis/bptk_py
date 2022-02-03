#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2019 transentis labs GmbH
import logging
import xmltodict
from collections import OrderedDict
from copy import deepcopy

try: # Relative imports in case you are using me inside BPTK or any other library
    from ...parsers.smile.grammar import SMILEVisitor, grammar
    from ...plugins import sanitizeName
    from ...plugins import makeExpressionAbsolute
except: # Absolute imports, in case you are using me standalone
    from parsers.smile.grammar import SMILEVisitor, grammar
    from plugins import sanitizeName, makeExpressionAbsolute


def extract_connects(model_name, connects_raw):
    """
    Extract Connects between elements
    :param model_name:
    :param connects_raw:
    :return:
    """
    def handle_connect(connect):
        to_ = make_qualified_name(model_name,connect["@to"])
        from_ = make_qualified_name(model_name, connect["@from"])
        return {sanitizeName(to_.lower()): sanitizeName(from_.lower())}

    def make_qualified_name(model_name,element_name):
        qualified_name = ""
        if "." in element_name or model_name == "":
            qualified_name = element_name if element_name[0]!='.' else element_name[1:]
        else:
            qualified_name = model_name + "." + element_name
        return qualified_name

    connects = {}
    if type(connects_raw) == OrderedDict:
        return handle_connect(connects_raw)

    elif type(connects_raw) == list:
        for connect in connects_raw:
            connects.update(handle_connect(connect))

    return connects


def make_name_absolute(model_name, name):
    """
    Make an element's name absolute to make it unique. Eg "stock1" in model "model" --> "model.stock1"
    :param model_name: Name of model
    :param name: Element name
    :return:
    """
    seperator = "."
    if "." not in name:
        return model_name + seperator + name
    else:
        return name

def parse_entity(entity, model_name):
    """
    Parse one entity
    :param entity: Entity (XML dict)
    :param model_name: Name of model the entity belongs to
    :return:
    """
    gf = []
    event_poster = []

    if "gf" in entity.keys(): # Graphical Function

        gf_ = entity["gf"]
        ypoints = [float(x) for x in gf_["ypts"].split(",")]
        xpoints = []
        if not "xpts" in gf_.keys():

            minX = float(gf_["xscale"]["@min"])
            maxX = float(gf_["xscale"]["@max"])

            for k in range(0, len(ypoints)):
                xpoints += [minX + k * (maxX - minX) / (len(ypoints) - 1)]

        else:
            xpoints = [float(x) for x in gf_["xpts"].split(",")]

        gf = list(zip(xpoints, ypoints))

    non_negative = True if "non_negative" in entity.keys() else False
    inflows = []
    outflows = []
    doc = None if not "doc" in entity.keys() else entity["doc"]

    if "inflow" in entity.keys(): # Inflow of entity
        inflows += [sanitizeName(make_name_absolute(model_name, entity["inflow"]))] if type(
            entity["inflow"]) is str else [sanitizeName(make_name_absolute(model_name, x)) for x in entity["inflow"]]

    if "outflow" in entity.keys(): # Outflow of entity
        outflows += [sanitizeName(make_name_absolute(model_name, entity["outflow"]))] if type(
            entity["outflow"]) is str else [sanitizeName(make_name_absolute(model_name, x)) for x in entity["outflow"]]

    if "@name" in entity.keys(): # Name of entity
        if not "." in entity["@name"]:
            entity["@name"] = model_name + "." + entity["@name"].lower()

    connects = {} if not "connect" in entity.keys() else extract_connects(model_name, entity["connect"])
    name = "" if not "@name" in entity.keys() else sanitizeName(entity["@name"])

    access = "" if not "@access" in entity.keys() else entity["@access"]
    equation = [] if not "eqn" in entity.keys() else entity["eqn"]

    dimensions = []
    labels = []


    if "dimensions" in entity.keys(): # If entity is arrayed

        dims = entity["dimensions"]["dim"] if type(entity["dimensions"]["dim"]) is list else [entity["dimensions"]["dim"]]
        if dims and "element" in entity.keys():

            for elem in entity["element"]:
                label = tuple([sanitizeName(x) for x in elem["@subscript"].split(",")])
                labels += [label]

        for dim in dims:
            dimensions+= [sanitizeName(dim["@name"])]

    ## Parse Equations again if we find out there are arrayed Equations!
    if len(labels) > 0: # If the entity has dimension labels
        equation = []
        for elem in entity["element"]:
            equation += [elem["eqn"]]

    return {"name": name,
        "access": access,
        "equation": [equation] if type(equation) is str else equation,
        "connects": connects,
        "non_negative": non_negative,
        "inflow": inflows,
        "outflow": outflows,
        "doc": doc,
        "gf": gf,
        "event_poster": event_poster,
        "dimensions": dimensions,
        "labels":labels
            }


def get_entities(entity_type, model):
    """
    Extract entites from XML tree of a Model
    :param entity_type: Type of entity to extract
    :param model: XML Dictionary of the Model
    :return:
    """
    entities = []

    model_name = "" if not "@name" in model.keys() else model["@name"]

    if entity_type in model["variables"].keys():

        if type(model["variables"][entity_type]) == OrderedDict:  # One entity in Model
            entity = model["variables"][entity_type]
            entities += [parse_entity(entity, model_name)]

        elif type(model["variables"][entity_type]) == list: # More than one entity (list of entities)
            for entity in model["variables"][entity_type]:  # For each entity
                entities += [parse_entity(entity, model_name)]

    return entities


def parse_xmile(filename):
    """
    Main method, opens the XMILE file and extracts the model structure
    :param filename: Filename of XMILE file (*.stmx, *.itmx)
    :return: Dictionary containing structure in a Python-processable data structure. Including Abstract Syntax trees for all equations (Excluding extensive pre-processing!)
    """
    with open(filename, "r") as infile:
        xml_string = infile.read()
        document = xmltodict.parse(xml_string)

    ## Main Specs
    specs = document["xmile"]["sim_specs"]
    header = document["xmile"]["header"]

    ## ensure starttime and stoptime are floats

    specs["start"] = specs["start"]+".0" if '.' not in specs["start"] else specs["start"]
    specs["stop"]= specs["stop"]+".0" if '.' not in specs["stop"] else specs["stop"]

    ## Delta T (DT)
    try:
        if "@reciprocal" in specs["dt"].keys() and specs["dt"]["@reciprocal"].lower() == 'true': ## Reciprocal values
            specs["dt"] = 1 / int(specs["dt"]["#text"])
        else: ## Not reciprocal
            specs["dt"] = specs["dt"]["#text"]
    except:
        pass

    specs["method"] = deepcopy(specs["@method"])
    specs["units"] = deepcopy(specs["@time_units"])
    specs.pop("@method")

    try: # Try to extract Array information (dimensions). Empty if this fails
        dimensions = document["xmile"]["dimensions"]
    except:
        dimensions = {}

    IR = { # Empty Intermediate Representation. This is the main representation that we fill up in the further parsing steps
        "dimensions": {},
        "models": {},
        "specs": dict(specs),
        "name": header["name"], "assignments": {}
    }

    ## DIMENSIONS
    if "dim" in dimensions.keys():
        dims = dimensions["dim"] if type(dimensions["dim"]) is list else [dimensions["dim"]]

        for dim in dims:
            size =  None if not "@size" in dim.keys() else int(dim["@size"])
            name = sanitizeName(dim["@name"])
            labels = None

            if not size:
                labels = [sanitizeName(elem["@name"]) for elem in dim["elem"]]
            else:
                labels = [str((i+1)) for i in range(0,size)]

            IR["dimensions"][sanitizeName(dim["@name"])] = {
                "size": size,
                "name": name, "labels": labels, "variables": []}



    ## ENTITIES
    visitor = SMILEVisitor()
    table = []

    models = document["xmile"]["model"] if type(document["xmile"]["model"]) is list else [document["xmile"]["model"]]

    for model in models:
        name = "" if not "@name" in model.keys() else model["@name"]
        variables = {} if not "variables" in model.keys() else model["variables"]
        entities = {}

        for entity_type in variables.keys():
            entities[entity_type] = get_entities(entity_type, model)

            '''
            Parse all arrayed variables
            '''
            if entity_type.lower() in ["stock","aux","array","flow"]:
                for entity in entities[entity_type]:
                    if entity["dimensions"]:
                        variable = entity["name"]
                        dimensions = [entity["dimensions"] ] if not type(entity["dimensions"]) is list else entity["dimensions"]
                        for dim in dimensions:
                            IR["dimensions"][dim]["variables"] += [{"model":name,"name":variable}]


        IR["models"][name] = {"name": name, "entities": entities}

        for key, value in entities.items():
            for elem in value:
                connects = elem["connects"]

                IR["assignments"].update({k:v for k,v in connects.items()})


        table += [[name, 0 if not "stock" in entities.keys() else len(entities["stock"]),
                   0 if not "aux" in entities.keys() else len(entities["aux"]),
                   0 if not "flow" in entities.keys() else len(entities["flow"])]]

    ### PARSE EQUATIONS
    for name, model in IR["models"].items():
        for entity_type, entity in model["entities"].items():
            for elem in entity:
                elem["equation_parsed"] = [makeExpressionAbsolute(name,visitor.visit(grammar.parse(x)),connects=IR["assignments"],entity=entity,dimensions=IR["dimensions"]) for x in elem["equation"]]

                # Handle Non-Negative stocks
                if elem["non_negative"]:
                    if type(elem["equation_parsed"]) is float: # Fixed value, can be stored directly as the actual max of 0 and value
                        elem["equation_parsed"] = max(0, elem["equation_parsed"])
                    else: # Construct Equation: max(0, equation)
                        elem["equation_parsed"] = {"name": 'max', "type": 'call',
                                                   "args": [0, deepcopy(elem["equation_parsed"])]}

    return IR
