

#################################
## IMPORT YOUR OWN MODEL HERE! ##
#################################
from model_stub import simulation_model


######### IMPORTS
from threading import Thread
import csv
import datetime
from logger.logger import log
import config.config as config
import pandas as pd
import sys
#########


now = datetime.datetime.now()
### SIMULATOR CLASS
class simulator():
    def __init__(self,model=simulation_model(),name="Simulation"):
        self.mod=model # The simulation model.
        self.results = [] # Will store the results
        self.threads = [] # List of threads for the simulations

        ## Create files for simulation results

        self.until = config.until
        self.finished_simulations_count = 0
        self.name = name


    def start(self,until=0,output=["csv"],name="Simulation"):


        equations = self.mod.stocks

        self.until = until
        log("[INFO] Starting {}  simulations".format(self.until * len(equations)))


        # Starting the simulations
        self.__simulate_equations(equations)

        # Waiting for the simulation threads to finish before I continue
        for thread in self.threads: #
            thread.join()


        if "csv" in output:
            log("[INFO] Simulations finished. Persisting results into CSV.")
            self.__write_results_to_csv()

        if "frame" in output:
            return pd.DataFrame(self.results)


    def __simulate_equations(self, equations):

        for equation in equations: # Start one thread for each equation
            t = Thread(target=self.__simulate, args=(equation,self.until))
            t.start()
            self.threads += [t]


    def __simulate(self, equation, until):
        ## First I make a local instance of the model. Why? Each simulation will work on its own object
        ## Hence, no worries about thread-safety! AND: Otherwise all simulations work with the same equations dict --> Thread safety slows this down!
        ## One thread at-a-time gains access to a dict!

        for i in range(0,until):
            result = self.mod.equations[equation](i)

            self.results += [{"equation" :equation ,"t":i,"result" :result}]

            self.finished_simulations_count += 1
        log("[INFO] Finished simulation of stock {}".format(str(equation)))


    def __write_results_to_csv(self):
        with open("results/results_{}_{}.csv".format(self.name,str(datetime.datetime.now())),"w",encoding="utf-8") as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=";")
            csvwriter.writerow(["equation","t","result"]) # Headline of file
            for result in self.results:
                row = [result["equation"],result["t"],result["result"]]
                csvwriter.writerow(row)


### END OF SIMULATOR CLASS



simulator = simulator(model=simulation_model(),name="Simulation")

frames =simulator.start(until=config.until+1,output=["csv","frame"])

log("[INFO]: Finished simulation. Took: {}".format(str(datetime.datetime.now() - now)))
print("[INFO]: Finished simulation. Took: {}".format(str(datetime.datetime.now() - now)))

