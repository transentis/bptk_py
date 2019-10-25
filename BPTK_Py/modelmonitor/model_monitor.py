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


import os
import time

from threading import Thread

import BPTK_Py.config.config as config
from ..logger import log
from BPTK_Py.sdcompiler.compile import compile_xmile as compile

########################
## ClASS MODELMONITOR ##
########################


class ModelMonitor():
    """
    Simple monitoring script for itmx files.
    Monitors itmx files and invokes parser when a change is detected
    """

    def __init__(self, source_file, dest, update_func):
        """

        :param source_file: path to itmx model
        :param dest: destination file .py
        :param update_func: a function that the monitor calls upon update to the source_file
        """
        self.update_func = update_func
        self.source_file = source_file
        self.dest = dest

        current_dir = str(os.getcwd())
        self.execute_script = "node -r babel-register src/cli.js -i \"" + current_dir + "/" + source_file + "\" -t py -c > \"" + current_dir + "/" + dest + ".py\""
        log(
            "[INFO] ABMModel Monitor: Starting to Monitor {} for changes. Will transform itmx file to Python model whenever I observe changes to it! Destination file: {}".format(
                source_file, dest))

        # As long as this is True, I will keep monitoring. Otherwise the thread will terminate
        self.running = True

        # Initial last modification timestamp
        self._cached_stamp = os.stat(self.source_file).st_mtime

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
            if os.path.isfile(self.source_file):
                # <-- During initialization we change the working dir if the python file is not yet existent.
                # This is a thread, so it runs in background during these folder changes and may throw a "fileNotFrounderror" if we are not yet back to the working dir
                if os.name == "nt":
                    stamp = os.stat(str(self.source_file.replace("/", "\\"))).st_mtime
                else:
                    stamp = os.stat(str(self.source_file)).st_mtime

                ## Check if changed
                if stamp > self._cached_stamp:

                    log("[INFO] ABMModel Monitor for {}: Observed a change to the model. Calling the parser".format(
                        str(self.source_file)))
                    self._cached_stamp = stamp

                    # File has changed, so parse model again
                    # Store current directory and chdir to sd compiler dir
                    current_dir = str(os.getcwd())
                    #os.chdir(config.configuration["sd_py_compiler_root"])
                    print(self.source_file)

                    output = compile(target="py",src=self.source_file,dest=self.dest + ".py")

                    # Go back to working dir
                    #os.chdir(current_dir)

                    ## Check if everything went well, i.e. exit status of the script = 0
                    if "error" in str(output).lower():
                        log("[ERROR] Tried to convert {} but to {} but got error: {}".format(str(self.source_file), str(
                            self.dest) + ".py", str(output)))
                        self.running = False
                        return None

                    ## Refresh all scenarios with the given model file
                    self.update_func(self.source_file)
                    log("[INFO] ABMModel Monitor for {}: model updated and relaoded scenarios!".format(
                        str(self.source_file)))

                    # Store new timestamp as cached timestamp
                    self._cached_stamp = stamp
            time.sleep(1)

        log("[INFO] Model Monitor for {}: I got killed... Goodbye!".format(str(self.source_file)))
