import os
import numpy as np
from BPTK_Py.sdcompiler.compile import compile_xmile
from BPTK_Py.sddsl.operators import BinaryOperator

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

#     a.equation = sd_functions.time()
#     b.equation = sd_functions.delay(model, a, 20.0, 10.0)

#     df_b = b.plot(return_df=True)

#     for index  in range(1,100):
#         if index<=20:
#             assert(df_b["b"][index]==10)
#         else:
#             assert(df_b["b"][index]==index-20)


#     model = Model(starttime=1, stoptime=10, dt=0.25, name='test')

#     a = model.converter('a')
#     b = model.converter('b')

#     a.equation = sd_functions.time()
#     b.equation = sd_functions.delay(model, a, 3.0, 0.0)

#     df_b = b.plot(return_df=True)

#     for index  in range(1,10):
#         if index<=3:
#             assert(df_b["b"][index]==0)
#         else:
#             assert(df_b["b"][index]==index-3)


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

# def test_sddsl_functions():
#     from BPTK_Py import Model
#     from BPTK_Py import sd_functions as sd
#     from BPTK_Py.bptk import bptk
#     import math
#     bptk=bptk()

#     # abs
#     start = 0.0
#     dt = 0.1
#     stop = 10.0
#     model = Model(starttime=start,stoptime=stop,dt=dt,name='abs')

#     input_converter = model.converter("input_converter")
#     input_converter.equation=sd.time()-5
#     abs_converter = model.converter("abs_converter")
#     abs_converter.equation = sd.abs(input_converter)
#     bptk.register_model(model)
#     data = bptk.run_scenarios(scenario_managers=["smAbs"],scenarios=["base"],equations=["input_converter","abs_converter"])

#     for i in np.arange(start, stop, dt):
#         assert abs(data.input_converter[i]) == data.abs_converter[i]


#     # delay
#     start = 0.0
#     dt = 0.5
#     stop = 10.0
#     model = Model(starttime=start,stoptime=stop,dt=dt,name='delay')

#     input_function = model.converter("input_function")
#     input_function.equation=sd.time()
#     delayed_input = model.converter("delayed_input")

#     delay_duration = 1.0
#     initial_value = 0.0
#     delayed_input.equation = sd.delay(model,input_function, delay_duration, initial_value)

#     bptk.register_model(model)
#     data = bptk.run_scenarios(scenario_managers=["smDelay"],scenarios=["base"],equations=["input_function","delayed_input"])
#     for i in np.arange(start, stop, dt):
#         if(i < delay_duration + dt):
#             assert data.delayed_input[i] == initial_value
#             continue

#         input_function_index = i - delay_duration
#         assert data.delayed_input[i] == data.input_function[input_function_index]

#     # dt
#     start = 5.0
#     dt = 0.25
#     stop = 12.0

#     model = Model(starttime=start,stoptime=stop,dt=dt,name='dt')
#     dt_converter = model.converter("dt")
#     dt_converter.equation = sd.dt(model)
#     data = dt_converter.plot(return_df = True)

#     for i in np.arange(start, stop, dt):
#         assert data.dt[i] == dt


#     # exp
#     start = 0
#     dt = 0.1
#     stop = 10
#     model = Model(starttime=start,stoptime=stop,dt=dt,name='exp')

#     exp_value = np.log(1)
#     growth_rate = model.constant("growth_rate")
#     growth_rate.equation = exp_value
#     exp = model.converter("exp")
#     exp.equation = sd.exp(growth_rate*sd.time())
#     data = exp.plot(return_df=True)

#     for i in np.arange(start, stop, dt):
#         assert data.exp[i] == math.exp(exp_value * i)


#     # max
#     start = 0
#     dt = 1
#     stop = 10
#     model = Model(starttime=start,stoptime=stop,dt=dt,name='max')
    
