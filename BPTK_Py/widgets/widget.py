



import importlib

class WidgetLoader():

    def __init__(self):
        self.widgets = []

    def create_widget(self, widget, **kwargs):
        mod = importlib.import_module("BPTK_Py.widgets")


        self.widgets += [getattr(mod, widget)(**kwargs)]

    def start(self):
        for widget in self.widgets:
            widget.start()


class Widget():

    def start(self):
        print("IMPLEMENT IN SUBCLASS")