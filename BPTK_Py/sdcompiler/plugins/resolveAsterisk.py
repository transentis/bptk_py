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


def resolve(expression, entity,IR):
    '''
    This function traverses the AST and replaces the SELF identifier by the entity's name
    '''

    if type(expression) is str or type(expression) is float:
        return expression

    if type(expression) is list:
        return [resolve(elem, entity,IR) for elem in expression]


    if type(expression) is dict:
        name_ = expression["name"]
        type_ = expression["type"]

        import itertools
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

        if type_ == "array":

            args = [remove_nesting(arg) for arg in expression["args"]]
            name_ = expression["name"]
            target_entity = {}

            for name, model in IR["models"].items():
                for entity_type, entities in model["entities"].items():
                    for ent in entities:
                        if ent["name"] == name_:
                            target_entity = ent
                            break

            if len(args) == 2:

                dimensions = target_entity["dimensions"]

                left, right = args
                found_asterisk = False

                if left == "*":
                    left_labels = IR["dimensions"][dimensions[0]]["labels"]
                    found_asterisk = True
                else:
                    left_labels = [left[0]["name"]]

                if right == "*":
                    right_labels = IR["dimensions"][dimensions[1]]["labels"]
                    found_asterisk = True
                else:
                    right_labels = [right[0]["name"]]


                # Baue kartesisches Produkt
                if found_asterisk:
                    from  .expandArrays import toLabelObjects
                    products = cartesian_product([left_labels,right_labels])

                    args = [{"name": name_, "type": "array", "args": toLabelObjects(product)} for product in
                             products]

                    return args
            expression["args"] = resolve(args,entity,IR)


        elif "args" in expression.keys():
            expression["args"] = resolve(expression["args"], entity,IR)

        return expression

    return expression


def resolveAsterisk(IR):
    '''
    This plugin replaces self by the respective entity's name
    '''
    #return IR
    IR["dimensions"]["order"] = {}

    for name, model in IR["models"].items():
        for entity_type, entities in model["entities"].items():
            for entity in entities:

                if len(entity["dimensions"]) > 0:
                    IR["dimensions"]["order"][entity["name"]] = entity["dimensions"]

    return IR