"""sd_simple_project_v0 - generated from XMILE by the BPTK-Py compiler, target py-sddsl."""

from BPTK_Py import Model
from BPTK_Py import sd_functions as sd


class SdSimpleProjectV0(Model):

    def __init__(self):
        super().__init__(starttime=0.0, stoptime=120.0, dt=1.0, name='sd_simple_project_v0')

        # ── Defining the elements ────────────────────────────────────────────

        # Stocks
        closedTasks = self.stock('closedTasks')
        openTasks = self.stock('openTasks')
        staff = self.stock('staff')

        # Flows
        completionRate = self.flow('completionRate')

        # Converters
        currentDate = self.converter('currentDate')
        productivity = self.converter('productivity')
        remainingTime = self.converter('remainingTime')
        schedulePressure = self.converter('schedulePressure')

        # Constants
        deadline = self.constant('deadline')
        effortPerTask = self.constant('effortPerTask')
        initialOpenTasks = self.constant('initialOpenTasks')
        initialStaff = self.constant('initialStaff')

        # ── Setting the initial values and equations ─────────────────────────

        # Graphical functions
        self.points['productivity'] = [[0.0, 0.093], [0.25, 0.093], [0.5, 0.093], [0.75, 0.086], [1.0, 1.0], [1.25, 1.186], [1.5, 1.236], [1.75, 1.25], [2.0, 1.25], [2.25, 1.25], [2.5, 1.25]]

        # Stocks
        closedTasks.initial_value = 0.0
        closedTasks.inflows = [completionRate]
        openTasks.initial_value = initialOpenTasks
        openTasks.outflows = [completionRate]
        staff.initial_value = initialStaff

        # Flows
        completionRate.equation = sd.max(0.0, sd.min(openTasks, ((staff * productivity) / effortPerTask)))

        # Converters
        currentDate.equation = sd.time()
        productivity.equation = sd.lookup(schedulePressure, 'productivity')
        remainingTime.equation = sd.max((deadline - currentDate), 0.0)
        schedulePressure.equation = sd.min(((((openTasks * effortPerTask) / staff)) / sd.max(remainingTime, 1.0)), 2.5)

        # Constants
        deadline.equation = 100.0
        effortPerTask.equation = 1.0
        initialOpenTasks.equation = 110.0
        initialStaff.equation = 1.0


def simulation_model():
    return SdSimpleProjectV0()
