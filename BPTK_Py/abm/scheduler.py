#                                                       /`-
# _                                  _   _             /####`-
#| |                                | | (_)           /########`-
#| |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
#| __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
#| |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018 transentis labs GmbH
# MIT License




from ..logger import log


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

    def run(self, model, progress_widget=None):
        """
        Override this in a subclass
            :param model: Model instance
            :param progress_widget: If true, show a progress widget during execution
            :return:
        """
        log("[ERROR] Scheduler.run should be overriden in a subclass")

    def run_step(self, model, sim_round, dt, progress_widget=None):
        """
        Override this in a subclass
            :param model: Model instance
            :param sim_round: round of simulator
            :param dt: Current step of round
            :param progress_widget: Live instance of FloatProgressBar
        """
        log("[ERROR] Scheduler.run_step should be overriden in a subclass")
