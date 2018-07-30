from functools import reduce
import math





dt = 1
starttime = 0


class simulation_model():
    class SimulatioModel():

        def __init__(self):
            # Simulation Buildins
            self.dt = 1
            self.starttime = 0
            self.stoptime = 10

            self.equations = {

                'customers': lambda t: self.equations['initialCustomers'](t) if t == 0
                else self.equations['customers'](t - dt) + dt * self.equations['acquisitionRate'](
                    t - dt),

                'potentialCustomers': lambda t: 6e6 if t <= starttime else self.equations["potentialCustomers"](
                    t - dt) + -1 * dt * self.equations["acquisitionRate"](t - dt),

                'totalAcquisitonsThroughMarketing': lambda t: max(0, 0 if t <= starttime else self.equations[
                                                                                                  'totalAcquisitonsThroughMarketing'](
                    t - dt) + dt * self.equations['inflow2'](t - dt)),

                'totalAcquisitonsThroughWordOfMouth' : lambda t : max(0,0 if t <= starttime else self.equations['totalAcquisitonsThroughWordOfMouth'](t-dt) + dt * self.equations["inflow"](t-dt)),

                'acquisitionRate': lambda t: max(0, min(self.equations["potentialCustomers"](t),
                                                        self.equations["acquisitionThroughMarketing"](t) + self.equations[
                                                            "acquisitionThroughWordOfMouth"](t))),

                'inflow': lambda t: max(0, self.equations["acquisitionThroughWordOfMouth"](t)),

                'inflow2': lambda t: max(0, self.equations["acquisitionThroughMarketing"](t)),

                'acquisitionThroughMarketing': lambda t: self.equations['marketingSuccesspct'](t) * self.equations[
                    'potentialCustomersReachedThroughMarketing'](t) / 100,

                'acquisitionThroughWordOfMouth': lambda t: self.equations['wordOfMouthSuccessPct'](t) * self.equations[
                    'potentialCustomersReachedThroughWordOfMouth'](t) / 100,

                'personsReachedPerKeurSpent': lambda t: 100,

                'potentialCustomersReachedThroughMarketing': lambda t: self.equations['remainingMarketPct'](t) *
                                                                       self.equations[
                                                                           'totalCustomersReachedThroughMarketing'](
                                                                           t) / 100,

                'potentialCustomersReachedThroughWordOfMouth': lambda t: self.equations['remainingMarketPct'](t) / 100 *
                                                                         self.equations[
                                                                             'totalCustomersReachedThroughWordOfMouth'](t),

                'remainingMarketPct': lambda t: 100 * self.equations['potentialCustomers'](t) / self.equations[
                    'totalMarket'](t),

                'totalCustomersReachedThroughMarketing': lambda t: self.equations['personsReachedPerKeurSpent'](t) *
                                                                   self.equations[
                                                                       'marketingSpending'](t),

                'totalCustomersReachedThroughWordOfMouth': lambda t: self.equations['customers'](t) * self.equations[
                    'wordOfMouthContactRate'](t),

                'totalMarket': lambda t: self.equations['customers'](t) + self.equations['potentialCustomers'](t),

                'initialCustomers': lambda t: 0,

                'marketingSpending': lambda t: 6e4,

                'marketingSuccesspct': lambda t: 0.1,

                'wordOfMouthContactRate': lambda t: 10,

                'wordOfMouthSuccessPct': lambda t: 1,
            }

            self.p = []
            self.dimensions = {
                    'Dim_Name_1': {
                        'labels': ['1'],
                        'variables': []
                    }
                }

            self.stocks = ['customers', 'potentialCustomers', 'totalAcquisitonsThroughMarketing',
                               'totalAcquisitonsThroughWordOfMouth']

            self.flows = ['acquisitionRate', 'inflow', 'inflow2']
            self.converters = ['acquisitionThroughMarketing', 'acquisitionThroughWordOfMouth', 'personsReachedPerKeurSpent',
                                   'potentialCustomersReachedThroughMarketing', 'potentialCustomersReachedThroughWordOfMouth',
                                   'remainingMarketPct', 'totalCustomersReachedThroughMarketing',
                                   'totalCustomersReachedThroughWordOfMouth',
                                   'totalMarket']
            self.gf = []
            self.constants = ['initialCustomers', 'marketingSpending', 'marketingSuccesspct', 'wordOfMouthContactRate',
                                  'wordOfMouthSuccessPct']
            self.events = [
                ]

            self.memo = {}
            for key in list(self.equations.keys()):
                self.memo[key] = {} # DICT VON DICTS