#     a = model.converter("a")
#     a.equation = 5.0+sd.step(15, 5)
#     b = model.converter("b")
#     b.equation = 10-sd.step(2, 5)
#     c = model.converter("c")
#     c.equation=sd.max(a,b)
#     bptk.register_model(model)

#     data = bptk.plot_scenarios(scenario_managers=["smMax"],scenarios=["base"],equations=["a","b","c"], return_df=True)

#     for i in np.arange(start, stop, dt):
#         if i <= 5:
#             assert data.c[i] == 10
#             continue
#         assert data.c[i] == 20

        
#     # min
#     start = 0
#     dt = 1
#     stop = 10
#     model = Model(starttime=start,stoptime=stop,dt=dt,name='min')

#     a = model.converter("a")
#     a.equation = 5.0+sd.step(15, 5)
#     b = model.converter("b")
#     b.equation = 10-sd.step(2, 5)
#     c = model.converter("c")
#     c.equation=sd.min(a,b)
#     bptk.register_model(model)

#     data = bptk.plot_scenarios(scenario_managers=["smMin"],scenarios=["base"],equations=["a","b","c"],return_df=True)

#     for i in np.arange(start, stop, dt):
#         if i <= 5:
#             assert data.c[i] == 5
#             continue
#         assert data.c[i] == 8


#     # pulse
#     # dt has to be 1/(2^n) or the pulse function does not properly work.
#     # the first pulse is 1-interval. Is that intended?
#     # first pulse attribute only works when first_pulse < interval. Intended?
#     start = 0
#     dt = .5
#     stop = 9
#     model = Model(starttime=start,stoptime=stop,dt=dt,name='pulse')
#     stock = model.stock("stock")
#     stock.initial_value=0.0
#     flow = model.flow("flow")
#     volume = 9.0
#     first_pulse = 1.5
#     interval = 3.0
#     flow.equation=sd.pulse(model,volume,first_pulse,interval)
#     stock.equation = flow
#     bptk.register_model(model)
#     data = bptk.plot_scenarios(scenario_managers=["smPulse"],scenarios=["base"],equations=["stock","flow"],return_df=True)
#     for i in np.arange(start, stop, dt):
#         if i < first_pulse:
#             assert data.flow[i] == 0
#             assert data.stock[i] == 0
#             continue
#         if i == first_pulse:
#             assert data.flow[i] == volume * (1 / dt)
#             assert data.stock[i] == 0
#             continue

#         if i % interval == first_pulse:
#             assert data.flow[i] == volume * (1 / dt)
#         assert data.stock[i] == volume * (math.ceil((i - first_pulse) / interval))


#     # smooth
#     # does not test for exact values
#     # only tests if the values continously increase, while the rate of change drops and absolute values stays below the max value (which implies some smoothing function)
#     start = 1.0
#     dt = 0.1
#     stop = 10.0
#     model = Model(starttime=start,stoptime=stop,dt=dt,name='smooth')
    
#     step_start = 3.0
#     step_height = 10.0
#     input_function = model.converter("input_function")
#     input_function.equation=sd.step(step_height,step_start)

#     base_value = 9.0
#     smooth = model.converter("smooth")
#     smooth.equation=sd.smooth(model, input_function,1.0,base_value)

#     bptk.register_model(model)
#     data = bptk.run_scenarios(scenario_managers=["smSmooth"],scenarios=["base"],equations=["input_function","smooth"])
#     last_value = base_value
#     last_change = 9999999
#     reached_step_height = False
#     for i in np.arange(start, stop, dt):

#         # smoothing function never exceeds height
#         assert data.smooth[i] <= step_height

#         # no further testing if necessary if height got reached
#         if data.smooth[i] == step_height:
#             reached_step_height = True
#             continue
#         else: 
#             # ensure the smoothing function never drops below step height once reached
#             assert reached_step_height == False

#         # before the smooth function reacts to the change in step height it should be equal to the initial value.
#         if i <= step_start + dt:
#             assert data.smooth[i] == base_value
#             continue

