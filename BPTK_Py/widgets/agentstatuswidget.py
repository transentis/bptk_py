import time
import ipywidgets as widgets
from IPython.display import display
import threading

from .widget import Widget

class AgentStatusWidget(Widget):

    def __init__(self, **kwargs):
        self.agents = kwargs["agents"]

        self.thread = threading.Thread(target=self.monitor_agents)
        self.running = False
        self.states = kwargs["states"]

        button_layout = widgets.Layout(width="10%")

        # main_vbox = widgets.VBox()
        self.buttons = []
        for i in range(0, len(self.agents)):

            self.buttons += [widgets.Button(description=str(i + 1), button_style='info', layout=button_layout)]

        hboxes = []
        for i in range(0, len(self.buttons) + 1, 10):

            buttons_tmp = []
            to = i + 10 if len(self.buttons) - i > 10 else len(self.buttons)

            for j in range(i, to):
                button = self.buttons[j]

                buttons_tmp += [button]

            hboxes += [widgets.HBox(children=buttons_tmp)]


        self.main_Vbox = widgets.VBox(children=hboxes)




    def start(self):
        self.running = True
        self.thread.start()
        return self.main_Vbox

    def stop(self):
        self.running = False

    def monitor_agents(self):
        while self.running:

            for i in range(0, len(self.agents)):
                if self.agents[i].state == self.states[1]:
                    self.buttons[i].button_style = 'warning'
                if self.agents[i].state == self.states[2]:
                    self.buttons[i].button_style = 'danger'

            time.sleep(1)


