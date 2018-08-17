#                                                       /`-
# _                                  _   _             /####`-
#| |                                | | (_)           /########`-
#| |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
#| __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
#| |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018 transentis labs GmbH
#




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


class modelMonitor():
    """
    Simple monitoring script for itmx files.
    Monitors itmx files and invokes parser when a change is detected
    """

    def __init__(self, model_file, dest,update_func,itmx=True):
        """

        :param model_file: path to itmx model
        :param dest: destination file .py
        :param update_func: a function that the monitor calls upon an update to the model_file
        :param itmx: Default true. If not True, we do not monitor an itmx file. Hence, also usable for other files
        """
        self.update_func=update_func
        self.model_file = model_file
        self.itmx = itmx
        self.dest = dest
        if os.name == "nt":
            model_file = model_file.replace("/","\\")
            dest = dest.replace("/","\\")
            self.execute_script ="\”" + config.configuration["bptk_Py_module_path"] + "\\shell_scripts\\update_model.bat\” \”" + config.configuration["sd_py_compiler_root"] + "\” \”"  +  model_file + "\” \"" + dest + "\""
        else:
            current_dir = str(os.getcwd())
            self.execute_script = "node -r babel-register src/cli.js -i \"" + current_dir + "/" + model_file + "\" -t py -c > \"" + current_dir + "/" + dest +".py\""
        log("[INFO] Model Monitor: Starting to Monitor {} for changes. Will transform itmx file to Python model whenever I observe changes to it! Destination file: {}".format(model_file, dest))

        # As long as this is True, I will keep monitoring. Otherwise the thread will terminate
        self.running = True

        # Initial last modification timestamp
        self._cached_stamp = os.stat(self.model_file).st_mtime

        # Starting the thread
        t = Thread(target=self.__monitor, args=())
        t.start()



    def kill(self):
        """
        Kill method. Thread will die after calling this
        :return: None
        """
        self.running = False


    def __monitor(self):
        """
        Actual method that monitors the source file for changes
        :return: None
        """
        while self.running:
            ## Get last modification timestamp and compare to cached one

            stamp = os.stat(self.model_file).st_mtime

            ## Check if changed
            if stamp != self._cached_stamp:

                log("[INFO] Model Monitor for {}: Observed a change to the model. Calling the parser".format(str(self.model_file)))
                self._cached_stamp = stamp

                if self.itmx: # If we monitor an itmx file, call the sd-compiler to parse it to python
                    # File has changed, so parse model again
                    # Store current directory and chdir to sd compiler dir
                    current_dir = str(os.getcwd())
                    os.chdir(config.configuration["sd_py_compiler_root"])

                    exit_status = os.system(self.execute_script)

                    # Go back to working dir
                    os.chdir(current_dir)

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
