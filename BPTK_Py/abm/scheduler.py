from BPTK_Py import log


class Scheduler:
    def __init__(self):
        self.current_time = 0
        self.current_round = 0
        self.current_step = 0
        self.progress = 0

    def run(self, scenario, progress_widget=None):
        log("[ERROR] Scheduler.run should be overriden in a subclass")

    def run_step(self, scenario, sim_round, step, progress_widget=None):
        log("[ERROR] Scheduler.run_step should be overriden in a subclass")
