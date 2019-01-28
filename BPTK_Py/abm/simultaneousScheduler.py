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


#################################
## SIMULTANEOUSSCHEDULER CLASS ##
#################################

class SimultaneousScheduler(Scheduler):
    """
    Implementation of a scheduler. Runs steps synchronously
    """

    def run(self, model, progress_widget=None):
        """
        Run method
            :param model: ABMOdel instance
            :param progress_widget: FloatBarProgress instance
            :return:  None
        """

        self.progress = 0

        if progress_widget:
            progress_widget.value = self.progress

        for sim_round in range(model.starttime, model.stoptime + 1):

            for step in range(round(1 / model.dt)):
                self.run_step(model, sim_round, step, progress_widget)

    def run_step(self, model, sim_round, dt, progress_widget=None):
        """
        Run one step
            :param sim_round: simulator round
            :param dt: step of round
            :param model: ABM Model instance
            :param progress_widget: FloatBarProgress instance (ipywidgets)
            :return:  None
        """

        self.current_round = sim_round

        self.current_step = dt

        time = sim_round + dt * model.dt

        self.current_time = time

        self.progress = self.current_time / model.stoptime

        if progress_widget:
            progress_widget.value = self.progress

        log("[INFO] Round #{} Step #{}".format(sim_round, dt))

        # the simultaneous scheduler first distributes all events to all agents ...

        while len(model.events) > 0:
            event = model.events.pop()

            model.agents[event.receiver_id].receive_event(event)

            if model.data_collector:
                model.data_collector.record_event(time, event)

        # give the model a chance to act and update dynamic properties etc.

        model.act(time, sim_round, dt)

        # ... then it let's the agents act on the events
        # The agents are called in the order they were created in

        for agent in model.agents:
            agent.handle_events(time, sim_round, dt)
            agent.act(time, sim_round, dt)

        if model.data_collector:
            model.data_collector.collect_agent_statistics(time, model.agents)
