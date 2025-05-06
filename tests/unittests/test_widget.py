import unittest
from unittest import mock

from BPTK_Py.widgets.widget import WidgetLoader, Widget

class TestWidgetLoader(unittest.TestCase):
    def setUp(self):
        pass

    def test_init(self):
        widgetLoader = WidgetLoader()
        self.assertEqual(widgetLoader.widgets,[])

    @mock.patch("importlib.import_module")
    def test_widgetloader_create_widget_adds_widget(self, mock_import_module):
        widgetLoader = WidgetLoader()

        # Create a mock widget class with an __init__ that accepts kwargs
        MockWidgetClass = mock.Mock()
        mock_widget_instance = mock.Mock()
        MockWidgetClass.return_value = mock_widget_instance

        # Simulate importlib.import_module returning a module with the mock widget
        mock_module = mock.Mock()
        setattr(mock_module, "MyWidget", MockWidgetClass)
        mock_import_module.return_value = mock_module

        widgetLoader.create_widget("MyWidget", foo="bar")

        assert len(widgetLoader.widgets) == 1
        MockWidgetClass.assert_called_once_with(foo="bar")
        assert widgetLoader.widgets[0] == mock_widget_instance

    @mock.patch("BPTK_Py.widgets.widget.display")
    def test_widgetloader_start_displays_widgets(self, mock_display):
        widgetLoader = WidgetLoader()

        import ipywidgets as widgets
        mock_widget_instance_1 = mock.Mock()
        mock_widget_instance_2 = mock.Mock()
        mock_widget_instance_1.start.return_value = widgets.Label("widget1")
        mock_widget_instance_2.start.return_value = widgets.Label("widget2")
        widgetLoader.widgets = [mock_widget_instance_1, mock_widget_instance_2]

        widgetLoader.start()

        mock_widget_instance_1.start.assert_called_once()
        mock_widget_instance_2.start.assert_called_once()
        called_arg = mock_display.call_args[0][0]
        assert isinstance(called_arg, widgets.VBox)
        assert isinstance(called_arg.children[0], widgets.Widget)
        assert isinstance(called_arg.children[1], widgets.Widget)

class TestWidget(unittest.TestCase):
    def setUp(self):
        pass

    def test_start(self):
        widget = Widget()

        #Redirect the console output
        import sys, io
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout 

        widget.start()

        #Remove the redirection of the console output
        sys.stdout = old_stdout
        output = new_stdout.getvalue()

        self.assertIn("IMPLEMENT IN SUBCLASS", output) 

if __name__ == '__main__':
    unittest.main()
