



import importlib

from ipywidgets import VBox
from IPython.display import display

class WidgetLoader():

    def __init__(self):
        self.widgets = []

    def create_widget(self, widget, **kwargs):
        mod = importlib.import_module("BPTK_Py.widgets")


        self.widgets += [getattr(mod, widget)(**kwargs)]

    def start(self):
        widgets = []
        for widget in self.widgets:
            widgets += [widget.start()]

        display(VBox(widgets))


class Widget():

    def start(self):
        """
        Should return a widget object
        :return:
        """
        print("IMPLEMENT IN SUBCLASS")

        return None