import unittest, importlib, datetime, jsonpickle, psycopg
from unittest.mock import MagicMock

from BPTK_Py.util.statecompression import compress_settings, compress_results, decompress_results, decompress_settings
import BPTK_Py.logger.logger as logmod
from BPTK_Py.externalstateadapter.externalStateAdapter import InstanceState
from BPTK_Py.externalstateadapter.postgres_adapter import PostgresAdapter

def _ts(dt: datetime.datetime) -> str:
    # converting timestamps in sql format
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")


def _instance_to_row(inst: InstanceState):
    # converts InstanceState into DB-tuple
    return (
        jsonpickle.dumps(inst.state) if inst.state is not None else None,  # state
        inst.instance_id,                                                  # instance_id
        _ts(inst.time),                                                    # time
        int(inst.timeout.get("weeks", 0)),
        int(inst.timeout.get("days", 0)),
        int(inst.timeout.get("hours", 0)),
        int(inst.timeout.get("minutes", 0)),
        int(inst.timeout.get("seconds", 0)),
        int(inst.timeout.get("milliseconds", 0)),
        int(inst.timeout.get("microseconds", 0)),
        int(inst.step),
    )

class FakeCursor:
    #Fake cursor, that simulates SELECT/INSERT/UPDATE/DELETE on an In-Memory-table.
    def __init__(self, store):
        # store: dict[str, tuple]  # instance_id -> row
        self.store = store
        self._row = None

    # Context-Manager
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False  

    def execute(self, sql, params=()):
        sql_up = sql.strip().upper()
        if sql_up.startswith("SELECT"):
            instance_id = params[0]
            self._row = self.store.get(instance_id, None)

        elif sql_up.startswith("INSERT"):
            state, instance_id, time, w, d, h, m, s, ms, us, step = params
            self.store[instance_id] = (
                state, instance_id, time, w, d, h, m, s, ms, us, step
            )
            self._row = None

        elif sql_up.startswith("UPDATE"):
            (state, time, w, d, h, m, s, ms, us, step, instance_id) = params
            if instance_id in self.store:
                self.store[instance_id] = (
                    state, instance_id, time, w, d, h, m, s, ms, us, step
                )
            self._row = None

        elif sql_up.startswith("DELETE"):
            instance_id = params[0]
            self.store.pop(instance_id, None)
            self._row = None

        else:
            raise AssertionError(f"Unexpected SQL in Test-Fake: {sql}")

    def fetchone(self):
        return self._row


class FakePG:
    """
    psycopg-Connection-Fake with .cursor() and .commit()
    """
    def __init__(self):
        self._store = {}  # "state"-Tabelle

    def cursor(self):
        return FakeCursor(self._store)

    def commit(self):
        pass  # no-op

