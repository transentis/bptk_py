from threading import Thread
import time
import os
from subprocess import call
import BPTK_Py.config.config as config
from BPTK_Py.logger.logger import log

import os

class modelMonitor():
    def __init__(self, model_file, dest):


        self.model_file = model_file

        self.execute_script = "/Users/dominikschroeck/Code/sd-compiler/bin/sdcc_test -i " + model_file + " -t py > " + dest

        log("[INFO] Model Monitor: Starting to Monitor {} for changes. Will transform itmx file to Python model whenever I observe changes to it! Destination file: {}".format(model_file, dest))
        self.running = True
        self._cached_stamp = os.stat(self.model_file).st_mtime
        t = Thread(target=self.__monitor, args=())
        t.start()


    def kill(self):
        self.running = False

    def __monitor(self):
        while self.running:
            stamp = os.stat(self.model_file).st_mtime
            if stamp != self._cached_stamp:
                log("[INFO] Model Monitor: Observed a change to the model. Calling the parser")
                self._cached_stamp = stamp

                # File has changed, so parse model again
                #os.system(self.execute_script)
                log("[WARN] Model Monitor UPDATE METHOD NOT YET IMPLEMENTED!")
            time.sleep(1)

        log("[INFO] Model Monitor: I got killed... Goodbye!")
