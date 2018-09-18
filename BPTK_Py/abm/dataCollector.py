

class DataCollector:

    def __init__(self):
        self.agent_statistics = {}
        self.event_statistics = {}

    def record_event(self, time, event):
        if time not in self.event_statistics:
            self.event_statistics[time] = {}

        if event.name not in self.event_statistics[time]:
            self.event_statistics[time][event.name] = 0

        self.event_statistics[time][event.name] += 1

    def collect_agent_statistics(self, time, agents):

        self.agent_statistics[time] = {}

        for agent in agents:

            if agent.agent_type not in self.agent_statistics[time]:
                self.agent_statistics[time][agent.agent_type] = {}

            if agent.state not in self.agent_statistics[time][agent.agent_type]:
                self.agent_statistics[time][agent.agent_type][agent.state] = 0

            self.agent_statistics[time][agent.agent_type][agent.state] += 1

    def statistics(self):

        return self.agent_statistics

    def step_statistics(self, time):

        # begin time step

        statistics = "\"" + str(time) + "\":{"

        # begin agents section

        statistics = statistics + "\"agents\":{"

        first_agent = True

        agent_statistics = self.agent_statistics[time]

        for agent in agent_statistics:

            if not first_agent:
                statistics += ","

            # begin agent

            statistics += "\"" + agent + "\":{"

            first_state = True

            for state in agent_statistics[agent]:

                if not first_state:
                    statistics += statistics + ","

                statistics += "\"" + state + "\":" + str(agent_statistics[agent][state])

                first_state = False

            # end agent

            statistics += "}"

            first_agent = False

        # end agents

        statistics += "},"

        # begin events

        statistics += "\"events\":{"

        first_event = True

        if time in self.event_statistics:

            for event in self.event_statistics[time]:

                if not first_event:
                    statistics += ","

                statistics += "\"" + event + "\":" + str(self.event_statistics[time][event])

                first_event = False

        # end events

        statistics += "}"

        # end time step

        statistics += "}"

        return "{"+statistics+"}"
