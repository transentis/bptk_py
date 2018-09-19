



import importlib

class WidgetLoader():

    def create_widget(self, widget, **kwargs):
        mod = importlib.import_module("BPTK_Py.widgets")

        self.widget = getattr(mod, widget)(**kwargs)

    def start(self):
        self.widget.start()


class Widget():

    def start(self):
        print("IMPLEMENT IN SUBCLASS")