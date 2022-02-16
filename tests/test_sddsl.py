import os
import numpy as np
from BPTK_Py.sdcompiler.compile import compile_xmile

# def test_spm():
#     from BPTK_Py import Model
#     from BPTK_Py import sd_functions as sd
#     model = Model(starttime=0.0, stoptime=120.0, dt=1.0, name='SimpleProjectManagement')

#     openTasks = model.stock("openTasks")
#     closedTasks = model.stock("closedTasks")
#     staff = model.stock("staff")
#     completionRate = model.flow("completionRate")
#     currentTime = model.converter("currentTime")
#     remainingTime = model.converter("remainingTime")
#     schedulePressure = model.converter("schedulePressure")
#     productivity = model.converter("productivity")
#     deadline = model.constant("deadline")
#     effortPerTask = model.constant("effortPerTask")
#     initialStaff = model.constant("initialStaff")
#     initialOpenTasks = model.constant("initialOpenTasks")

#     closedTasks.initial_value = 0.0
#     staff.initial_value = initialStaff
#     openTasks.initial_value = initialOpenTasks
#     deadline.equation = 100.0
#     effortPerTask.equation = 1.0
#     initialStaff.equation = 1.0
#     initialOpenTasks.equation = 100.0

#     currentTime.equation = sd.time()
#     remainingTime.equation = deadline - currentTime
#     openTasks.equation = -completionRate
#     closedTasks.equation = completionRate

#     schedulePressure.equation = sd.min((openTasks * effortPerTask) / (staff * sd.max(remainingTime, 1)), 2.5)

#     model.points["productivity"] = [
#         [0, 0.4],
#         [0.25, 0.444],
#         [0.5, 0.506],
#         [0.75, 0.594],
#         [1, 1],
#         [1.25, 1.119],
#         [1.5, 1.1625],
#         [1.75, 1.2125],
#         [2, 1.2375],
#         [2.25, 1.245],
#         [2.5, 1.25]
#     ]

#     productivity.equation = sd.lookup(schedulePressure, "productivity")
#     completionRate.equation = sd.max(0.0, sd.min(openTasks, staff * (productivity / effortPerTask)))

#     x = model.converter("x")

#     # !=
#     x.equation = sd.If(productivity != 1.0, 1, 0)

#     for i in range(0,120+1):
#         result = x(i)
#         if i < 100:
#             assert result == 0
#         else:
#             assert result == 1

#     # ==
#     x.equation = sd.If(productivity == 1.0, 1, 0)

#     for i in range(0,120+1):
#         result = x(i)
#         if i < 100:
#             assert result == 1
#         else:
#             assert result == 0

#     ## >
#     x.equation = sd.If(productivity > 1.0, 1, 0)

#     for i in range(0,120+1):
#         result = x(i)
#         assert result == 0

#     ## <
#     x.equation = sd.If(productivity < 1.0, 1, 0)

#     for i in range(0,120+1):
#         result = x(i)
#         if i < 100:
#             assert result == 0
#         else:
#             assert result == 1

#     # <=
#     x.equation = sd.If(productivity <= 1.0, 1, 0)

#     for i in range(0,120+1):
#         result = x(i)

#         assert result == 1

#     # >=
#     x.equation = sd.If(productivity >= 1.0, 1, 0)

#     for i in range(0,120+1):
#         result = x(i)

#         if i < 100:
#             assert result == 1
#         else:
#             assert result == 0



# def test_delay():
#     from BPTK_Py import Model
#     from BPTK_Py import sd_functions

#     model = Model(starttime=1, stoptime=100, dt=1, name='test')

#     a = model.converter('a')
#     b = model.converter('b')

#     a.equation = 0
#     b.equation = 100.0 + (sd_functions.delay(model, a, 20.0, 10.0))

#     df = b.plot(return_df=True)

#     assert (df[0:20] == 110.0).all()["b"]
#     assert (df[21:] == 100).all()["b"]

#     model = Model(starttime=1, stoptime=100, dt=0.25, name='test')

#     a = model.converter('a')
#     b = model.converter('b')

#     a.equation = 0
#     b.equation = 100.0 + (sd_functions.delay(model, a, 20.0, 10.0))

#     df = b.plot(return_df=True)

#     assert (df[0:20] == 110.0).all()["b"]
#     assert (df[22:] == 100).all()["b"]

# def test_equations():
#     from BPTK_Py import Model

#     from BPTK_Py.bptk import bptk

#     bptk = bptk()

#     model = Model(starttime=1, stoptime=1, dt=1, name='test')

#     a = model.converter('a')

#     b = model.converter('b')

#     c = model.converter('c')

#     a.equation = 0.1

#     b.equation = 1 - a
#     assert b(1) == 0.9

