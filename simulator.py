

#################################
## IMPORT YOUR OWN MODEL HERE! ##
#################################
from model_stub import simulation_model


######### IMPORTS
from threading import Thread
import time
import datetime
from logger.logger import log
import config.config as config
import pandas as pd
#########


### SIMULATOR CLASS
class simulator():
    def __init__(self,model=simulation_model()):
        self.mod= simulation_model()
        self.results = []
        self.threads = []
        self.result_frames = {}
        self.monitoring_thread = Thread()

        ## Create files for simulation results

        self.until = 0
        self.finished_simulations_count = 0




    def start(self,until=0):

        equations = self.mod.stocks

        self.until = until
        log("[INFO] Starting {}  simulations".format(self.until * len(equations)))

        # Building the dataframes which store the results
        self.__create_dataframes(equations)

        # Starting the simulations
        self.__simulate_equations(equations)

        for thread in self.threads:
            thread.join()

        log("[INFO] Simulations finished. Persisting results into CSV.")
        self.__write_out_results()



    def __create_dataframes(self, equations):
        for equation in equations:
                self.result_frames[equation] = pd.DataFrame(columns=["equation","t","result"])

    def __simulate_equations(self, equations):
        # Monitoring/ Status thread:
        t = Thread(target=self.__output_status, args=(datetime.datetime.now(),len(equations),self.until,))
        t.start()
        self.monitoring_thread = t


        for equation in equations:
            for i in range(0,self.until):
                t = Thread(target=self.__simulate, args=(equation, i))
                t.start()
                self.threads += [t]



    def __simulate(self, equation, until):
        ## First I make a local instance of the model. Why? Each simulation will work on its own object
        ## Hence, no worries about thread-safety! AND: Otherwise all simulations work with the same equations dict --> Thread safety slows this down!
        ## One thread at-a-time gains access to a dict!
        my_own_model = simulation_model()
        my_own_dictionary = my_own_model.equations.copy()
        result = my_own_dictionary[equation](until)

        self.results += "{},{},{}".format(str(equation), str(until), str(result))
        self.__cache_results(result=[str(equation), str(until), str(result)], equation=equation)
        self.finished_simulations_count += 1
        log("[INFO] Finished simulation of stock {} for t={}. Result={}".format(str(equation),until,str(result)))



    def __output_status(self,start,simulation_count,until):

        number_simulations = until * simulation_count
        active_simulations = number_simulations - self.finished_simulations_count # Number of active threads -2: One is me, the other is the main thread
        while active_simulations > 0:
            active_simulations = number_simulations - self.finished_simulations_count
            log("[INFO] Simulation running. Finished {} % of simulations. Running simulations: {}. Simulations overall: {}. Runtime: {}".format((number_simulations-active_simulations)/number_simulations*100, active_simulations,number_simulations, datetime.datetime.now()-start))
            time.sleep(5)


        log("[INFO] Simulation finished! Took: {}".format(datetime.datetime.now()-start))


    def __cache_results(self, result, equation):
        df = self.result_frames[equation]
        try:
            arow = {"equation" : result[0], "t":result[1], "result" : result[2]}
            df.loc[len(df)] = arow
            #self.result_frames[equation].loc[len(self.result_frames[equation])] = {"equation" : result[0], "t":result[1], "result" : result[2]}

        except ValueError as e:
            print("[ERROR] adding results to dataframe for equation {} with result list: {}".format(equation,str(result)))


    def __write_out_results(self):
        for equation in self.result_frames.keys():
            df = self.result_frames[equation]
            df.sort_values(by='t')
            df.to_csv("results/result_{}.csv".format(equation),index_label=False,index=False)


### END OF SIMULATOR CLASS



simulator = simulator(model=simulation_model())

simulator.start(until=config.until+1)
