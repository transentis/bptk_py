from .scheduler import Scheduler
from BPTK_Py import log


class SimultaneousScheduler(Scheduler):

    def run(self, scenario, progress_widget=None):

        self.progress = 0

        if progress_widget:
            progress_widget.value = self.progress

        for sim_round in range(scenario.start_time, scenario.stop_time+1):

            for step in range(round(1/scenario.step)):

                self.run_step(scenario, sim_round, step, progress_widget)

    def run_step(self, scenario, sim_round, step, progress_widget=None):

        self.current_round = sim_round

        self.current_step = step

        time = sim_round + step * scenario.step

        self.current_time = time

        self.progress = self.current_time/scenario.stop_time

        if progress_widget:
            progress_widget.value = self.progress

        log("[INFO] Round #{} Step #{}".format(sim_round, step))

        # the simultaneous scheduler first distributes all events to all agents ...

        while len(scenario.events) > 0:
            event = scenario.events.pop()

            scenario.agents[event.receiver_id].receive_event(event)

            if scenario.data_collector:
                scenario.data_collector.record_event(time, event)

        # ... then it let's the agents act on the events
        # The agents are called in the order they were created in

        for agent in scenario.agents:
            agent.act(time, sim_round, step)

        if scenario.data_collector:
            scenario.data_collector.collect_agent_statistics(time, scenario.agents)