#     b.equation = 1 + a
#     assert b(1) == 1.1

#     b.equation = 1 * a
#     assert b(1) == 0.1

#     b.equation = 1 / a
#     assert b(1) == 10

#     c.equation = a*b
#     assert c(1) == 1.0

#     a.equation = 3.0
#     b.equation = 5.0 - a
#     c.equation = a**b
#     assert c(1)==9.0

def test_sddsl_functions():
    from BPTK_Py import Model
    from BPTK_Py import sd_functions as sd
    from BPTK_Py.bptk import bptk
    import math
    bptk=bptk()

    # #abs
    # start = 0.0
    # dt = 0.1
    # stop = 10.0
    # model = Model(starttime=start,stoptime=stop,dt=dt,name='abs')
    # input_converter = model.converter("input_converter")
    # input_converter.equation=sd.time()-5
    # abs_converter = model.converter("abs_converter")
    # abs_converter.equation = sd.abs(input_converter)
    # bptk.register_model(model)
    # data = bptk.run_scenarios(scenario_managers=["smAbs"],scenarios=["base"],equations=["input_converter","abs_converter"])

    # for i in np.arange(start, stop, dt):
    #     assert abs(data.input_converter[i]) == data.abs_converter[i]


    # delay
    # only works properly with integer values or a model dt of 1.0. Is this intended? Looks weird for example for dt = .9
    # start = 0.0
    # dt = 0.1
    # stop = 10.0
    # model = Model(starttime=start,stoptime=stop,dt=dt,name='delay')
    # input_function = model.converter("input_function")
    # input_function.equation=sd.time()
    # delayed_input = model.converter("delayed_input")

    # delay_duration = 0.0
    # initial_value = 0.0

    # delayed_input.equation = sd.delay(model,input_function, delay_duration, initial_value)
    # bptk.register_model(model)
    # data = bptk.run_scenarios(scenario_managers=["smDelay"],scenarios=["base"],equations=["input_function","delayed_input"])
    # print(data)
    # for i in np.arange(start, stop, dt):
    #     if(i < delay_duration + 1):
    #         assert data.delayed_input[i] == initial_value
    #         continue

    #     # round to avoid floating point inprecision when indexing array
    #     input_function_index = math.floor(i - delay_duration)
    #     assert data.delayed_input[i] == data.input_function[input_function_index]


    # # dt
    # start = 5.0
    # dt = 0.25
    # stop = 12.0
    # model = Model(starttime=start,stoptime=stop,dt=dt,name='dt')
    # dt_converter = model.converter("dt")
    # dt_converter.equation = sd.dt(model)
    # data = dt_converter.plot(return_df = True)
    # for i in np.arange(start, stop, dt):
    #     assert data.dt[i] == dt


    # # exp
    # start = 0
    # dt = 0.1
    # stop = 10
    # model = Model(starttime=start,stoptime=stop,dt=dt,name='exp')
    # exp_value = np.log(1)
    # growth_rate = model.constant("growth_rate")
    # growth_rate.equation = exp_value
    # exp = model.converter("exp")
    # exp.equation = sd.exp(growth_rate*sd.time())
    # data = exp.plot(return_df=True)
    # for i in np.arange(start, stop, dt):
    #     assert data.exp[i] == math.exp(exp_value * i)


    # # max
    # start = 0
    # dt = 1
    # stop = 10
    # model = Model(starttime=start,stoptime=stop,dt=dt,name='max')
    # a = model.converter("a")
    # a.equation = 5.0+sd.step(15, 5)
    # b = model.converter("b")
    # b.equation = 10-sd.step(2, 5)

    # c = model.converter("c")
    # c.equation=sd.max(a,b)
    # bptk.register_model(model)

    # data = bptk.plot_scenarios(scenario_managers=["smMax"],scenarios=["base"],equations=["a","b","c"], return_df=True)
    # for i in np.arange(start, stop, dt):
    #     if i <= 5:
    #         assert data.c[i] == 10
    #         continue
    #     assert data.c[i] == 20

        
    # # min
    # start = 0
    # dt = 1
    # stop = 10
    # model = Model(starttime=start,stoptime=stop,dt=dt,name='min')
    # a = model.converter("a")
    # a.equation = 5.0+sd.step(15, 5)
    # b = model.converter("b")
    # b.equation = 10-sd.step(2, 5)

    # c = model.converter("c")
    # c.equation=sd.min(a,b)
    # bptk.register_model(model)

    # data = bptk.plot_scenarios(scenario_managers=["smMin"],scenarios=["base"],equations=["a","b","c"],return_df=True)
    # for i in np.arange(start, stop, dt):
    #     if i <= 5:
    #         assert data.c[i] == 5
    #         continue
    #     assert data.c[i] == 8


    # # pulse
    # # dt has to be 1/(2^n) or the pulse function does not properly work.
    # # the first pulse is 1-interval. Is that intended?
    # # first pulse attribute only works when first_pulse < interval. Intended?
    # start = 0
    # dt = 2
    # stop = 10
    # model = Model(starttime=start,stoptime=stop,dt=dt,name='pulse')
    # stock = model.stock("stock")
    # stock.initial_value=0.0
    # flow = model.flow("flow")
    # volume = 10.0
    # first_pulse = 2.0
    # interval = 3.0
    # flow.equation=sd.pulse(model,10.0,first_pulse,interval)
    # stock.equation = flow
    # bptk.register_model(model)
    # data = bptk.plot_scenarios(scenario_managers=["smPulse"],scenarios=["base"],equations=["stock","flow"],return_df=True)
    # for i in np.arange(start, stop, dt):
    #     if i < first_pulse:
    #         assert data.flow[i] == 0
    #         assert data.stock[i] == 0
    #         continue
    #     if i == first_pulse:
    #         assert data.flow[i] == volume * (1 / dt)
    #         assert data.stock[i] == 0
    #         continue

    #     if i % interval == first_pulse:
    #         assert data.flow[i] == volume * (1 / dt)
    #     assert data.stock[i] == volume * (math.ceil((i - first_pulse) / interval))


    # # smooth
    # # does not test for exact values
    # # Only tests if the values continously increase, while the rate of change drops and absolute values stays below the max value (which implies some smoothing function)
    # start = 1.0
    # dt = 0.1
    # stop = 10.0
    # model = Model(starttime=start,stoptime=stop,dt=dt,name='smooth')
    
    # step_start = 3.0
    # step_height = 10.0
    # input_function = model.converter("input_function")
    # input_function.equation=sd.step(step_height,step_start)

    # base_value = 9.0
    # smooth = model.converter("smooth")
    # smooth.equation=sd.smooth(model, input_function,1.0,base_value)

    # bptk.register_model(model)
    # data = bptk.run_scenarios(scenario_managers=["smSmooth"],scenarios=["base"],equations=["input_function","smooth"])
    # last_value = base_value
    # last_change = 9999999
    # reached_step_height = False
    # for i in np.arange(start, stop, dt):

    #     # smoothing function never exceeds height
    #     assert data.smooth[i] <= step_height

    #     # no further testing if necessary if height got reached
    #     if data.smooth[i] == step_height:
    #         reached_step_height = True
    #         continue
    #     else: 
    #         # ensure the smoothing function never drops below step height once reached
    #         assert reached_step_height == False

    #     # before the smooth function reacts to the change in step height it should be equal to the initial value.
    #     if i <= step_start + dt:
    #         assert data.smooth[i] == base_value
    #         continue

    #     # the value of the function should always increase
    #     assert data.smooth[i] > last_value

    #     # calculate the rate of change and ensure it is lower than in previous runs.
    #     new_change = data.smooth[i] - last_value
    #     assert new_change < last_change

    #     last_value = data.smooth[i]
    #     last_change = new_change


    # # starttime
    # start = 5
    # dt = 0.25
    # stop = 10
    # model = Model(starttime=start,stoptime=stop,dt=dt,name='starttime')
    # starttime = model.converter("starttime")
    # starttime.equation = sd.starttime(model)
    # data = starttime.plot(return_df=True)
    # for i in np.arange(start, stop, dt):
    #     assert data.starttime[i] == start


    # # stoptime
    # start = 5
    # dt = 0.25
    # stop = 10
    # model = Model(starttime=start,stoptime=stop,dt=dt,name='stoptime')
    # stoptime = model.converter("stoptime")
    # stoptime.equation = sd.stoptime(model)
    # data = stoptime.plot(return_df=True)
    # for i in np.arange(start, stop, dt):
    #     assert data.stoptime[i] == stop


    # # step
    # start = 1
    # dt = 1
    # stop = 10
    # model = Model(starttime=1,stoptime=10,dt=1,name='step')
    # step = model.converter("step")
    # step_timestep = 5.0
    # step_height = 10.0
    # step.equation=sd.step(10.0,5.0)
    # data = step.plot(return_df=True)
    # for i in np.arange(start, stop, dt):
    #     if i <= step_timestep:
    #         assert data.step[i] == 0
    #         continue

    #     assert data.step[i] == step_height


    # # time
    # start = 0
    # dt = 1
    # stop = 10
    # model = Model(starttime=start,stoptime=stop,dt=dt,name='time')
    # stock = model.stock("stock")
    # stock.initial_value=0.0
    # inflow = model.flow("inflow")
    # inflow.equation = sd.time()
    # stock.equation = inflow
    # data = inflow.plot(return_df=True)
    # for i in np.arange(start, stop, dt):
    #     assert data.inflow[i] == i


    # # trend
    # # To Do


    # # round
    # start = 0
    # dt = 0.1
    # stop = 10
    # model = Model(starttime=start,stoptime=stop,dt=dt,name='round')
    # flow = model.flow("round")
    # flow.equation = sd.round( sd.time(), 0 )
    # data = flow.plot(return_df=True)
    # for i in np.arange(start, stop, dt):
    #     assert data['round'][i] == round(i)


    # # sqrt
    # start = 0
    # dt = 1
    # stop = 10
    # m = Model(starttime=start,stoptime=stop,dt=dt)
    # f = m.flow(name="sqrt")

    # val = sd.time() 

    # f.equation = sd.sqrt(val)
    # data = f.plot(return_df=True)
    # for i in np.arange(start, stop, dt):
    #     assert data.sqrt[i] == math.sqrt(i)


    # # sin cos tan
    # start = 0
    # dt = 0.1
    # stop = 10
    # m = Model(starttime=start,stoptime=stop,dt=dt)
    # sin = m.flow(name="sin")
    # tan = m.flow(name="tan")
    # cos = m.flow(name="cos")
    # x = sd.time() 

    # sin.equation = sd.sin(x)
    # tan.equation = sd.tan(x)
    # cos.equation = sd.cos(x)

    # data_sin = sin.plot(return_df=True)
    # data_tan = tan.plot(return_df=True)
    # data_cos = cos.plot(return_df=True)
    # for i in np.arange(start, stop, dt):
    #     print(str(i) + "   " + str(math.tan(i)) + "     " + str(data_tan.tan[i]))
    #     assert data_sin.sin[i] == max(math.sin(i), 0.0)
    #     assert data_cos.cos[i] == max(math.cos(i), 0.0)
    #     assert data_tan.tan[i] == max(math.tan(i), 0.0)


    # combinations
    # only works for r < 5? 
    # start = 3
    # dt = 1
    # stop = 10
    # m = Model(starttime=start,stoptime=stop,dt=dt)
    # f = m.flow(name="combinations")
    # n = 3
    # r = 5
    # f.equation = sd.combinations(n,r)
    # data = f.plot(return_df=True)
    

    # # factorial
    # start = 0
    # dt = 1
    # stop = 10
    # m = Model(starttime=start,stoptime=stop,dt=dt)
    # f = m.flow(name="factorial")

    # n = 5

    # f.equation = sd.factorial(sd.time())
    # data = f.plot(return_df=True)
    # for i in np.arange(start, stop, dt):
    #     assert data.factorial[i] == math.factorial(i)


    # # gammaln
    # # Only tests if it runs
    # m = Model(starttime=0,stoptime=10,dt=0.1)
    # f = m.flow(name="gammaln")

    # n = sd.time()
    # f.equation = sd.gammaln(n)
    # data = f.plot(return_df=True)
    # assert len(data) == 101


    # # invnorm
    # # Only tests if it runs
    # m = Model(starttime=-0.5,stoptime=1,dt=0.1)
    # f = m.flow(name="invnorm")

    # p = sd.time()

    # f.equation = sd.invnorm(p)
    # data = f.plot(return_df=True)
    # assert len(data) == 16


    # # montecarlo
    # # Only tests if it runs
    # m = Model(starttime=0,stoptime=10,dt=0.1)
    # f = m.flow(name="montecarlo")

    # probability = 50
    # f.equation = sd.montecarlo(probability)
    # data = f.plot(return_df=True)

    # assert len(data) == 101


    # # normalcdf
    # m = Model(starttime=-4,stoptime=4,dt=0.1)
    # f = m.flow(name="normalCDF")
    # left = -4
    # right = sd.time()
    # mean = 0
    # stddev = 1
    # f.equation = sd.normalcdf(left, right, mean, stddev)
    # data = f.plot(return_df=True)
    # assert len(data) == 81


    # permutations
    # only working for some values. For example not for 3 and 4
    # m = Model(starttime=2,stoptime=10,dt=0.1)
    # f = m.flow(name="permutations")
    # n = 3
    # r = 4

    # f.equation = sd.permutations(n, r)
    # data = f.plot(return_df=True)
    

    # # random
    # start = .2
    # dt = .1
    # stop = 30
    # m = Model(starttime=start,stoptime=stop,dt=dt)
    # f = m.flow(name="random")
    # min_value = 0.1
    # max_value = sd.time()

    # f.equation = sd.random(min_value, max_value)
    # data = f.plot(return_df=True)
    # for i in np.arange(start, stop, dt):
    #     assert data.random[i] >= min_value and data.random[i] <= i