class TestPostgresAdapter(unittest.TestCase):
    def setUp(self):
        importlib.reload(logmod)
        logmod.loglevel = "INFO"
        with open(logmod.logfile, "w", encoding="UTF-8"):
            pass

        self.client = FakePG()
        self.adapter = PostgresAdapter(
            postgres_client=self.client,
            compress=True
        )

    def test_init_logs(self):
        with open(logmod.logfile, "r", encoding="UTF-8") as f:
            content = f.read()
        self.assertIn("[INFO] PostgresAdapter initialized with compression: True", content)

    def test__load_instance_not_found(self):
        inst = self.adapter._load_instance("does-not-exist")
        self.assertIsNone(inst)
        with open(logmod.logfile, "r", encoding="UTF-8") as f:
            content = f.read()
        self.assertIn("No data found in PostgreSQL for instance does-not-exist", content)        

    def test__load_instance_found(self):
        instance_id = "abc-123"
        fake_state = {"test": "value"}
        fake_time = datetime.datetime(2024, 5, 6, 7, 8, 9, 123456)
        fake_timeout = {
            "weeks": 1, "days": 2, "hours": 3, "minutes": 4,
            "seconds": 5, "milliseconds": 6, "microseconds": 7
        }
        fake_step = 42

        inst_expected = InstanceState(
            state=fake_state,
            instance_id=instance_id,
            time=fake_time,
            timeout=fake_timeout,
            step=fake_step
        )

        self.client._store[instance_id] = _instance_to_row(inst_expected)

        # Load instance
        inst = self.adapter._load_instance(instance_id)

        self.assertIsInstance(inst, InstanceState)

        self.assertEqual(inst.instance_id, instance_id)
        self.assertEqual(inst.state, fake_state)               
        self.assertEqual(inst.step, fake_step)
        self.assertEqual(inst.timeout, fake_timeout)           
        self.assertEqual(inst.time, fake_time)                 

        with open(logmod.logfile, "r", encoding="UTF-8") as f:
            content = f.read()
        self.assertIn(f"Data retrieved from PostgreSQL for instance {instance_id}", content)
        self.assertIn(f"Instance {instance_id} loaded successfully from PostgreSQL", content)

    def test_load_instance(self):
        instance_id = "testtesttest"
        original_settings_log = {
            0: {"scenarioManager": {"scenario": {"constants": {"value1": 1, "value2": 2}}}},
            1: {"scenarioManager": {"scenario": {"constants": {"value1": 3, "value2": 4}}}},
        }
        original_results_log = {
            1: {"scenarioManager": {"scenario": {"value3": {1: 11}, "value4": {1: 12}}}},
            2: {"scenarioManager": {"scenario": {"value3": {2: 21}, "value4": {2: 22}}}},
        }
        original_scenario_cache = {
            "1": {"scenarioManager": {"scenario": {"flow1": {"1": 31}, "flow2": {"1": 32}}}},
            "2": {"scenarioManager": {"scenario": {"flow1": {"2": 41}, "flow2": {"2": 42}}}},
        }        
        fake_state = {
            "settings_log": compress_settings(original_settings_log),
            "results_log": compress_results(original_results_log), 
            "scenario_cache": original_scenario_cache
        }
        fake_time = datetime.datetime(2024, 5, 6, 7, 8, 9, 123456)
        fake_timeout = {
            "weeks": 1, "days": 2, "hours": 3, "minutes": 4,
            "seconds": 5, "milliseconds": 6, "microseconds": 7
        }
        fake_step = 1

        inst_expected = InstanceState(
            state=fake_state,
            instance_id=instance_id,
            time=fake_time,
            timeout=fake_timeout,
            step=fake_step
        )

        self.client._store[instance_id] = _instance_to_row(inst_expected)

        # Load instance
        state = self.adapter.load_instance(instance_id)

        with open(logmod.logfile, "r", encoding="UTF-8") as f:
            content = f.read()
        self.assertIn("Loading instance testtesttest", content)       
        self.assertIn("State loaded for instance testtesttest", content)
        self.assertIn("Decompressing state for instance testtesttest", content)     
        self.assertIn("State decompression completed for instance testtesttest", content)  
        self.assertIn("Numeric keys restored for instance testtesttest", content)  
        self.assertIn("Instance testtesttest loaded successfully", content)  

        self.assertEqual(state.state["settings_log"], decompress_settings(compress_settings(original_settings_log)))
        self.assertEqual(state.state["results_log"], decompress_results(compress_results(original_results_log)))
        self.assertEqual(state.state["scenario_cache"], self.adapter._restore_numeric_keys(original_scenario_cache))

    def test__load_instance_exception(self):
        # Mock-Client such that it Cursor.execute raises an exception
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg.Error("Simulated DB failure")

        mock_client = MagicMock()
        mock_client.cursor.return_value = mock_cursor

        adapter = PostgresAdapter(mock_client, compress=False)

        with self.assertRaises(psycopg.Error):
            adapter._load_instance("broken-id")

        with open(logmod.logfile, "r", encoding="UTF-8") as f:
            content = f.read()

        self.assertIn("Failed to load instance broken-id", content)
        self.assertIn("Simulated DB failure", content)

    def test_delete_instance(self):
        instance_id = "delete_this"
        fake_state = {"delete_test": "delete_value"}
        fake_time = datetime.datetime(2024, 1, 1, 12, 0, 0, 0)
        fake_timeout = {
            "weeks": 0, "days": 0, "hours": 0, "minutes": 0,
            "seconds": 0, "milliseconds": 0, "microseconds": 0
        }
        fake_step = 1

        inst = InstanceState(
            state=fake_state,
            instance_id=instance_id,
            time=fake_time,
            timeout=fake_timeout,
            step=fake_step
        )

        self.client._store[instance_id] = _instance_to_row(inst)

        # Delete instance
        inst = self.adapter.delete_instance(instance_id)        

        self.assertNotIn(instance_id, self.client._store)
        with open(logmod.logfile, "r", encoding="UTF-8") as f:
            content = f.read()
        self.assertIn(f"Deleting instance {instance_id} from PostgreSQL", content)
        self.assertIn(f"Instance {instance_id} deleted successfully from PostgreSQL", content)

    def test_delete_instance_exception(self):
        # Mock-Client such that it Cursor.execute raises an exception
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg.Error("Simulated DB failure")

        mock_client = MagicMock()
        mock_client.cursor.return_value = mock_cursor

        adapter = PostgresAdapter(mock_client, compress=False)

        with self.assertRaises(psycopg.Error):
            adapter.delete_instance("broken-id")

        with open(logmod.logfile, "r", encoding="UTF-8") as f:
            content = f.read()

        self.assertIn("Deleting instance broken-id from PostgreSQL", content)
        self.assertIn("Failed to delete instance broken-id from PostgreSQL: Simulated DB failure", content)

    def test_save_instance(self):
        #Insert new instance
        instance_id = "insert-this"
        fake_state = {"x": 1, "y": 2}
        fake_time = datetime.datetime(1999, 1, 1, 12, 1, 2, 3)
        fake_timeout = {
            "weeks": 0, "days": 0, "hours": 1, "minutes": 2,
            "seconds": 3, "milliseconds": 4, "microseconds": 5
        }

        inst = InstanceState(
            state=fake_state,
            instance_id=instance_id,
            time=fake_time,
            timeout=fake_timeout,
            step=0
        )

        self.adapter._save_instance(inst)

        self.assertIn(instance_id, self.client._store)
        stored_row = self.client._store[instance_id]
        expected_row = _instance_to_row(inst)
        self.assertEqual(stored_row, expected_row)

        with open(logmod.logfile, "r", encoding="UTF-8") as f:
            content = f.read()
        self.assertIn(f"Inserting new instance {instance_id} into PostgreSQL", content)
        self.assertIn(f"Instance {instance_id} inserted successfully into PostgreSQL", content)

        #update existing instance
        fake_state2 = {"x": 11, "y": 21}
        fake_time2 = datetime.datetime(2015, 2, 3, 4, 5, 6, 7)
        fake_timeout2 = {
            "weeks": 1, "days": 2, "hours": 3, "minutes": 4,
            "seconds": 5, "milliseconds": 6, "microseconds": 7
        }

        inst2 = InstanceState(
            state=fake_state2,
            instance_id=instance_id,
            time=fake_time2,
            timeout=fake_timeout2,
            step=1
        )

        self.adapter._save_instance(inst2)

        self.assertIn(instance_id, self.client._store)
        stored_row = self.client._store[instance_id]
        expected_row = _instance_to_row(inst2)
        self.assertEqual(stored_row, expected_row)

        with open(logmod.logfile, "r", encoding="UTF-8") as f:
            content = f.read()
        self.assertIn(f"Updating existing instance {instance_id} in PostgreSQL", content)
        self.assertIn(f"Instance {instance_id} updated successfully in PostgreSQL", content)

        #no update needed
        fake_state3 = {"x": 12, "y": 22}
        fake_time3 = datetime.datetime(2016, 3, 4, 5, 6, 7, 8)
        fake_timeout3 = {
            "weeks": 2, "days": 3, "hours": 4, "minutes": 5,
            "seconds": 6, "milliseconds": 7, "microseconds": 8
        }

        inst3 = InstanceState(
            state=fake_state3,
            instance_id=instance_id,
            time=fake_time3,
            timeout=fake_timeout3,
            step=1
        )

        self.adapter._save_instance(inst3)

        self.assertIn(instance_id, self.client._store)
        stored_row = self.client._store[instance_id]
        expected_row = _instance_to_row(inst2)
        self.assertEqual(stored_row, expected_row)

        with open(logmod.logfile, "r", encoding="UTF-8") as f:
            content = f.read()
        self.assertIn(f"Instance {instance_id} already up to date in PostgreSQL", content)        

    def test_save_instance_exception(self):
        # Mock-Client such that it Cursor.execute raises an exception
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg.Error("Simulated DB failure")

        mock_client = MagicMock()
        mock_client.cursor.return_value = mock_cursor

        #Insert new instance
        instance_id = "test-exception"
        fake_state = {"x": 1, "y": 2}
        fake_time = datetime.datetime(1999, 1, 1, 12, 1, 2, 3)
        fake_timeout = {
            "weeks": 0, "days": 0, "hours": 1, "minutes": 2,
            "seconds": 3, "milliseconds": 4, "microseconds": 5
        }

        inst = InstanceState(
            state=fake_state,
            instance_id=instance_id,
            time=fake_time,
            timeout=fake_timeout,
            step=0
        )

        self.adapter._postgres_client = mock_client

        with self.assertRaises(psycopg.Error):
            self.adapter._save_instance(inst)

        with open(logmod.logfile, "r", encoding="UTF-8") as f:
            content = f.read()

        self.assertIn("Saving instance test-exception to PostgreSQL", content)
        self.assertIn("Failed to save instance test-exception to PostgreSQL: Simulated DB failure", content)

if __name__ == '__main__':
    unittest.main()         