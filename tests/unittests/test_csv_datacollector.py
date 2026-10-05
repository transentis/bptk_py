import unittest

from BPTK_Py import Event, Model, Agent, SimultaneousScheduler
from BPTK_Py.modeling.datacollectors.csv_datacollector import CSVDataCollector

import os, tempfile


def _read(filename):
    with open(filename, "r", encoding="UTF-8") as file:
        return [line.rstrip("\n") for line in file]


class _Customer(Agent):
    def initialize(self):
        self.agent_type = "customer"
        self.state = "active"
        self.set_property("revenue", {"type": "Double", "value": 0.0})

    def act(self, time, round_no, step_no):
        self.revenue = time * 10.0 * self.id


class TestCSVDataCollector(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.prefix = os.path.join(self._tmp.name, "results")

    def tearDown(self):
        self._tmp.cleanup()

    def _agent(self, agent_id, agent_type="customer", value=0.0):
        return Agent(agent_id=agent_id, model=Model(), agent_type=agent_type,
                     properties={"revenue": {"type": "Double", "value": value}})

    def test_csv_data_collector_init_creates_the_directory(self):
        prefix = os.path.join(self.prefix, "nested", "deeper")

        CSVDataCollector(prefix=prefix)

        self.assertTrue(os.path.isdir(prefix))

    def test_one_file_per_agent_type_and_a_row_per_step(self):
        collector = CSVDataCollector(prefix=self.prefix)
        first, second = self._agent(1), self._agent(2)

        for time in (1, 2, 3):
            first.properties["revenue"]["value"] = time * 10.0
            second.properties["revenue"]["value"] = time * 20.0
            collector.collect_agent_statistics(sim_time=time, agents=[first, second])

        self.assertEqual(os.listdir(self.prefix), ["customer.csv"])
        self.assertEqual(_read(os.path.join(self.prefix, "customer.csv")), [
            "id;time;revenue",
            "1;1;10.0", "2;1;20.0",
            "1;2;20.0", "2;2;40.0",
            "1;3;30.0", "2;3;60.0",
        ])

    def test_agent_types_go_to_separate_files(self):
        collector = CSVDataCollector(prefix=self.prefix)

        collector.collect_agent_statistics(sim_time=1, agents=[self._agent(1, "customer"),
                                                               self._agent(2, "supplier")])

        self.assertEqual(sorted(os.listdir(self.prefix)), ["customer.csv", "supplier.csv"])

    def test_a_property_the_header_lacks_is_left_out(self):
        collector = CSVDataCollector(prefix=self.prefix)
        late = self._agent(2)
        late.properties["extra"] = {"type": "Double", "value": 1.0}

        collector.collect_agent_statistics(sim_time=1, agents=[self._agent(1), late])

        self.assertEqual(_read(os.path.join(self.prefix, "customer.csv")),
                         ["id;time;revenue", "1;1;0.0", "2;1;0.0"])

    def test_record_event(self):
        collector = CSVDataCollector(prefix=self.prefix)

        collector.record_event(time=1, event=Event(name="order", sender_id=1, receiver_id=2))
        collector.record_event(time=2, event=Event(name="payment", sender_id=2, receiver_id=1))

        self.assertEqual(_read(os.path.join(self.prefix, "events.csv")), [
            "time;event;sender_id;receiver_id",
            "1;order;1;2",
            "2;payment;2;1",
        ])

    def test_reset_starts_the_files_afresh(self):
        collector = CSVDataCollector(prefix=self.prefix)
        collector.collect_agent_statistics(sim_time=1, agents=[self._agent(1, value=1.0)])

        collector.reset()
        collector.collect_agent_statistics(sim_time=1, agents=[self._agent(1, value=2.0)])

        self.assertEqual(_read(os.path.join(self.prefix, "customer.csv")),
                         ["id;time;revenue", "1;1;2.0"])

    def test_statistics(self):
        collector = CSVDataCollector(prefix=self.prefix)

        self.assertEqual(collector.statistics(), {})

    def test_in_a_model_run(self):
        model = Model(name="csv", scheduler=SimultaneousScheduler(),
                      data_collector=CSVDataCollector(prefix=self.prefix))
        model.register_agent_factory("customer", lambda agent_id, model, properties:
                                     _Customer(agent_id, model, properties))
        model.configure({"runspecs": {"starttime": 1, "stoptime": 3, "dt": 1.0},
                         "properties": {},
                         "agents": [{"name": "customer", "count": 2}]})
        filename = os.path.join(self.prefix, "customer.csv")

        # A header, then two customers in each of three steps
        model.run()
        lines = _read(filename)
        self.assertEqual(lines[0].split(";")[:2], ["id", "time"])
        self.assertEqual(len(lines), 1 + 2 * 3)

        # A second run replaces the first rather than appending to it: the scheduler
        # resets the collector when a run starts
        model.run()
        self.assertEqual(len(_read(filename)), 1 + 2 * 3)
