#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018 transentis labs GmbH
# MIT License


import importlib

from ipywidgets import VBox
from IPython.display import display

########################
## CLASS WIDGETLOADER ##
########################

class WidgetLoader():
    '''
    WidgetLoader loads a Widget class dynamically using the package path. Class has to be stored in 'BPTK_Py.widgets'
    '''

    def __init__(self):
        """
        initiailize the object variables. Here, only self.widgets as empty list
        """
        self.widgets = []

    def create_widget(self, widget, **kwargs):
        """
        Create a widget using the widget class name.
        :param widget: Widget class name
        :param kwargs: Arbitrary dictionary of key-worded args for the actual Widget object to be loaded
        :return: None
        """
        mod = importlib.import_module("BPTK_Py.widgets")


        self.widgets += [getattr(mod, widget)(**kwargs)]

    def start(self):
        """
        Displays the widget
        :return:  None
        """
        widgets = []
        for widget in self.widgets:
            widgets += [widget.start()]

        display(VBox(widgets))


class Widget():
    """
    Widget mainclass. Has to implement a start function
    """

    def start(self):
        """
        Should return a widget object
        :return:
        """
        print("IMPLEMENT IN SUBCLASS")

        return None