#         # the value of the function should always increase
#         assert data.smooth[i] > last_value

#         # calculate the rate of change and ensure it is lower than in previous runs.
#         new_change = data.smooth[i] - last_value
#         assert new_change < last_change

#         last_value = data.smooth[i]
#         last_change = new_change


#     # starttime
#     start = 5
#     dt = 0.25
#     stop = 10
#     model = Model(starttime=start,stoptime=stop,dt=dt,name='starttime')

#     starttime = model.converter("starttime")
#     starttime.equation = sd.starttime(model)
#     data = starttime.plot(return_df=True)

#     for i in np.arange(start, stop, dt):
#         assert data.starttime[i] == start


#     # stoptime
#     start = 5
#     dt = 0.25
#     stop = 10

#     model = Model(starttime=start,stoptime=stop,dt=dt,name='stoptime')
#     stoptime = model.converter("stoptime")
#     stoptime.equation = sd.stoptime(model)
#     data = stoptime.plot(return_df=True)

#     for i in np.arange(start, stop, dt):
#         assert data.stoptime[i] == stop


#     # step
#     start = 1
#     dt = 1
#     stop = 10
#     model = Model(starttime=1,stoptime=10,dt=1,name='step')
    
#     step_timestep = 5.0
#     step_height = 10.0
#     step = model.converter("step")
#     step.equation=sd.step(step_height,step_timestep)
#     data = step.plot(return_df=True)

#     for i in np.arange(start, stop, dt):
#         if i <= step_timestep:
#             assert data.step[i] == 0
#             continue
#         assert data.step[i] == step_height


#     # time
#     start = 0
#     dt = 1
#     stop = 10
#     model = Model(starttime=start,stoptime=stop,dt=dt,name='time')
    
#     stock = model.stock("stock")
#     stock.initial_value=0.0
#     inflow = model.flow("inflow")
#     inflow.equation = sd.time()
#     stock.equation = inflow

#     data = inflow.plot(return_df=True)

#     for i in np.arange(start, stop, dt):
#         assert data.inflow[i] == i


#     # trend
#     # ToDo


#     # round
#     start = 0
#     dt = 0.1
#     stop = 10
#     model = Model(starttime=start,stoptime=stop,dt=dt,name='round')
#     flow = model.flow("round")
#     flow.equation = sd.round( sd.time(), 0 )
#     data = flow.plot(return_df=True)
#     for i in np.arange(start, stop, dt):
#         assert data['round'][i] == round(i)


#     # sqrt
#     start = 0
#     dt = 1
#     stop = 10
#     m = Model(starttime=start,stoptime=stop,dt=dt)
#     f = m.flow(name="sqrt")

#     val = sd.time() 

#     f.equation = sd.sqrt(val)
#     data = f.plot(return_df=True)
#     for i in np.arange(start, stop, dt):
#         assert data.sqrt[i] == math.sqrt(i)


#     # sin cos tan
#     start = 0
#     dt = 0.1
#     stop = 10
#     m = Model(starttime=start,stoptime=stop,dt=dt)
#     sin = m.flow(name="sin")
#     tan = m.flow(name="tan")
#     cos = m.flow(name="cos")
#     x = sd.time() 

#     sin.equation = sd.sin(x)
#     tan.equation = sd.tan(x)
#     cos.equation = sd.cos(x)

#     data_sin = sin.plot(return_df=True)
#     data_tan = tan.plot(return_df=True)
#     data_cos = cos.plot(return_df=True)
#     for i in np.arange(start, stop, dt):
#         assert data_sin.sin[i] == max(math.sin(i), 0.0)
#         assert data_cos.cos[i] == max(math.cos(i), 0.0)
#         assert data_tan.tan[i] == max(math.tan(i), 0.0)

