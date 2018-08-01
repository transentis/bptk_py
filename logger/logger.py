import config.config as config
import datetime


def log(message):
    message = message.replace("\n", "")
    if "logfile" in config.log_modes:
        with open(config.log_file, "a", encoding="UTF-8") as myfile:
            myfile.write(str(datetime.datetime.now()) + ", " + message + "\n")

    if "print" in config.log_modes or "[ERROR]" in message:
        print(str(datetime.datetime.now()) + ", " + message)
