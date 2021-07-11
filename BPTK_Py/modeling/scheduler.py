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
        self.current_time = 0
        self.current_round = 0
        self.current_step = 0
        self.progress = 0
        self.delayed_events = []
        self.running = True

    def run(self, model, progress_widget=None, collect_data=True):
        """Run the simulation.
        Override this in a subclass.

        Parameters:
            model: Model instance.
            progress_widget: Widget (Default=None).
                If set, the widget is used to show progress during execution
        """
        log("[ERROR] Scheduler.run should be overriden in a subclass")

    def run_step(self, model, sim_round, dt, progress_widget=None, collect_data=True):
        """Run a simulation step.

        Override this in a subclass.
        
        Parameters:
            model: Model
                Model instance
            sim_round: Integer
                round of simulator
            dt: Integer.
                Current step of round
            progress_widget: Widget (default=None)
                Live instance of FloatProgressBar
            collect_data: Boolean.
                Flag that indicates whether to collect data.
        """
        log("[ERROR] Scheduler.run_step should be overriden in a subclass")

    def handle_delayed_event(self, event, dt):
        """
        This method checks to see whether the event is a DelayedEvent.
        
        If not, it simply returns the event.
        
        If yes, it counts down the delay by one timestep (dt), caches the event in delayed_events and returns None.

        Parameters:
            event: Event.
                The event to check
            dt: Integer 
                the timestep to count down.

        Returns
            The event if this is not a DelayedEvent or the delay<=0 , otherwise None
        """
        if isinstance(event, DelayedEvent):
            if event.delay > 0:
                event.delay -= dt
                self.delayed_events += [event]
                return None
        return event

