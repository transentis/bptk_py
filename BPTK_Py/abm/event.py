class Event:

    def __init__(self, name, sender_id, receiver_id, data=None):
        self.sender_id = sender_id
        self.name = name
        self.receiver_id = receiver_id
        self.data = data


