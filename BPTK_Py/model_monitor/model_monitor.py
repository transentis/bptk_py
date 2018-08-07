
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
    def __init__(self, model_file, dest):

        self.model_file = model_file

        self.execute_script = "sh BPTK_Py/shell_scripts/update_model.sh " + config.configuration["sd_py_compiler_root"] + " "  +  model_file + " " + dest

        log("[INFO] Model Monitor: Starting to Monitor {} for changes. Will transform itmx file to Python model whenever I observe changes to it! Destination file: {}".format(model_file, dest))
        self.running = True
        self._cached_stamp = os.stat(self.model_file).st_mtime
        t = Thread(target=self.__monitor, args=())
        t.start()



    ### Kill method. Thread will die after calling this
    def kill(self):
        self.running = False

    def __monitor(self):
        while self.running:
            stamp = os.stat(self.model_file).st_mtime
            if stamp != self._cached_stamp:
                log("[INFO] Model Monitor for {}: Observed a change to the model. Calling the parser".format(str(self.model_file)))
                self._cached_stamp = stamp

                # File has changed, so parse model again
                os.system(self.execute_script)
                log("[INFO] Model Monitor for {}: model updated!".format(str(self.model_file)))
            time.sleep(1)

        log("[INFO] Model Monitor for {}: I got killed... Goodbye!".format(str(self.model_file)))
