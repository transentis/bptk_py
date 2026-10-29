"""make_your_psf_grow - generated from XMILE by the BPTK-Py compiler, target py-sddsl."""

from BPTK_Py import Model
from BPTK_Py import sd_functions as sd


class MakeYourPsfGrow(Model):

    def __init__(self):
        super().__init__(starttime=1.0, stoptime=24.0, dt=1.0, name='make_your_psf_grow')

        # ── Defining the elements ────────────────────────────────────────────

        # Stocks
        cash__cash = self.stock('cash.cash')
        cost__professionalStaff = self.stock('cost.professionalStaff')
        kpi__professionalStaff = self.stock('kpi.professionalStaff')
        kpi__projects = self.stock('kpi.projects')
        projects__projects = self.stock('projects.projects')
        projects__proposals = self.stock('projects.proposals')
        revenue__receivables = self.stock('revenue.receivables')
        staff__professionalStaff = self.stock('staff.professionalStaff')
        staff__staffInRecruitment = self.stock('staff.staffInRecruitment')

        # Flows
        cash__cashIn = self.flow('cash.cashIn')
        cash__cashOut = self.flow('cash.cashOut')
        projects__deliveringProjects = self.flow('projects.deliveringProjects')
        projects__prospectingProjects = self.flow('projects.prospectingProjects')
        projects__winningProjects = self.flow('projects.winningProjects')
        revenue__collectingRevenue = self.flow('revenue.collectingRevenue')
        revenue__makingRevenue = self.flow('revenue.makingRevenue')
        staff__hiringStaff = self.flow('staff.hiringStaff')
        staff__staffArriving = self.flow('staff.staffArriving')

        # Converters
        cash__cashFlow = self.converter('cash.cashFlow')
        cash__collectingRevenue = self.converter('cash.collectingRevenue')
        cash__cost = self.converter('cash.cost')
        cost__cost = self.converter('cost.cost')
        cost__staffCost = self.converter('cost.staffCost')
        cost__staffSalary = self.converter('cost.staffSalary')
        kpi__acquisitionToDeliveryRatio_ = self.converter('kpi.acquisitionToDeliveryRatio%')
        kpi__cashFlow = self.converter('kpi.cashFlow')
        kpi__cashFlowPerProfessional = self.converter('kpi.cashFlowPerProfessional')
        kpi__deliveringProjects = self.converter('kpi.deliveringProjects')
        kpi__maxiumProjectCapacity = self.converter('kpi.maxiumProjectCapacity')
        kpi__projectBacklog = self.converter('kpi.projectBacklog')
        kpi__projectVolume = self.converter('kpi.projectVolume')
        kpi__prospectingEffort = self.converter('kpi.prospectingEffort')
        kpi__targetBusinessDevelopmentAllocation_ = self.converter('kpi.targetBusinessDevelopmentAllocation%')
        kpi__targetProjctDeliveryCapacity = self.converter('kpi.targetProjctDeliveryCapacity')
        kpi__targetProjectStaff = self.converter('kpi.targetProjectStaff')
        kpi__utilization_ = self.converter('kpi.utilization%')
        projects__businessDevelopmentCapacity = self.converter('projects.businessDevelopmentCapacity')
        projects__projectDeliveryCapacity = self.converter('projects.projectDeliveryCapacity')
        projects__projectDeliveryRate = self.converter('projects.projectDeliveryRate')
        projects__projectProposalRate = self.converter('projects.projectProposalRate')
        revenue__deliveringProjects = self.converter('revenue.deliveringProjects')
        revenue__revenue = self.converter('revenue.revenue')
        staff__actualBusinessDevelopmentAllocation_ = self.converter('staff.actualBusinessDevelopmentAllocation%')
        staff__businessDevelopmentAllocation_ = self.converter('staff.businessDevelopmentAllocation%')
        staff__businessDevelopmentCapacity = self.converter('staff.businessDevelopmentCapacity')
        staff__hiringRate = self.converter('staff.hiringRate')
        staff__projectDeliveryCapacity = self.converter('staff.projectDeliveryCapacity')
        staff__steadyGrowthPolicyOn1 = self.converter('staff.steadyGrowthPolicyOn1')
        staff__targetBusinessDevStaff_ = self.converter('staff.targetBusinessDevStaff%')
        staff__workCapacity = self.converter('staff.workCapacity')

        # Constants
        cash__easyTargetCash = self.constant('cash.easyTargetCash')
        cash__expertTargetCash = self.constant('cash.expertTargetCash')
        cash__minimumCash = self.constant('cash.minimumCash')
        cost__overheadCost = self.constant('cost.overheadCost')
        cost__workplaceCost = self.constant('cost.workplaceCost')
        kpi__minimumBusDevAllocationOn = self.constant('kpi.minimumBusDevAllocationOn')
        kpi__steadyGrowthPolicyOn = self.constant('kpi.steadyGrowthPolicyOn')
        kpi__targetBacklog = self.constant('kpi.targetBacklog')
        projects__projectAcquisitionDuration = self.constant('projects.projectAcquisitionDuration')
        projects__projectVolume = self.constant('projects.projectVolume')
        projects__prospectingEffort = self.constant('projects.prospectingEffort')
        revenue__collectionTime = self.constant('revenue.collectionTime')
        revenue__projectDeliveryFee = self.constant('revenue.projectDeliveryFee')
        staff__hiringDuration = self.constant('staff.hiringDuration')
        staff__steadyGrowthRate_ = self.constant('staff.steadyGrowthRate%')
        staff__workMonth = self.constant('staff.workMonth')

        # ── Setting the initial values and equations ─────────────────────────

        # Graphical functions
        self.points['staff.businessDevelopmentAllocation%'] = [[1.0, 20.0], [2.0, 20.0], [3.0, 20.0], [4.0, 20.0], [5.0, 20.0], [6.0, 20.0], [7.0, 20.0], [8.0, 20.0], [9.0, 20.0], [10.0, 20.0], [11.0, 20.0], [12.0, 20.0], [13.0, 20.0], [14.0, 20.0], [15.0, 20.0], [16.0, 20.0], [17.0, 20.0], [18.0, 20.0], [19.0, 20.0], [20.0, 20.0], [21.0, 20.0], [22.0, 20.0], [23.0, 20.0], [24.0, 20.0]]
        self.points['staff.hiringRate'] = [[1.0, 0.0], [2.0, 0.0], [3.0, 0.0], [4.0, 0.0], [5.0, 0.0], [6.0, 0.0], [7.0, 0.0], [8.0, 0.0], [9.0, 0.0], [10.0, 0.0], [11.0, 0.0], [12.0, 0.0], [13.0, 0.0], [14.0, 0.0], [15.0, 0.0], [16.0, 0.0], [17.0, 0.0], [18.0, 0.0], [19.0, 0.0], [20.0, 0.0], [21.0, 0.0], [22.0, 0.0], [23.0, 0.0], [24.0, 0.0]]

        # Stocks
        cash__cash.initial_value = 1000.0
        cash__cash.inflows = [cash__cashIn]
        cash__cash.outflows = [cash__cashOut]
        cost__professionalStaff.initial_value = 0.0
        kpi__professionalStaff.initial_value = 0.0
        kpi__projects.initial_value = 0.0
        projects__projects.initial_value = 320.0
        projects__projects.inflows = [projects__winningProjects]
        projects__projects.outflows = [projects__deliveringProjects]
        projects__proposals.initial_value = 320.0
        projects__proposals.inflows = [projects__prospectingProjects]
        projects__proposals.outflows = [projects__winningProjects]
        revenue__receivables.initial_value = 0.0
        revenue__receivables.inflows = [revenue__makingRevenue]
        revenue__receivables.outflows = [revenue__collectingRevenue]
        staff__professionalStaff.initial_value = 200.0
        staff__professionalStaff.inflows = [staff__staffArriving]
        staff__staffInRecruitment.initial_value = 0.0
        staff__staffInRecruitment.inflows = [staff__hiringStaff]
        staff__staffInRecruitment.outflows = [staff__staffArriving]

        # Flows
        cash__cashIn.equation = sd.max(0.0, revenue__collectingRevenue)
        cash__cashOut.equation = sd.max(0.0, cost__cost)
        projects__deliveringProjects.equation = sd.max(0.0, sd.min(projects__projectDeliveryRate, projects__projects))
        projects__prospectingProjects.equation = sd.max(0.0, projects__projectProposalRate)
        projects__winningProjects.equation = sd.max(0.0, sd.min(sd.delay(self, projects__prospectingProjects, projects__projectAcquisitionDuration, 160.0), projects__proposals))
        revenue__collectingRevenue.equation = sd.max(0.0, sd.delay(self, revenue__makingRevenue, revenue__collectionTime, 2816.0))
        revenue__makingRevenue.equation = sd.max(0.0, revenue__revenue)
        staff__hiringStaff.equation = sd.max(0.0, ((((1.0 - kpi__steadyGrowthPolicyOn)) * staff__hiringRate) + (((kpi__steadyGrowthPolicyOn * staff__professionalStaff) * staff__steadyGrowthRate_) / 100.0)))
        staff__staffArriving.equation = sd.max(0.0, sd.delay(self, staff__hiringStaff, staff__hiringDuration, 0.0))

        # Converters
        cash__cashFlow.equation = (cash__cashIn - cash__cashOut)
        cash__collectingRevenue.equation = revenue__collectingRevenue
        cash__cost.equation = cost__cost
        cost__cost.equation = (cost__overheadCost + cost__staffCost)
        cost__staffCost.equation = (((cost__workplaceCost + cost__staffSalary)) * staff__professionalStaff)
        cost__staffSalary.equation = (80.0 / 12.0)
        kpi__acquisitionToDeliveryRatio_.equation = ((100.0 * projects__prospectingEffort) / ((projects__prospectingEffort + projects__projectVolume)))
        kpi__cashFlow.equation = cash__cashFlow
        kpi__cashFlowPerProfessional.equation = (cash__cashFlow / staff__professionalStaff)
        kpi__deliveringProjects.equation = projects__deliveringProjects
        kpi__maxiumProjectCapacity.equation = (((1.0 - (kpi__acquisitionToDeliveryRatio_ / 100.0))) * staff__professionalStaff)
        kpi__projectBacklog.equation = (projects__projects / kpi__maxiumProjectCapacity)
        kpi__projectVolume.equation = projects__projectVolume
        kpi__prospectingEffort.equation = projects__prospectingEffort
        kpi__targetBusinessDevelopmentAllocation_.equation = (((((1.0 - kpi__minimumBusDevAllocationOn)) * 100.0) * sd.max(((1.0 - (kpi__targetProjectStaff / staff__professionalStaff))), 0.0)) + (kpi__minimumBusDevAllocationOn * sd.max((100.0 * ((1.0 - (kpi__targetProjectStaff / staff__professionalStaff)))), kpi__acquisitionToDeliveryRatio_)))
        kpi__targetProjctDeliveryCapacity.equation = (projects__projects / kpi__targetBacklog)
        kpi__targetProjectStaff.equation = kpi__targetProjctDeliveryCapacity
        kpi__utilization_.equation = ((100.0 * projects__deliveringProjects) / kpi__maxiumProjectCapacity)
        projects__businessDevelopmentCapacity.equation = staff__businessDevelopmentCapacity
        projects__projectDeliveryCapacity.equation = staff__projectDeliveryCapacity
        projects__projectDeliveryRate.equation = staff__projectDeliveryCapacity
        projects__projectProposalRate.equation = (projects__projectVolume * ((staff__businessDevelopmentCapacity / projects__prospectingEffort)))
        revenue__deliveringProjects.equation = projects__deliveringProjects
        revenue__revenue.equation = (revenue__projectDeliveryFee * projects__deliveringProjects)
        staff__actualBusinessDevelopmentAllocation_.equation = ((kpi__steadyGrowthPolicyOn * kpi__targetBusinessDevelopmentAllocation_) + (((1.0 - kpi__steadyGrowthPolicyOn)) * staff__businessDevelopmentAllocation_))
        staff__businessDevelopmentAllocation_.equation = sd.lookup(sd.time(), 'staff.businessDevelopmentAllocation%')
        staff__businessDevelopmentCapacity.equation = ((staff__workCapacity * staff__actualBusinessDevelopmentAllocation_) / 100.0)
        staff__hiringRate.equation = sd.lookup(sd.time(), 'staff.hiringRate')
        staff__projectDeliveryCapacity.equation = ((staff__workCapacity * ((100.0 - staff__actualBusinessDevelopmentAllocation_))) / 100.0)
        staff__steadyGrowthPolicyOn1.equation = kpi__steadyGrowthPolicyOn
        staff__targetBusinessDevStaff_.equation = kpi__targetBusinessDevelopmentAllocation_
        staff__workCapacity.equation = (staff__professionalStaff * staff__workMonth)

        # Constants
        cash__easyTargetCash.equation = 30000.0
        cash__expertTargetCash.equation = 40000.0
        cash__minimumCash.equation = 23463.0
        cost__overheadCost.equation = 306.0
        cost__workplaceCost.equation = 1.0
        kpi__minimumBusDevAllocationOn.equation = 0.0
        kpi__steadyGrowthPolicyOn.equation = 0.0
        kpi__targetBacklog.equation = 2.0
        projects__projectAcquisitionDuration.equation = 6.0
        projects__projectVolume.equation = 16.0
        projects__prospectingEffort.equation = 4.0
        revenue__collectionTime.equation = 2.0
        revenue__projectDeliveryFee.equation = 17.6
        staff__hiringDuration.equation = 3.0
        staff__steadyGrowthRate_.equation = 1.0
        staff__workMonth.equation = 1.0


def simulation_model():
    return MakeYourPsfGrow()
