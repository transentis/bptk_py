#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018 transentis management & consulting. All rights reserved.
#


##########################
### CLASS MODELCHECKER ###
##########################

# Simple model checking
class modelChecker():
    """simple model checking class"""


    def model_check(self, data, check, message="None"):
        """param check is a lambda method with one param: lambda data : CHECK A CONDITION"""
        try:
            assert check(data), message
            return 0  ## 0 = Success
        except AssertionError as e:
            print("[ERROR] Model Checking failed with {}".format(e))
            return 1  ## 1 = Error
