#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
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


class jsonMonitor():
    """
    Simple monitoring script for itmx files.
    Monitors itmx files and invokes parser when a change is detected
    """

    def __init__(self, json_file,  update_func):
        """

        :param json_file: path to itmx model
        :param dest: destination file .py
        :param update_func: a function that the monitor calls upon update to the source_file
        """
        self.update_func = update_func
        self.json_file = json_file


        log(
            "[INFO] JSON Monitor: Starting to Monitor {} for changes. Will update scenarios whenever I observe changes to it! ".format(
                json_file))

        # As long as this is True, I will keep monitoring. Otherwise the thread will terminate
        self.running = True

        # Initial last modification timestamp
        self._cached_stamp = os.stat(self.json_file).st_mtime

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
            if os.path.isfile(self.json_file):
                # <-- During initialization we change the working dir if the python file is not yet existent.
                # This is a thread, so it runs in background during these folder changes and may throw a "fileNotFrounderror" if we are not yet back to the working dir
                if os.name == "nt":
                    stamp = os.stat(str(self.json_file.replace("/", "\\"))).st_mtime
                else:
                    stamp = os.stat(str(self.json_file)).st_mtime

                ## Check if changed
                if stamp > self._cached_stamp:

                    log("[INFO] JSON Monitor: Observed a change to {} ".format(
                        str(self.json_file)))
                    self._cached_stamp = stamp

                    # File has changed, so parse model again

                    ## Refresh all scenarios with the given model file
                    self.update_func(self.json_file)
                    log("[INFO] JSON Monitor for {}: model updated and relaoded scenarios!".format(
                        str(self.json_file)))

                    # Store new timestamp as cached timestamp
                    self._cached_stamp = stamp
            time.sleep(1)

        log("[INFO] JSON Monitor for {}: I got killed... Goodbye!".format(str(self.json_file)))
