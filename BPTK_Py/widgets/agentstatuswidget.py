import time
import ipywidgets as widgets
from IPython.display import display
import threading

from ..logger import log
from .widget import Widget


class AgentStatusWidget(Widget):
    """
    This widget reacts to the state of certain agent and changes the color of buttons (one button per agent, no effect on click).
    We use it as an example for the widget functionality in our example notebook (The interactive tutorial).
    In the example we monitor the states "INPROGRESS" and "DONE" of the given agents and change the color of the buttons
    """
    def __init__(self, **kwargs):
        """

        :param kwargs: Has to contain the key "agents", a list of Agent objects. Has to contain the states to map to. A list, element 0: "GREEN STATE" (for now, not used, but specify None), element 1: "YELLOW STATE", element 2: "RED STATE"
        """
        try:
            self.agents = kwargs["agents"]
        except KeyError as e:
            log("[ERROR] AgentStatusWidget did not receive argument 'agents'")
            raise e

        try:
            self.states = kwargs["states"]
        except KeyError as e:
            log("[ERROR] AgentStatusWidget did not receive argument 'states'")
            raise e

        self.thread = threading.Thread(target=self.monitor_agents)
        self.running = False


        button_layout = widgets.Layout(width="10%")

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
        """
        This methods starts the widget's thread for monitoring the agent states. Has to be called from outside.
        :return The actual widget object to show on the output (e.g. Jupyter Notebook). Here a VBox with all the buttons
        """
        self.running = True
        self.thread.start()
        return self.main_Vbox

    def stop(self):
        """
        Call from outside when simulation finished. Will kill the running thread
        :return: None
        """
        self.running = False

    def monitor_agents(self):
        """
        Threaded method. Will monitor the agents' states and change the color of the buttons
        :return: None
        """
        while self.running:

            for i in range(0, len(self.agents)):
                if self.agents[i].state == self.states[1]:
                    self.buttons[i].button_style = 'warning'
                if self.agents[i].state == self.states[2]:
                    self.buttons[i].button_style = 'danger'

            time.sleep(1)

        return None


