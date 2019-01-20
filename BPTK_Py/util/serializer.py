#                                                       /`-
# _                                  _   _             /####`-
#| |                                | | (_)           /########`-
#| |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
#| __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
#| |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018 transentis labs GmbH
# MIT License

import json

class serializer():
    """
    Simple Serializer class
    """

    def __init__(self):
        """
        Initialize addresses
        """
        self.addresses = []

    def serialize_to_json(self, obj, filename):
        self.addresses = []
        res = self.serialize(obj)

        with open(filename, "w") as output_file:
            output_file.write(json.dumps(res, indent=4))

    def serialize(self, obj):
        return_value = {}

        if type(obj) is dict:
            # Handle dict
            for key, value in obj.items():
                return_value[key] = self.serialize(value)
        elif type(obj) is list:
            # Handle list
            return self.serialize_list(obj)
        # Handle primitive types
        elif type(obj) in (int, float, str, bool):
            return str(obj)

        elif obj is None:
            # Handle the None-Object
            return "None"
        else:
            # Handle ordinary objects that we can iterate using "vars"
            return_value["__address__"] = hex(id(obj))
            return_value["__type__"] = str(type(obj)).replace("<class", "").replace("\'", "").replace(">", "").replace(
                " ", "")

            if return_value["__address__"] not in self.addresses:
                # To avoid endless recursion (may occur frequently), I only serialize objects I have not serialized before
                # Otherwise, just add address so I can rebuild later
                self.addresses += [return_value["__address__"]]

                for key, value in vars(obj).items():
                    return_value[key] = self.serialize(value)

        return return_value

    def serialize_list(self, lis):
        return_value = []
        for value in lis:
            if type(value) in (int, float, str, bool):
                return_value += [value]
            elif type(value) is dict:
                return_value += [self.serialize(value)]
            elif type(value) is list:
                return_value += [self.serialize_list(value)]
            else:
                return_value += [self.serialize(value)]
        return return_value


    def deserialize(self,dictionary):
        obj = None

        ## First trials deserialize

        # Beim deserialisieren müsste ich also immer auf nen Key "__address__" checken
        # und daraufhin entweder das Objekt dranhängen, das ich schon kenne, oder es suchen und dann weiter machen


        # Oder zwei Schritte: erst alle Objekte bauen
        # Dann links fixen, wenn fehlende gefunden


        # Lambda funktionen sind komplizierter
