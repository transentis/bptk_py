from functools import reduce
import math

dt = 1
starttime = 0


class simulation_model():

    def __init__(self):
        # Simulation Buildins
        self.dt = 1
        self.starttime = 0
        self.stoptime = 10

        self.equations = {

            'customers': lambda t: self.memoize('initialCustomers', t) if t == 0
            else self.equations['customers'](t - dt) + dt * self.memoize('acquisitionRate',
                                                                         t - dt),

            'potentialCustomers': lambda t: 6e6 if t <= starttime else self.memoize("potentialCustomers",
                                                                                    t - dt) + -1 * dt * self.memoize(
                "acquisitionRate", t - dt),

            'totalAcquisitonsThroughMarketing': lambda t: max(0, 0 if t <= starttime else self.memoize(
                'totalAcquisitonsThroughMarketing', t - dt) + dt * self.memoize('inflow2', t - dt)),

            'totalAcquisitonsThroughWordOfMouth': lambda t: max(0, 0 if t <= starttime else self.memoize(
                'totalAcquisitonsThroughWordOfMouth', t - dt) + dt * self.memoize("inflow", t - dt)),

            'acquisitionRate': lambda t: max(0, min(self.memoize("potentialCustomers", t),
                                                    self.memoize("acquisitionThroughMarketing", t) + self.memoize(
                                                        "acquisitionThroughWordOfMouth", t))),

            'inflow': lambda t: max(0, self.memoize("acquisitionThroughWordOfMouth", t)),

            'inflow2': lambda t: max(0, self.memoize("acquisitionThroughMarketing", t)),

            'acquisitionThroughMarketing': lambda t: self.memoize('marketingSuccesspct', t) * self.memoize(
                'potentialCustomersReachedThroughMarketing', t) / 100,

            'acquisitionThroughWordOfMouth': lambda t: self.memoize('wordOfMouthSuccessPct', t) * self.memoize(
                'potentialCustomersReachedThroughWordOfMouth', t) / 100,

            'personsReachedPerKeurSpent': lambda t: 100,

            'potentialCustomersReachedThroughMarketing': lambda t: self.memoize('remainingMarketPct', t) *
                                                                   self.memoize(
                                                                       'totalCustomersReachedThroughMarketing',
                                                                       t) / 100,

            'potentialCustomersReachedThroughWordOfMouth': lambda t: self.memoize('remainingMarketPct', t) / 100 *
                                                                     self.memoize(
                                                                         'totalCustomersReachedThroughWordOfMouth', t),

            'remainingMarketPct': lambda t: 100 * self.memoize('potentialCustomers', t) / self.memoize(
                'totalMarket', t),

            'totalCustomersReachedThroughMarketing': lambda t: self.memoize('personsReachedPerKeurSpent', t) *
                                                               self.memoize(
                                                                   'marketingSpending', t),

            'totalCustomersReachedThroughWordOfMouth': lambda t: self.memoize('customers', t) * self.memoize(
                'wordOfMouthContactRate', t),

            'totalMarket': lambda t: self.memoize('customers', t) + self.memoize('potentialCustomers', t),

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
            self.memo[key] = {}  # DICT VON DICTS

    def memoize(self, equation, arg):
        mymemo = self.memo[equation]
        if arg in mymemo.keys():
            return mymemo[arg]
        else:
            result = self.equations[equation](arg)
            mymemo[arg] = result
            return result
