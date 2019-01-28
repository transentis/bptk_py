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


#################
## EVENT CLASS ##
#################

class Event:
    """
    The event class is used to capture event information. Each event has a name, the id of the sending agent, the id of the receiving agent an optionally also some data (the actual payload).
    """

    def __init__(self, name, sender_id, receiver_id, data=None):
        self.sender_id = sender_id
        self.name = name
        self.receiver_id = receiver_id
        self.data = data
