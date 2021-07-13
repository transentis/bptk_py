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


#########################
## DATACOLLECTOR CLASS ##
#########################


class KinesisDataCollector:
    """
    A datacollector for the agent based simulation.
    Collects the output data of each agent/event and outputs them to a Kinesis stream (100 records per 1/10th seconds)
    For now it only outputs the agent statistics, not the event statistics
    """

    def __init__(self, target_streams=["BPTK-Demo"], region="eu-west-1"):
        """

        :param target_streams: List of streams to fire the events into
        :param region:  AWS region where the stream(s) are located
        """
        self.agent_statistics = {}
        self.event_statistics = {}

        self.client = kinesisProducer(stream_names=target_streams, region=region)

    def record_event(self, time, event):
        """
        Record an event
        :param time: t (int)
        :param event: event instance
        :return: None
        """
        if time not in self.event_statistics:
            self.event_statistics[time] = {}

        if event.name not in self.event_statistics[time]:
            self.event_statistics[time][event.name] = 0

        self.event_statistics[time][event.name] += 1

    def reset(self):
        """
        No effect in this data collector
        :return:
        """
        self.agent_statistics = {}

    def collect_agent_statistics(self, sim_time, agents):
        """
        Collect agent statistics from agent(s)
        :param sim_time: t (int)
        :param agents: list of Agent
        :return: None
        """

        for agent in agents:

            stats = {}
            stats["id"] = agent.id
            stats["time"] = sim_time

            for agent_property_name, agent_property_value in agent.properties.items():
                stats[agent_property_name] = agent_property_value['value']

            self.client.send_data(stats)

    def statistics(self):
        """
        Get the statistics collected
        :return: Dictionary
        """

        return {}


## You will need boto for accessing AWS.
try:
    from boto import kinesis
except ModuleNotFoundError as e:
    print("Module boto not available. This is required for acessing your AWS account. Please install using pip.")

import json
from time import sleep
from time import time


class kinesisProducer():

    def __init__(self, region="eu-west-1", stream_names=["BPTK-Demo"]):
        """
        Please make sure you used "aws configure" and have access to the stream(s) given

        :param region: AWS region where the streams(s) are located
        :param stream_names: List of stream(s) to output the data to
        """

        ## Create stream if not already existing
        self.kinesis = kinesis.connect_to_region(region)
        self.stream_names = stream_names

        for stream_name in stream_names:
            if not stream_name in self.kinesis.list_streams()['StreamNames']:
                print("Target Stream does not yet exist. Attempting to create.")
                stream = self.kinesis.create_stream(stream_name, shard_count=8)
                self.kinesis.describe_stream(stream_name)
                sleep(3)

        self.records = []

    def send_data(self, data=None):
        '''
        Send data to the AWS Kinesis stream(s)
        :param data: Dictionary of agent statistics
        :return:
        '''

        if data:
            data["timestamp"] = time()
            record = {'Data': json.dumps(data), 'PartitionKey': str(hash(data["id"]))}
            self.records.append(record)

            ## Only send  bunches of 100 records to Kinesis
            if len(self.records) == 100:
                for stream_name in self.stream_names:
                    self.kinesis.put_records(self.records, stream_name)

                self.records = []
                sleep(0.1)