#     # beta
#     # only tests if it runs
#     m = Model(starttime=0,stoptime=10,dt=0.1)
#     f = m.flow(name="beta")
#     alpha = 1
#     beta = 2
#     f.equation = sd.beta(alpha, beta)
#     data = f.plot(return_df=True)
#     assert len(data) == 101

#     # binomial
#     # only tests if it runs
#     m = Model(starttime=0,stoptime=10,dt=0.1)
#     f = m.flow(name="binomial")
#     n = 100
#     p = 0.1
#     f.equation = sd.binomial(n, p)
#     data = f.plot(return_df=True)
#     assert len(data) == 101


#     # combinations
#     # only works for r < 5? 
#     start = 3
#     dt = 1
#     stop = 10
#     m = Model(starttime=start,stoptime=stop,dt=dt)
#     f = m.flow(name="combinations")
#     n = 7
#     r = 5
#     f.equation = sd.combinations(n,r)
#     data = f.plot(return_df=True)
#     for i in np.arange(start, stop, dt):
#         assert data.combinations[i] == 21

#     # exprnd
#     # only tests if it runs
#     m = Model(starttime=0,stoptime=10,dt=0.1)
#     f = m.flow(name="exprnd")
#     mean = sd.time()
#     f.equation = sd.exprnd(mean)
#     data = f.plot(return_df=True)
#     assert len(data) == 101


#     # factorial
#     start = 0
#     dt = 1
#     stop = 10
#     m = Model(starttime=start,stoptime=stop,dt=dt)
#     f = m.flow(name="factorial")

#     n = 5

#     f.equation = sd.factorial(sd.time())
#     data = f.plot(return_df=True)
#     for i in np.arange(start, stop, dt):
#         assert data.factorial[i] == math.factorial(i)

#     # gamma
#     # only tests if it runs
#     m = Model(starttime=0,stoptime=10,dt=0.1)
#     f = m.flow(name="gamma")

#     shape = 10
#     scale = sd.time()

#     f.equation = sd.gamma(shape, scale)
#     data = f.plot(return_df=True)
#     assert len(data) == 101


#     # gammaln
#     # only tests if it runs
#     m = Model(starttime=0,stoptime=10,dt=0.1)
#     f = m.flow(name="gammaln")

#     n = sd.time()
#     f.equation = sd.gammaln(n)
#     data = f.plot(return_df=True)
#     assert len(data) == 101


#     # geometric
#     # only tests if it runs
#     m = Model(starttime=0,stoptime=10,dt=0.1)
#     f = m.flow(name="geometric")

#     p = 0.1

#     f.equation = sd.geometric(p)
#     data = f.plot(return_df=True)
#     assert len(data) == 101


#     # invnorm
#     # only tests if it runs
#     m = Model(starttime=-0.5,stoptime=1,dt=0.1)
#     f = m.flow(name="invnorm")

#     p = sd.time()

#     f.equation = sd.invnorm(p)
#     data = f.plot(return_df=True)
#     assert len(data) == 16


#     # logistic
#     # only tests if it runs
#     m = Model(starttime=-1,stoptime=10,dt=0.1)
#     f = m.flow(name="logistic")

#     mean = 0
#     scale = 1

#     f.equation = sd.logistic(mean, scale)
#     data = f.plot(return_df=True)
#     assert len(data) == 111


#     # lognormal
#     # only tests if it runs
#     m = Model(starttime=0,stoptime=10,dt=0.1)
#     f = m.flow(name="lognormal")

#     mean = 0
#     stdev = 1
#     f.equation = sd.lognormal(mean, stdev)
#     data = f.plot(return_df=True)
#     assert len(data) == 101


#     # montecarlo
#     # only tests if it runs
#     m = Model(starttime=0,stoptime=10,dt=0.1)
#     f = m.flow(name="montecarlo")

#     probability = 50
#     f.equation = sd.montecarlo(probability)
#     data = f.plot(return_df=True)

#     assert len(data) == 101


#     # normal
#     # only tests if it runs
#     m = Model(starttime=0,stoptime=10,dt=1)
#     f = m.flow(name="normal")

