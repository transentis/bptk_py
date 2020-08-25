import json
import logging
from time import sleep

import pandas as pd
import requests
from cachetools import TTLCache, cached

from BPTK_Py.bptk import conf
from BPTK_Py.visualizations import visualizer

cache = TTLCache(maxsize=1024, ttl=100)


class bptk_remote:
    jobs = None

    def __init__(self, token, url):
        self.headers = {"Authorization": 'Bearer ' + token}
        self.base_url = url

    @cached(cache=cache)
    def list_equations(self, scenario_managers=[]):
        if len(scenario_managers) == 0:
            scenario_managers = [m["sm"] for m in self.jobs]

        equations = {}

        for job in self.jobs:
            if job["sm"] in scenario_managers:
                url = self.base_url + "/api/xmile/{}/equations".format(job["job_id"])

                response = requests.get(url, headers=self.headers)

                if response.status_code != 200:
                    logging.error("Problem accessing the equations endpoint for the job.")
                    return

                equations_remote = json.loads(response.text)
                equations[job["sm"]] = equations_remote["data"]

        for scenario_manager in equations.keys():
            print("Scenario Manager: '{}'".format(scenario_manager))

            for equation in equations[scenario_manager]:
                print("\t\t" + equation)

    def plot_scenarios(self, scenarios, scenario_managers, agents=[], agent_states=[], agent_properties=[],
                       agent_property_types=[], equations=[],
                       kind=None,
                       alpha=None, stacked=None,
                       freq="D", start_date="", title="", visualize_from_period=0, visualize_to_period=0, x_label="",
                       y_label="",
                       series_names={}, strategy=False,
                       progress_bar=False,
                       return_df=False):

        df = self.__get_results(str(scenarios), str(scenario_managers),
                                str(equations))
        v = visualizer(config=conf())
        return v.plot(df=df,
                      return_df=return_df,
                      visualize_from_period=visualize_from_period,
                      visualize_to_period=visualize_to_period,
                      stacked=stacked,
                      kind=kind,
                      title=title,
                      alpha=alpha,
                      x_label=x_label,
                      y_label=y_label,
                      start_date=start_date,
                      freq=freq,
                      series_names=series_names
                      )

    @cached(cache=cache)
    def __get_results(self, scenarios, scenario_managers,
                      equations):
        scenarios = eval(scenarios)
        scenario_managers = eval(scenario_managers)
        equations = eval(equations)
        data = []
        if not self.jobs:
            logging.error("Please create a job first by using 'submit()' or 'initialize()'")
            return

        if len(scenario_managers) == 0:
            scenario_managers = [m["sm"] for m in self.jobs]

        for job in self.jobs:
            if job["sm"] in scenario_managers:
                data += [self.get_results_for_job(job_id=job["job_id"],equations=str(equations))]

        # Convert format to be readable for Pandas!
        result = {"t": []}

        for job_data in data:

            for key, values in job_data.items():
                for element in values:
                    if not float(element["t"]) in result["t"]:
                        result["t"] += [float(element["t"])]

                    scenario_match = next((s for s in scenarios if key.lower().startswith(s.lower())), None)
                    equation_match = next((s for s in equations if key.lower().endswith(s.lower())), None)

                    if len(scenarios) == 0:
                        scenario_match = True

                    if len(equations) == 0:
                        equation_match = True

                    if scenario_match and equation_match:

                        if not key in result.keys():
                            result[key] = []

                        result[key] += [element["value"]]

        df = pd.DataFrame.from_dict(result)

        df = df.set_index("t")

        return df

    def upload_xmile(self,file, config):
        """
        Upload a simulation model along with its config to share it with others or initialize later
        :param file: Simulation file, stmx
        :param config: Configuration for the model (anonymous access, users to share with and so on)
        :return: The model ID of the newly generated and stored model
        """
        url = self.base_url + "/api/models/xmile/upload/"

        files = {"stmx": file, "config": config}
        try:
            response = requests.post(url, headers=self.headers, files=files)
            x = json.loads(response.text)
            model_id = x["id"]

            print("Successfully stored the model and configured it. Please note down this Model ID to access it later: '{}'".format(model_id))
        except:
            if response.status_code != 201:
                logging.error("There was a problem uploading the model: '{}', '{}'".format(response.status_code,response.text))


    def initialize_sd(self, model_id):
        """
        Initialize a given model using its model_id
        :param model_id: Model ID
        :return:
        """
        url = self.base_url + "/api/xmile/{}/initialize/".format(model_id)

        response = requests.get(url, headers=self.headers)

        if response.status_code == 201:
            print("Successfully initialized!")
            try:
                response = json.loads(response.text)
            except Exception as e:
                logging.error("Problem parsing server response: '{}'".format(response.text))
                return

            self.jobs = []

            for job in response:
                self.jobs += [{"job_id": job["job_id"], "sm": job["sm"]}]
                logging.info("Successfully created a new job. Job ID: '{}'".format(self.jobs))

            print("{} new job(s) created, one for each scenario manager.".format(len(self.jobs)))
        else:
            logging.error("Error initializing the model. Error code: {}, '{}'".format(response.status_code,response.text))

    def submit(self, stmx, scenarios, name="undefined"):
        """
        Submit a new configuration and stmx file
        :param stmx:
        :param scenarios:
        :return:
        """

        # Upload config and stmx file
        files = {"stmx": open(stmx, "r"), "scenario": open(scenarios, "r")}
        response = requests.post(self.base_url + "/api/xmile/create/{}".format(name), headers=self.headers, files=files)

        try:
            response = json.loads(response.text)
        except Exception as e:
            logging.error("Problem parsing server response: '{}'".format(response.text))
            return

        self.jobs = []

        for job in response:
            self.jobs += [{"job_id": job["job_id"], "sm": job["sm"]}]
            logging.info("Successfully created a new job. Job ID: '{}'".format(self.jobs))

        print("{} new job(s) created, one for each scenario manager.".format(len(self.jobs)))

    def __get_equations(self, equations, job_id):
        pass

    def __delete(self, job_id):
        pass

    @cached(cache=cache)
    def get_results_for_job(self, job_id, equations="[]"):
        response = requests.get(self.base_url + "/api/xmile/{}/run/".format(job_id))

        equations = eval(equations)
        status = json.loads(response.text)["status"]

        while status != "SUCCESS":
            logging.warning("Waiting for Job to finish. Current status: '{}'".format(status))
            ur = self.base_url + "/api/xmile/{}/status/".format(job_id)

            if len(equations) > 0:
                ur += "?equations=" + ",".join(equations)
            response = requests.get(self.base_url + "/api/xmile/{}/status/".format(job_id))

            status = json.loads(response.text)["status"]

            if status == "FAIL":
                logging.error(
                    "Job failed. Please retry or try locally using the offline API (maybe only for a few periods to check for errors in the model!)")
                return
            if status == "SUCCESS":
                break
            sleep(1)

        try:
            response = requests.get(self.base_url + "/api/xmile/{}/results".format(job_id),
                                    headers=self.headers)
            job_data = json.loads(response.text)["data"]
        except:
            logging.error("Problem downloading results: '{}'".format(response.text))
            return

        return job_data

    def disconnect(self):
        for job in self.jobs:
            url = self.base_url + "/api/xmile/{}/".format(job["job_id"])
            response = requests.delete(url, headers=self.headers)

            if response.status_code == 204:
                print("Successfully deleted the job for scenario manager '{}'!".format(job["sm"]))
            else:
                print("Problem deleting the job for scenario manager '{}': '{}'".format(job["sm"], response.text))

        print("Disconnected from API. Please use 'submit()' or 'initialize()' again to reconnect.")


def connect(url, token):
    """
    Generate a BPTK Remote object by connecting to remote API and check if it is available
    :param url: Base URL to BPTK API instance, e.g. https://api.myurl.com/. Omit /api/!
    :param token: Login token that you obtained by accessing the base url
    :return: A bptk_remote object that is connected to the API
    """
    # Return a bptk_remote object that has the flag "connected"
    headers = {
        'Authorization': 'Bearer ' + token}
    try:
        x = requests.get(url + "/login_token", headers=headers)

        if x.status_code != 200:
            logging.error("Problem establishing connection to remote BPTK backend: '{}'".format(x.text))
            return

        # bptk_remote object has to be instantiated by submitting a stmx and configuration
        bptk = bptk_remote(token=token, url=url)
        print("Connection successful! Please submit a new model by using the 'submit()' function!")
        return bptk

    except:
        logging.error("Problem connecting to Remote URL. Did you supply the correct URL and token?")
        return
