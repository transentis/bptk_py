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
    The Event class is used to capture event information. Each event has a name, the id of the sending agent, the id of the receiving agent an optionally also some data (the actual payload).
    """

    def __init__(self, name, sender_id, receiver_id, data=None):
        if sender_id and not type(sender_id) in [int,float]:
            raise ValueError("{} did not receive a correct type for sender_id. Allowed types: int and float".format(type(self)))

        if receiver_id and not type(receiver_id) in [int,float]:
            raise ValueError("{} did not receive a correct type for receiver_id. Allowed types: int and float".format(type(self)))

        self.sender_id = sender_id
        self.name = name
        self.receiver_id = receiver_id
        self.data = data


class DelayedEvent(Event):
    """
    The DelayedEvent class is used to send events that are not to be delivered in the next round but are delayed by a given number of time steps (dt).
    """

    def __init__(self, name, sender_id, receiver_id, delay, data=None,):
        super().__init__(name, sender_id, receiver_id, data)

        if not type(delay) in [int,float]:
            raise ValueError("{} did not receive a correct type for delay. Allowed types: int and float".format(type(self)))
        self.delay = delay