#     mean = 0
#     stdev = 1
#     f.equation = sd.normal(mean, stdev)
#     data = f.plot(return_df=True)
#     assert len(data) == 11


#     # normalcdf
#     # only tests if it runs
#     m = Model(starttime=-4,stoptime=4,dt=0.1)
#     f = m.flow(name="normalCDF")
#     left = -4
#     right = sd.time()
#     mean = 0
#     stddev = 1
#     f.equation = sd.normalcdf(left, right, mean, stddev)
#     data = f.plot(return_df=True)
#     assert len(data) == 81


#     # paetro
#     # only tests if it runs
#     m = Model(starttime=1,stoptime=10,dt=0.1)
#     f = m.flow(name="pareto")
#     shape = 1
#     scale = 1

#     f.equation = sd.pareto(shape, scale)
#     data = f.plot(return_df=True)
#     assert len(data) == 91


#     # permutations
#     start = 4
#     stop = 10
#     dt = 1
#     m = Model(starttime=start,stoptime=stop,dt=dt)
#     f = m.flow(name="permutations")
#     n = sd.time()
#     r = 2

#     f.equation = sd.permutations(n, r)
#     data = f.plot(return_df=True)
    
#     for i in np.arange(start, stop, dt):
#         assert (math.factorial(i) / math.factorial(i - r))

#     # poisson
#     # only tests if it runs
#     m = Model(starttime=1,stoptime=10,dt=0.1)
#     f = m.flow(name="poisson")
#     mu = sd.time()

#     f.equation = sd.poisson(mu)
#     data = f.plot(return_df=True)
#     assert len(data) == 91


#     # random
#     start = .2
#     dt = .1
#     stop = 30
#     m = Model(starttime=start,stoptime=stop,dt=dt)
#     f = m.flow(name="random")
#     min_value = 0.1
#     max_value = sd.time()

#     f.equation = sd.random(min_value, max_value)
#     data = f.plot(return_df=True)
#     for i in np.arange(start, stop, dt):
#         assert data.random[i] >= min_value and data.random[i] <= i

#     # triangular
#     # only tests if it runs
#     m = Model(starttime=1,stoptime=10,dt=0.1)
#     f = m.flow(name="triangular")
#     lower_bound = 0
#     mode = 1
#     upper_bound = sd.time()

#     f.equation = sd.triangular(lower_bound, mode, upper_bound)
#     data = f.plot(return_df=True)
#     assert len(data) == 91

#     # weibull
#     # only tests if it runs
#     m = Model(starttime=1,stoptime=10,dt=0.1)
#     f = m.flow(name="weibull")
#     shape = 1
#     scale = sd.time()

#     f.equation = sd.weibull(shape, scale)
#     data = f.plot(return_df=True)
#     assert len(data) == 91















    

