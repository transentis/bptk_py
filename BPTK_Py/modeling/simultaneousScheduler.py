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


from .scheduler import Scheduler
from ..logger import log
from .event import DelayedEvent

#################################
## SIMULTANEOUSSCHEDULER CLASS ##
#################################

class SimultaneousScheduler(Scheduler):
    """
    Implementation of a scheduler. Runs steps synchronously
    """

    def run(self, model, progress_widget=None, collect_data=True):
        """
        Run method
            :param model: ABMOdel instance
            :param progress_widget: FloatBarProgress instance
            :return:  None
        """

        self.progress = 0

        if model.data_collector:
            model.data_collector.reset()

        if progress_widget:
            progress_widget.value = self.progress

        for sim_round in range(model.starttime, model.stoptime + 1):

            if self.running:
                for step in range(round(1 / model.dt)):
                    if self.running:
                        self.run_step(model, sim_round, step, progress_widget, collect_data)
                    else:
                        break
            else:
                break

    def run_step(self, model, sim_round, step, progress_widget=None, collect_data=True):
        """
        Run one step
            :param sim_round: simulator round
            :param dt: step of round
            :param model: ABM Model instance
            :param progress_widget: FloatBarProgress instance (ipywidgets)
            :return:  None
        """

        self.current_round = sim_round

        self.current_step = step

        time = sim_round + step * model.dt

        self.current_time = time

        self.progress = self.current_time / model.stoptime

        if progress_widget:
            progress_widget.value = self.progress

        log("[INFO] Round #{} Step #{}, collect_data={}".format(sim_round, step, collect_data))

        # the simultaneous scheduler first distributes all events to all agents ...

        while len(model.events) > 0:

            # Check if the event is of type DelayedEvent. If yes, we do not get a reply here and the event will be stored in self.delayed_events

            event = self.handle_delayed_event(model.events.pop(), dt=model.dt)

            if event:
                model.agents[event.receiver_id].receive_event(event)

                if model.data_collector:
                    model.data_collector.record_event(time, event)

        # give the model a chance to update dynamic properties etc.

        model.begin_round(time, sim_round, step)

        # ... then it let's the agents act on the events
        # The agents are called in the order they were created in

        for agent in model.agents:
            agent.handle_events(time, sim_round, step)
            agent.act(time, sim_round, step)

        model.end_round(time, sim_round, step)



        if model.data_collector:
            if collect_data:
                model.data_collector.collect_agent_statistics(time, model.agents)
            else:
                # only collect data on the last round
                if sim_round == model.stoptime and step == (round(1 / model.dt) - 1):
                    model.data_collector.collect_agent_statistics(time, model.agents)


        # If any delayed events observed, store them in the model's events list for later use
        model.events += self.delayed_events

        self.delayed_events = []

