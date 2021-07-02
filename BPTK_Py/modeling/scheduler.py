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


from ..logger import log
from .event import DelayedEvent


#####################
## SCHEDULER CLASS ##
#####################


class Scheduler:
    """
    Scheduler for agent based modelling
    """

    def __init__(self):
        """
        Init method, no params
        """
        self.current_time = 0
        self.current_round = 0
        self.current_step = 0
        self.progress = 0
        self.delayed_events = []
        self.running = True

    def run(self, model, progress_widget=None, collect_data=True):
        """
        Override this in a subclass
            :param model: Model instance
            :param progress_widget: If true, show a progress widget during execution
            :return:
        """
        log("[ERROR] Scheduler.run should be overriden in a subclass")

    def run_step(self, model, sim_round, dt, progress_widget=None, collect_data=True):
        """
        Override this in a subclass
            :param model: Model instance
            :param sim_round: round of simulator
            :param dt: Current step of round
            :param progress_widget: Live instance of FloatProgressBar
        """
        log("[ERROR] Scheduler.run_step should be overriden in a subclass")

    def handle_delayed_event(self, event, dt):
        """
        This method checks to see whether the event is a DelayedEvent. If not, it simply returns the event. If yes, it counts down the delay by one timestep (dt), caches the event in delayed_events and returns None.
            :param event: the event to check
            :param dt: the timestep to count down.
            :return: the event if this is not a DelayedEvent or the delay<=0 , otherwise None
        """
        if isinstance(event, DelayedEvent):
            if event.delay > 0:
                event.delay -= dt
                self.delayed_events += [event]
                return None
        return event

