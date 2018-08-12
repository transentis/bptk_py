
####### IMPORTS
from threading import Thread
import time
from BPTK_Py.logger.logger import log
import os
import BPTK_Py.config.config as config
#######

########################
## ClASS MODELMONITOR ##
########################

### Simple monitoring script for itmx files. Still under development.
### Monitors itmx files and invokes parser when a change is detected
class modelMonitor():

    ## Init.
    # model_file: path to itmx model
    # dest: path to final python file
    def __init__(self, model_file, dest,update_func):
        self.update_func=update_func
        self.model_file = model_file
        if os.name == "nt":
            model_file = model_file.replace("/","\\")
            dest = dest.replace("/","\\")
            self.execute_script = config.configuration["bptk_Py_module_path"] + "\\shell_scripts\\update_model.bat " + config.configuration["sd_py_compiler_root"] + " "  +  model_file + " " + dest
        else:
            self.execute_script = "sh " + config.configuration["bptk_Py_module_path"] + "/shell_scripts/update_model.sh " + config.configuration["sd_py_compiler_root"] + " "  +  model_file + " " + dest
        log("[INFO] Model Monitor: Starting to Monitor {} for changes. Will transform itmx file to Python model whenever I observe changes to it! Destination file: {}".format(model_file, dest))

        # As long as this is True, I will keep monitoring. Otherwise the thread will terminate
        self.running = True

        # Initial last modification timestamp
        self._cached_stamp = os.stat(self.model_file).st_mtime

        # Starting the thread
        t = Thread(target=self.__monitor, args=())
        t.start()



    ### Kill method. Thread will die after calling this
    def kill(self):
        self.running = False

    # Actual method that monitors the source file for changes
    def __monitor(self):
        while self.running:
            ## Get last modification timestamp and compare to cached one
            stamp = os.stat(self.model_file).st_mtime

            ## Check if changed
            if stamp != self._cached_stamp:

                log("[INFO] Model Monitor for {}: Observed a change to the model. Calling the parser".format(str(self.model_file)))
                self._cached_stamp = stamp

                # File has changed, so parse model again
                exit_status = os.system(self.execute_script)

                ## Check if everything went well, i.e. exit status of the script = 0
                if exit_status != 0:
                    log("[ERROR] Problem calling the script for model conversion itmx --> python. Exit status: {}".format(str(exit_status)))

                ## Refresh all scenarios with the given model file
                self.update_func(self.model_file)
                log("[INFO] Model Monitor for {}: model updated and relaoded scenarios!".format(str(self.model_file)))

                # Store new timestamp as cached timestamp
                self._cached_stamp = stamp
            time.sleep(1)

        log("[INFO] Model Monitor for {}: I got killed... Goodbye!".format(str(self.model_file)))
