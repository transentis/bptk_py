import config.config as config
import datetime

def log(message):

    with open(config.log_file, "a",encoding="UTF-8") as myfile:
        message = message.replace("\n","")
        if "logfile" in config.log_modes:
            myfile.write(str(datetime.datetime.now()) + ", " + message +"\n")

        if "print" in config.log_modes:
            print(str(datetime.datetime.now()) + ", " + message )






