class Property:

    def __init__(self, name, type, value, properties):
        self._properties = properties
        self._name = name
        self._properties[self._name]={"value": value, "type": type}

    @property
    def value(self):
            """
            return the value of the property
            :return: The property value
            """
            return self._properties[self._name]["value"]

    @value.setter
    def value(self, value):
            """
            Set the value of the property. Currently no type checking is performed.
            :param value: the value
            :return: None
            """
            self._properties[self._name]["value"] = value



