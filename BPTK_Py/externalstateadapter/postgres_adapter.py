#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2025 transentis labs GmbH
# MIT License

import datetime

import jsonpickle
import psycopg
from .externalStateAdapter import ExternalStateAdapter, InstanceState
from ..logger import log

# Postgres Create Script:
#
# CREATE TABLE "state" (
#   "state" text,
#   "instance_id" text,
#   "time" text,
#   "timeout.weeks" bigint,
#   "timeout.days" bigint,
#   "timeout.hours" bigint,
#   "timeout.minutes" bigint,
#   "timeout.seconds" bigint,
#   "timeout.milliseconds" bigint,
#   "timeout.microseconds" bigint,
#   "step" bigint
# );


class PostgresAdapter(ExternalStateAdapter):
    def __init__(self, postgres_client, compress: bool):
        super().__init__(compress)
        self._postgres_client = postgres_client
        log(f"[INFO] PostgresAdapter initialized with compression: {compress}")

    def _load_instance(self, instance_uuid: str) -> InstanceState:
        log(f"[INFO] Loading instance {instance_uuid} from PostgreSQL")
        try:
            with self._postgres_client.cursor() as cur:
                cur.execute("SELECT * FROM state WHERE instance_id = %s", (instance_uuid,))
                res = cur.fetchone()

            if res is None:
                log(f"[INFO] No data found in PostgreSQL for instance {instance_uuid}")
            else:
                log(f"[INFO] Data retrieved from PostgreSQL for instance {instance_uuid}")

            result = self._tuple_to_state(res)
            if result:
                log(f"[INFO] Instance {instance_uuid} loaded successfully from PostgreSQL")
            return result
        except Exception as e:
            log(f"[ERROR] Failed to load instance {instance_uuid} from PostgreSQL: {str(e)}")
            raise

   

    def delete_instance(self, instance_uuid: str):
        log(f"[INFO] Deleting instance {instance_uuid} from PostgreSQL")
        try:
            with self._postgres_client.cursor() as cur:
                cur.execute("DELETE FROM state WHERE instance_id = %s", (instance_uuid,))
                self._postgres_client.commit()
            log(f"[INFO] Instance {instance_uuid} deleted successfully from PostgreSQL")
        except Exception as e:
            log(f"[ERROR] Failed to delete instance {instance_uuid} from PostgreSQL: {str(e)}")
            raise
    
    def _save_instance(self, instance_state: InstanceState):
        log(f"[INFO] Saving instance {instance_state.instance_id if instance_state else 'None'} to PostgreSQL")
        try:
            with self._postgres_client.cursor() as cur:
                cur.execute("SELECT * FROM state WHERE instance_id = %s", (instance_state.instance_id,))

                postgres_data = {
                    "state": jsonpickle.dumps(instance_state.state) if instance_state.state is not None else None,
                    "instance_id": instance_state.instance_id,
                    "time": str(instance_state.time),
                    "timeout.weeks": instance_state.timeout["weeks"],
                    "timeout.days": instance_state.timeout["days"],
                    "timeout.hours": instance_state.timeout["hours"],
                    "timeout.minutes": instance_state.timeout["minutes"],
                    "timeout.seconds": instance_state.timeout["seconds"],
                    "timeout.milliseconds": instance_state.timeout["milliseconds"],
                    "timeout.microseconds": instance_state.timeout["microseconds"],
                    "step": instance_state.step
                }

                res = cur.fetchone()
                if res is None:
                    log(f"[INFO] Inserting new instance {instance_state.instance_id} into PostgreSQL")
                    cur.execute(
                        "INSERT INTO state (state, instance_id, time, \"timeout.weeks\", \"timeout.days\", \"timeout.hours\", \"timeout.minutes\", \"timeout.seconds\", \"timeout.milliseconds\", \"timeout.microseconds\", step) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (postgres_data["state"], postgres_data["instance_id"], postgres_data["time"], postgres_data["timeout.weeks"], postgres_data["timeout.days"], postgres_data["timeout.hours"], postgres_data["timeout.minutes"], postgres_data["timeout.seconds"], postgres_data["timeout.milliseconds"], postgres_data["timeout.microseconds"], postgres_data["step"])
                    )
                    self._postgres_client.commit()
                    log(f"[INFO] Instance {instance_state.instance_id} inserted successfully into PostgreSQL")
                elif res[10] != instance_state.step:
                    log(f"[INFO] Updating existing instance {instance_state.instance_id} in PostgreSQL (step {res[10]} -> {instance_state.step})")
                    cur.execute("UPDATE state SET state = %s, time = %s, \"timeout.weeks\" = %s, \"timeout.days\" = %s, \"timeout.hours\" = %s, \"timeout.minutes\" = %s, \"timeout.seconds\" = %s, \"timeout.milliseconds\" = %s, \"timeout.microseconds\" = %s, step = %s WHERE instance_id = %s", (postgres_data["state"], postgres_data["time"], postgres_data["timeout.weeks"], postgres_data["timeout.days"], postgres_data["timeout.hours"], postgres_data["timeout.minutes"], postgres_data["timeout.seconds"], postgres_data["timeout.milliseconds"], postgres_data["timeout.microseconds"], postgres_data["step"], postgres_data["instance_id"]))
                    self._postgres_client.commit()
                    log(f"[INFO] Instance {instance_state.instance_id} updated successfully in PostgreSQL")
                else:
                    log(f"[INFO] Instance {instance_state.instance_id} already up to date in PostgreSQL (step {res[10]})")

        except (Exception, psycopg.Error) as error:
            log(f"[ERROR] Failed to save instance {instance_state.instance_id if instance_state else 'None'} to PostgreSQL: {str(error)}")
            raise
    
    def _tuple_to_state(self, state_tuple: tuple) -> InstanceState:
        if state_tuple is None:
            return None

        log(f"[INFO] Converting PostgreSQL tuple to InstanceState for instance {state_tuple[1] if state_tuple else 'None'}")
        return InstanceState(
            state=jsonpickle.loads(state_tuple[0]) if state_tuple[0] is not None else None,
            instance_id=state_tuple[1],
            time=datetime.datetime.strptime(state_tuple[2], "%Y-%m-%d %H:%M:%S.%f"),
            timeout = {
                "weeks": state_tuple[3],
                "days": state_tuple[4],
                "hours": state_tuple[5],
                "minutes":  state_tuple[6],
                "seconds": state_tuple[7],
                "milliseconds": state_tuple[8],
                "microseconds":state_tuple[9]
            },
            step=state_tuple[10]
        )

   
