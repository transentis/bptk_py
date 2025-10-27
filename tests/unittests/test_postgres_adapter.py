import unittest, importlib, datetime, jsonpickle
import BPTK_Py.logger.logger as logmod

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
        # Logger frisch setzen
        importlib.reload(logmod)
        logmod.loglevel = "INFO"
        # Logfile bereitstellen/leeren
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
        # optional: Log prüfen
        with open(logmod.logfile, "r", encoding="UTF-8") as f:
            content = f.read()
        self.assertIn("No data found in PostgreSQL for instance does-not-exist", content)        

if __name__ == '__main__':
    unittest.main()         