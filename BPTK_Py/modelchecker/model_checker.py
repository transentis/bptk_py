#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018 transentis labs GmbH
# MIT License


##########################
### CLASS MODELCHECKER ###
##########################

# Simple model checking
class ModelChecker():
    """simple model checking class. Can check assertions using lambda methods
    """

    def model_check(self, data, check, message="None"):
        """
        Model checker
        :param data: dataframe series or any data
        :param check: lambda function of structure : lambda data : BOOLEAN CHECK
        :param message: Error message if test failed
        :return: None
        """

        try:
            assert check(data), message
            print("[SUCCESS] Model check successful!")

        except AssertionError as e:
            print("[ERROR] Model Checking failed with message: \"{}\"".format(e))
