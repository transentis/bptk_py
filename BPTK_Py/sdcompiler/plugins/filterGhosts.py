

def filterGhosts(IR):
    '''
    This plugin fixes empty equations
    '''
    for name, model in IR["models"].items():
        for entity_type, entities in model["entities"].items():
            for entity in entities:
                if  entity["equation_parsed"] == []:
                    entity["equation_parsed"] = ["0"]

    return IR