def test_array_functions():
    from BPTK_Py import Model
    from BPTK_Py import sd_functions as sd
    from BPTK_Py.bptk import bptk
    import math
    bptk=bptk()

    # # setup functions
    # for i in range(1, 10):
    #     model = Model(starttime=0.0,stoptime=2.0,dt=1.0,name='setup_func_vec_' + str(i))

    #     test_converter = model.converter("test_converter")
    #     test_converter.setup_vector(i, i)

    #     assert(test_converter._elements.vector_size() == i)
    #     dim = test_converter._elements.matrix_size()
    #     assert(dim == [i, 0])
    #     for x in range(0, i):
    #         assert(test_converter[x].equation == i)

    #     for j in range(1, 10):
    #         test_converter = model.converter("test_converter_matrix_" + str(j))
    #         test_converter.setup_matrix([i, j], i + j)
    #         dim = test_converter._elements.matrix_size()
    #         assert(dim[0] == i)
    #         assert(dim[1] == j)
    #         for x in range(0, i):
    #             for y in range(0, j):
    #                 assert(test_converter[x][y].equation == i + j)


    # multiplication
    
    model = Model(starttime=0.0,stoptime=2.0,dt=1.0,name='setup_func_vec_' + str(4))

    test_converter = model.converter("test_converter")
    test_converter.setup_vector(3, 4.0)
    test_converter[1] = 5.0
    test_converter[2] = 6.0

    test_converter2 = model.converter("test_converter2")
    test_converter2.setup_vector(3, 5.0)
    # test_converter2[1] = 6.0
    # test_converter2[2] = 7.0

    test_mul_converter = model.converter("test_mul_converter")
    test_mul_converter.equation = test_converter * 2.0 + 3.0 + 4.0

    data = test_mul_converter[0].plot(return_df=True)
    print(data)
    data = test_mul_converter[1].plot(return_df=True)
    print(data)
    data = test_mul_converter[2].plot(return_df=True)
    print(data)
    # test_eq = test_converter2 + 2.5
    # print(test_converter._elements.matrix_size())
    # print(test_eq.resolve_dimensions())
    # def print_eq(eq, offset):
    #     if isinstance(eq, BinaryOperator):
    #         print(offset + str(type(eq)))
    #         print(offset + str(eq.resolve_dimensions()))
    #         print(offset + str(eq.is_any_subelement_arrayed()))
    #         print()
    #         print_eq(eq.element_1, offset + "  ")
    #         print_eq(eq.element_2, offset + "  ")
    #     else:
    #         print(offset + str(type(eq)))
    # print_eq(test_eq, "")

    # def resolve(eq, offset):
    #     if isinstance(eq, BinaryOperator):
    #         if eq.is_any_arrayed():
    #             if eq.arrayed:
                    
    #         else:
    #             return -1
    
    # for i in range(1, 10):
    #     model = Model(starttime=0.0,stoptime=2.0,dt=1.0,name='setup_func_vec_' + str(i))

    #     test_converter = model.converter("test_converter")
    #     test_converter.setup_vector(i, i)

    #     test_mul_converter = model.converter("test_mul_converter")
    #     test_mul_converter.equation = test_converter * i

    #     test_eq = test_converter * i * 0.45

    #     def print_eq(eq, offset):
    #         if isinstance(eq, BinaryOperator):
    #             print(offset + str(type(eq)))
    #             print_eq(eq.element_1, offset + "  ")
    #             print_eq(eq.element_2, offset + "  ")
    #         else:
    #             print(offset + str(type(eq)))
    #     print_eq(test_eq, "")
        # assert(test_mul_converter._elements.vector_size() == i)
        # dim = test_mul_converter._elements.matrix_size()
        # assert(dim == [i, 0])



        # for x in range(0, i):
        #     assert(test_converter[x].equation == i)
        #     assert(test_mul_converter[x].equation == i * i * 0.45)


        # for j in range(1, 10):
        #     test_converter = model.converter("test_converter_matrix" + str(j))
        #     test_converter.setup_matrix([i, j], i + j)
            
        #     test_mul_converter = model.converter("test_converter_matrix_mul_" + str(j))
        #     test_mul_converter.equation = test_converter * i * j * 0.45

        #     for x in range(0, i):
        #         for y in range(0, j):
        #             assert(test_converter[x][y].equation == i + j)
        #             assert(test_mul_converter[x][y].equation == i * i * j * 0.45)


        #bptk.register_model(model)
        #data = bptk.run_scenarios(scenario_managers=["smAbs"],scenarios=["base"],equations=["input_converter","abs_converter"])

        # test_converter = model.converter("test_converter")
        # test_converter.setup_vector(i, i)
        # test_add_converter = model.converter("test_add_converter")
        # test_add_converter.equation = test_converter * i

        # assert(test_add_converter._elements.vector_size() == i)
        # dim = test_add_converter._elements.matrix_size()
        # assert(dim == [i, 0])

        


test_array_functions()