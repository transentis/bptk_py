#                                                       /`-
# _                                  _   _             /####`-
#| |                                | | (_)           /########`-
#| |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
#| __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
#| |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018 transentis labs GmbH
# MIT License



import BPTK_Py.config.config as config
import datetime


def log(message):
    """logs all log messages either to file or stdout"""
    message = message.replace("\n", "")

    if config.loglevel == "ERROR":
        if not "ERROR" in message:
            return

    if config.loglevel == "WARN":
        if not "ERROR" in message and not "WARN" in message:
            return


    if "logfile" in config.configuration["log_modes"]:
        with open(config.configuration["log_file"], "a", encoding="UTF-8") as myfile:
            myfile.write(str(datetime.datetime.now()) + ", " + message + "\n")

    if "print" in config.configuration["log_modes"] or "[ERROR]" in message:
        print(str(datetime.datetime.now()) + ", " + message)
