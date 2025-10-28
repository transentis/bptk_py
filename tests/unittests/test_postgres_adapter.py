import unittest, importlib, datetime, jsonpickle, psycopg
from unittest.mock import MagicMock

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

    def test_load_instance_not_found(self):
        inst = self.adapter._load_instance("does-not-exist")
        self.assertIsNone(inst)
        with open(logmod.logfile, "r", encoding="UTF-8") as f:
            content = f.read()
        self.assertIn("No data found in PostgreSQL for instance does-not-exist", content)        

    def test_load_instance_found(self):
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
            step=fake_step,
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

    def test_load_instance_exception(self):
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
            step=fake_step,
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

if __name__ == '__main__':
    unittest.main()         