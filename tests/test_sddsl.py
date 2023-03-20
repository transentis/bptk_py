import random
import os
import numpy as np
from BPTK_Py.sdcompiler.compile import compile_xmile
from BPTK_Py.sddsl.operators import BinaryOperator
from BPTK_Py.util import timerange

def test_spm():
    from BPTK_Py import Model
    from BPTK_Py import sd_functions as sd
    model = Model(starttime=0.0, stoptime=120.0, dt=1.0,
                  name='SimpleProjectManagement')

    openTasks = model.stock("openTasks")
    closedTasks = model.stock("closedTasks")
    staff = model.stock("staff")
    completionRate = model.flow("completionRate")
    currentTime = model.converter("currentTime")
    remainingTime = model.converter("remainingTime")
    schedulePressure = model.converter("schedulePressure")
    productivity = model.converter("productivity")
    deadline = model.constant("deadline")
    effortPerTask = model.constant("effortPerTask")
    initialStaff = model.constant("initialStaff")
    initialOpenTasks = model.constant("initialOpenTasks")

    closedTasks.initial_value = 0.0
    staff.initial_value = initialStaff
    openTasks.initial_value = initialOpenTasks
    deadline.equation = 100.0
    effortPerTask.equation = 1.0
    initialStaff.equation = 1.0
    initialOpenTasks.equation = 100.0

    currentTime.equation = sd.time()
    remainingTime.equation = deadline - currentTime
    openTasks.equation = -completionRate
    closedTasks.equation = completionRate

    schedulePressure.equation = sd.min(
        (openTasks * effortPerTask) / (staff * sd.max(remainingTime, 1)), 2.5)

    model.points["productivity"] = [
        [0, 0.4],
        [0.25, 0.444],
        [0.5, 0.506],
        [0.75, 0.594],
        [1, 1],
        [1.25, 1.119],
        [1.5, 1.1625],
        [1.75, 1.2125],
        [2, 1.2375],
        [2.25, 1.245],
        [2.5, 1.25]
    ]

    productivity.equation = sd.lookup(schedulePressure, "productivity")
    completionRate.equation = sd.max(0.0, sd.min(
        openTasks, staff * (productivity / effortPerTask)))

    print(openTasks)
    print(completionRate)

    x = model.converter("x")

    # !=
    x.equation = sd.If(productivity != 1.0, 1, 0)

    for i in range(0, 120+1):
        result = x(i)
        if i < 100:
            assert result == 0
        else:
            assert result == 1

    # ==
    x.equation = sd.If(productivity == 1.0, 1, 0)

    for i in range(0, 120+1):
        result = x(i)
        if i < 100:
            assert result == 1
        else:
            assert result == 0

    # >
    x.equation = sd.If(productivity > 1.0, 1, 0)

    for i in range(0, 120+1):
        result = x(i)
        assert result == 0

    # <
    x.equation = sd.If(productivity < 1.0, 1, 0)

    for i in range(0, 120+1):
        result = x(i)
        if i < 100:
            assert result == 0
        else:
            assert result == 1

    # <=
    x.equation = sd.If(productivity <= 1.0, 1, 0)

    for i in range(0, 120+1):
        result = x(i)

        assert result == 1

    # >=
    x.equation = sd.If(productivity >= 1.0, 1, 0)

    for i in range(0, 120+1):
        result = x(i)

        if i < 100:
            assert result == 1
        else:
            assert result == 0


def test_delay():
    from BPTK_Py import Model
    from BPTK_Py import sd_functions

    model = Model(starttime=1, stoptime=100, dt=1, name='test')

    a = model.converter('a')
    b = model.converter('b')

    a.equation = sd_functions.time()
    b.equation = sd_functions.delay(model, a, 20.0, 10.0)

    df_b = b.plot(return_df=True)

    for index in range(1, 100):
        if index <= 20:
            assert(df_b["b"][index] == 10)
        else:
            assert(df_b["b"][index] == index-20)

    model = Model(starttime=1, stoptime=10, dt=0.25, name='test')

    a = model.converter('a')
    b = model.converter('b')

    a.equation = sd_functions.time()
    b.equation = sd_functions.delay(model, a, 3.0, 0.0)

    df_b = b.plot(return_df=True)

    for index in range(1, 10):
        if index <= 3:
            assert(df_b["b"][index] == 0)
        else:
            assert(df_b["b"][index] == index-3)


def test_equations():
    from BPTK_Py import Model

    from BPTK_Py.bptk import bptk

    bptk = bptk()

    model = Model(starttime=1, stoptime=1, dt=1, name='test')

    a = model.converter('a')

    b = model.converter('b')

    c = model.converter('c')

    a.equation = 0.1

    b.equation = 1 - a
    assert b(1) == 0.9

    b.equation = 1 + a
    assert b(1) == 1.1

    b.equation = 1 * a
    assert b(1) == 0.1

    b.equation = 1 / a
    assert b(1) == 10

    c.equation = a*b
    assert c(1) == 1.0

    a.equation = 3.0
    b.equation = 5.0 - a
    c.equation = a**b
    assert c(1) == 9.0

def test_small_dt():
    from BPTK_Py import Model
    from BPTK_Py import sd_functions as sd
    from BPTK_Py.bptk import bptk
    from BPTK_Py.util import timerange

    model = Model(starttime=0.0,stoptime=10.0,dt=0.001,name='Oscillator')

    # variables
    position = model.stock("position")
    velocity = model.stock("velocity")
    change_in_position = model.biflow("change_in_position")
    change_in_velocity = model.biflow("change_in_velocity")
    acceleration= model.converter("acceleration")
    mass = model.constant("mass")
    stiffness = model.constant("stiffness")
    analytical_solution = model.converter("analytical_solution")

    # equations

    position.initial_value = 1.0
    position.equation = change_in_position

    change_in_position.equation = velocity

    velocity.initial_value = 0.0
    velocity.equation = change_in_velocity

    change_in_velocity.equation = acceleration

    acceleration.equation = -mass*stiffness*position

    mass.equation = 1.0
    stiffness.equation = 1.0

    analytical_solution.equation= (-1)*sd.cos(sd.pi()+sd.time())
    bptk=bptk()
    bptk.register_model(model)
    df=bptk.run_scenarios(
    scenario_managers=["smOscillator"],
    scenarios=["base"],
    equations=["position","analytical_solution"])

    assert df.index.to_list() == timerange(0.0,10.0,0.001,exclusive=False)


def test_sddsl_functions():
    from BPTK_Py import Model
    from BPTK_Py import sd_functions as sd
    from BPTK_Py.bptk import bptk
    import math
    bptk = bptk()

    # abs
    start = 0.0
    dt = 0.1
    stop = 10.0
    model = Model(starttime=start, stoptime=stop, dt=dt, name='abs')

    input_converter = model.converter("input_converter")
    input_converter.equation = sd.time()-5
    abs_converter = model.converter("abs_converter")
    abs_converter.equation = sd.abs(input_converter)
    bptk.register_model(model)
    data = bptk.run_scenarios(scenario_managers=["smAbs"], scenarios=[
                              "base"], equations=["input_converter", "abs_converter"])

    for i in timerange(start, stop, dt):
        assert abs(data.input_converter[i]) == data.abs_converter[i]

    # delay
    start = 0.0
    dt = 0.5
    stop = 10.0
    model = Model(starttime=start, stoptime=stop, dt=dt, name='delay')

    input_function = model.converter("input_function")
    input_function.equation = sd.time()
    delayed_input = model.converter("delayed_input")

    delay_duration = 1.0
    initial_value = 0.0
    delayed_input.equation = sd.delay(
        model, input_function, delay_duration, initial_value)

    bptk.register_model(model)
    data = bptk.run_scenarios(scenario_managers=["smDelay"], scenarios=[
                              "base"], equations=["input_function", "delayed_input"])
    for i in timerange(start, stop, dt):
        if(i < delay_duration + dt):
            assert data.delayed_input[i] == initial_value
            continue

        input_function_index = i - delay_duration
        assert data.delayed_input[i] == data.input_function[input_function_index]

    # dt
    start = 5.0
    dt = 0.25
    stop = 12.0

    model = Model(starttime=start, stoptime=stop, dt=dt, name='dt')
    dt_converter = model.converter("dt")
    dt_converter.equation = sd.dt(model)
    data = dt_converter.plot(return_df=True)

    for i in timerange(start, stop, dt):
        assert data.dt[i] == dt

    # exp
    start = 0
    dt = 0.1
    stop = 10
    model = Model(starttime=start, stoptime=stop, dt=dt, name='exp')

    exp_value = np.log(1)
    growth_rate = model.constant("growth_rate")
    growth_rate.equation = exp_value
    exp = model.converter("exp")
    exp.equation = sd.exp(growth_rate*sd.time())
    data = exp.plot(return_df=True)

    for i in timerange(start, stop, dt):
        assert data.exp[i] == math.exp(exp_value * i)

    # max
    start = 0
    dt = 1
    stop = 10
    model = Model(starttime=start, stoptime=stop, dt=dt, name='max')

    a = model.converter("a")
    a.equation = 5.0+sd.step(15, 5)
    b = model.converter("b")
    b.equation = 10-sd.step(2, 5)
    c = model.converter("c")
    c.equation = sd.max(a, b)
    bptk.register_model(model)

    data = bptk.plot_scenarios(scenario_managers=["smMax"], scenarios=[
                               "base"], equations=["a", "b", "c"], return_df=True)

    for i in timerange(start, stop, dt):
        if i <= 5:
            assert data.c[i] == 10
            continue
        assert data.c[i] == 20

    # min
    start = 0
    dt = 1
    stop = 10
    model = Model(starttime=start, stoptime=stop, dt=dt, name='min')

    a = model.converter("a")
    a.equation = 5.0+sd.step(15, 5)
    b = model.converter("b")
    b.equation = 10-sd.step(2, 5)
    c = model.converter("c")
    c.equation = sd.min(a, b)
    bptk.register_model(model)

    data = bptk.plot_scenarios(scenario_managers=["smMin"], scenarios=[
                               "base"], equations=["a", "b", "c"], return_df=True)

    for i in timerange(start, stop, dt):
        if i <= 5:
            assert data.c[i] == 5
            continue
        assert data.c[i] == 8

    # pulse
    # dt has to be 1/(2^n) or the pulse function does not properly work.
    # the first pulse is 1-interval. Is that intended?
    # first pulse attribute only works when first_pulse < interval. Intended?
    start = 0
    dt = .5
    stop = 9
    model = Model(starttime=start, stoptime=stop, dt=dt, name='pulse')
    stock = model.stock("stock")
    stock.initial_value = 0.0
    flow = model.flow("flow")
    volume = 9.0
    first_pulse = 1.5
    interval = 3.0
    flow.equation = sd.pulse(model, volume, first_pulse, interval)
    stock.equation = flow
    bptk.register_model(model)
    data = bptk.plot_scenarios(scenario_managers=["smPulse"], scenarios=[
                               "base"], equations=["stock", "flow"], return_df=True)
    for i in timerange(start, stop, dt):
        if i < first_pulse:
            assert data.flow[i] == 0
            assert data.stock[i] == 0
            continue
        if i == first_pulse:
            assert data.flow[i] == volume * (1 / dt)
            assert data.stock[i] == 0
            continue

        if i % interval == first_pulse:
            assert data.flow[i] == volume * (1 / dt)
        assert data.stock[i] == volume * \
            (math.ceil((i - first_pulse) / interval))

    # smooth
    # does not test for exact values
    # only tests if the values continously increase, while the rate of change drops and absolute values stays below the max value (which implies some smoothing function)
    start = 1.0
    dt = 0.1
    stop = 10.0
    model = Model(starttime=start, stoptime=stop, dt=dt, name='smooth')

    step_start = 3.0
    step_height = 10.0
    input_function = model.converter("input_function")
    input_function.equation = sd.step(step_height, step_start)

    base_value = 9.0
    smooth = model.converter("smooth")
    smooth.equation = sd.smooth(model, input_function, 1.0, base_value)

    bptk.register_model(model)
    data = bptk.run_scenarios(scenario_managers=["smSmooth"], scenarios=[
                              "base"], equations=["input_function", "smooth"])
    last_value = base_value
    last_change = 9999999
    reached_step_height = False
    for i in timerange(start, stop, dt):
        # smoothing function never exceeds height
        assert data.smooth[i] <= step_height

        # no further testing if necessary if height got reached
        if data.smooth[i] == step_height:
            reached_step_height = True
            continue
        else:
            # ensure the smoothing function never drops below step height once reached
            assert reached_step_height == False

        # before the smooth function reacts to the change in step height it should be equal to the initial value.
        if i <= step_start + dt:
            assert data.smooth[i] == base_value
            continue

        # the value of the function should always increase or stay the same
        assert data.smooth[i] > last_value

        # calculate the rate of change and ensure it is lower than in previous runs.
        new_change = data.smooth[i] - last_value
        assert new_change < last_change

        last_value = data.smooth[i]
        last_change = new_change

    # starttime
    start = 5
    dt = 0.25
    stop = 10
    model = Model(starttime=start, stoptime=stop, dt=dt, name='starttime')

    starttime = model.converter("starttime")
    starttime.equation = sd.starttime(model)
    data = starttime.plot(return_df=True)

    for i in timerange(start, stop, dt):
        assert data.starttime[i] == start

    # stoptime
    start = 5
    dt = 0.25
    stop = 10

    model = Model(starttime=start, stoptime=stop, dt=dt, name='stoptime')
    stoptime = model.converter("stoptime")
    stoptime.equation = sd.stoptime(model)
    data = stoptime.plot(return_df=True)

    for i in timerange(start, stop, dt):
        assert data.stoptime[i] == stop

    # step
    start = 1
    dt = 1
    stop = 10
    model = Model(starttime=1, stoptime=10, dt=1, name='step')

    step_timestep = 5.0
    step_height = 10.0
    step = model.converter("step")
    step.equation = sd.step(step_height, step_timestep)
    data = step.plot(return_df=True)

    for i in timerange(start, stop, dt):
        if i <= step_timestep:
            assert data.step[i] == 0
            continue
        assert data.step[i] == step_height

    # time
    start = 0
    dt = 1
    stop = 10
    model = Model(starttime=start, stoptime=stop, dt=dt, name='time')

    stock = model.stock("stock")
    stock.initial_value = 0.0
    inflow = model.flow("inflow")
    inflow.equation = sd.time()
    stock.equation = inflow

    data = inflow.plot(return_df=True)

    for i in timerange(start, stop, dt):
        assert data.inflow[i] == i

    # trend
    # ToDo

    # round
    start = 0
    dt = 0.1
    stop = 10
    model = Model(starttime=start, stoptime=stop, dt=dt, name='round')
    flow = model.flow("round")
    flow.equation = sd.round(sd.time(), 0)
    data = flow.plot(return_df=True)
    for i in timerange(start, stop, dt):
        assert data['round'][i] == round(i)

    # sqrt
    start = 0
    dt = 1
    stop = 10
    m = Model(starttime=start, stoptime=stop, dt=dt)
    f = m.flow(name="sqrt")

    val = sd.time()

    f.equation = sd.sqrt(val)
    data = f.plot(return_df=True)
    for i in timerange(start, stop, dt):
        assert data.sqrt[i] == math.sqrt(i)

    # sin cos tan
    start = 0
    dt = 0.1
    stop = 10
    m = Model(starttime=start, stoptime=stop, dt=dt)
    sin = m.flow(name="sin")
    tan = m.flow(name="tan")
    cos = m.flow(name="cos")
    x = sd.time()

    sin.equation = sd.sin(x)
    tan.equation = sd.tan(x)
    cos.equation = sd.cos(x)

    data_sin = sin.plot(return_df=True)
    data_tan = tan.plot(return_df=True)
    data_cos = cos.plot(return_df=True)
    for i in timerange(start, stop, dt):
        assert data_sin.sin[i] == max(math.sin(i), 0.0)
        assert data_cos.cos[i] == max(math.cos(i), 0.0)
        assert data_tan.tan[i] == max(math.tan(i), 0.0)

    # beta
    # only tests if it runs
    m = Model(starttime=0, stoptime=10, dt=0.1)
    f = m.flow(name="beta")
    alpha = 1
    beta = 2
    f.equation = sd.beta(alpha, beta)
    data = f.plot(return_df=True)
    assert len(data) == 101

    # binomial
    # only tests if it runs
    m = Model(starttime=0, stoptime=10, dt=0.1)
    f = m.flow(name="binomial")
    n = 100
    p = 0.1
    f.equation = sd.binomial(n, p)
    data = f.plot(return_df=True)
    assert len(data) == 101

    # combinations
    # only works for r < 5?
    start = 3
    dt = 1
    stop = 10
    m = Model(starttime=start, stoptime=stop, dt=dt)
    f = m.flow(name="combinations")
    n = 7
    r = 5
    f.equation = sd.combinations(n, r)
    data = f.plot(return_df=True)
    for i in timerange(start, stop, dt):
        assert data.combinations[i] == 21

    # exprnd
    # only tests if it runs
    m = Model(starttime=0, stoptime=10, dt=0.1)
    f = m.flow(name="exprnd")
    mean = sd.time()
    f.equation = sd.exprnd(mean)
    data = f.plot(return_df=True)
    assert len(data) == 101

    # factorial
    start = 0.0
    dt = 1.0
    stop = 10.0
    m = Model(starttime=start, stoptime=stop, dt=dt)
    f = m.flow(name="factorial")

    n = 5

    f.equation = sd.factorial(sd.time())
    data = f.plot(return_df=True)
    for i in timerange(start, stop, dt):
        assert data.factorial[i] == 1.0*math.factorial(int(i))

    # gamma
    # only tests if it runs
    m = Model(starttime=0.0, stoptime=10.0, dt=0.1)
    f = m.flow(name="gamma")

    shape = 10
    scale = sd.time()

    f.equation = sd.gamma(shape, scale)
    data = f.plot(return_df=True)
    assert len(data) == 101

    # gammaln
    # only tests if it runs
    m = Model(starttime=0, stoptime=10, dt=0.1)
    f = m.flow(name="gammaln")

    n = sd.time()
    f.equation = sd.gammaln(n)
    data = f.plot(return_df=True)
    assert len(data) == 101

    # geometric
    # only tests if it runs
    m = Model(starttime=0, stoptime=10, dt=0.1)
    f = m.flow(name="geometric")

    p = 0.1

    f.equation = sd.geometric(p)
    data = f.plot(return_df=True)
    assert len(data) == 101

    # invnorm
    # only tests if it runs
    m = Model(starttime=-0.5, stoptime=1, dt=0.1)
    f = m.flow(name="invnorm")

    p = sd.time()

    f.equation = sd.invnorm(p)
    data = f.plot(return_df=True)
    assert len(data) == 16

    # logistic
    # only tests if it runs
    m = Model(starttime=-1, stoptime=10, dt=0.1)
    f = m.flow(name="logistic")

    mean = 0
    scale = 1

    f.equation = sd.logistic(mean, scale)
    data = f.plot(return_df=True)
    assert len(data) == 111

    # lognormal
    # only tests if it runs
    m = Model(starttime=0, stoptime=10, dt=0.1)
    f = m.flow(name="lognormal")

    mean = 0
    stdev = 1
    f.equation = sd.lognormal(mean, stdev)
    data = f.plot(return_df=True)
    assert len(data) == 101

    # montecarlo
    # only tests if it runs
    m = Model(starttime=0, stoptime=10, dt=0.1)
    f = m.flow(name="montecarlo")

    probability = 50
    f.equation = sd.montecarlo(probability)
    data = f.plot(return_df=True)

    assert len(data) == 101

    # normal
    # only tests if it runs
    m = Model(starttime=0, stoptime=10, dt=1)
    f = m.flow(name="normal")

    mean = 0
    stdev = 1
    f.equation = sd.normal(mean, stdev)
    data = f.plot(return_df=True)
    assert len(data) == 11

    # normalcdf
    # only tests if it runs
    m = Model(starttime=-4, stoptime=4, dt=0.1)
    f = m.flow(name="normalCDF")
    left = -4
    right = sd.time()
    mean = 0
    stddev = 1
    f.equation = sd.normalcdf(left, right, mean, stddev)
    data = f.plot(return_df=True)
    assert len(data) == 81

    # paetro
    # only tests if it runs
    m = Model(starttime=1, stoptime=10, dt=0.1)
    f = m.flow(name="pareto")
    shape = 1
    scale = 1

    f.equation = sd.pareto(shape, scale)
    data = f.plot(return_df=True)
    assert len(data) == 91

    # permutations
    start = 4
    stop = 10
    dt = 1
    m = Model(starttime=start, stoptime=stop, dt=dt)
    f = m.flow(name="permutations")
    n = sd.time()
    r = 2

    f.equation = sd.permutations(n, r)
    data = f.plot(return_df=True)

    for i in timerange(start, stop, dt):
        assert (math.factorial(int(i)) / math.factorial(int(i) - int(r)))

    # poisson
    # only tests if it runs
    m = Model(starttime=1, stoptime=10, dt=0.1)
    f = m.flow(name="poisson")
    mu = sd.time()

    f.equation = sd.poisson(mu)
    data = f.plot(return_df=True)
    assert len(data) == 91

    # random
    start = .2
    dt = .1
    stop = 30
    m = Model(starttime=start, stoptime=stop, dt=dt)
    f = m.flow(name="random")
    min_value = 0.1
    max_value = sd.time()

    f.equation = sd.random(min_value, max_value)
    data = f.plot(return_df=True)
    for i in timerange(start, stop, dt):
        assert data.random[i] >= min_value and data.random[i] <= i

    # triangular
    # only tests if it runs
    m = Model(starttime=1, stoptime=10, dt=0.1)
    f = m.flow(name="triangular")
    lower_bound = 0
    mode = 1
    upper_bound = sd.time()

    f.equation = sd.triangular(lower_bound, mode, upper_bound)
    data = f.plot(return_df=True)
    assert len(data) == 91

    # weibull
    # only tests if it runs
    m = Model(starttime=1, stoptime=10, dt=0.1)
    f = m.flow(name="weibull")
    shape = 1
    scale = sd.time()

    f.equation = sd.weibull(shape, scale)
    data = f.plot(return_df=True)
    assert len(data) == 91


def get_random(t):
    if t == 2:
        return float(random.randrange(1, 2000) * .1)
    num = float(random.randrange(-2000, 2000) * .1)
    while(num == 0.0):
        num = float(random.randrange(-2000, 2000) * .1)
    return num


def get_element_data(element):
    data = element.plot(return_df=True)
    # 2 because it is the first timestep to consider stocks
    return data[element.name][1]


def setup_vector(element, i, elements, n):
    if(n == 1):
        if isinstance(elements, (float, int)):
            names = {}
            for j in range(i):
                names[str(j)] = elements
            element.setup_named_vector(names)
        else:
            names = {}
            for j in range(i):
                names[str(j)] = elements[j]
            element.setup_named_vector(names)
    else:
        element.setup_vector(i, elements)


def setup_matrix(element, i, elements, n):
    if(n == 1):
        if isinstance(elements, (float, int)):
            names = {}
            for j in range(i[0]):
                cur = {}
                for x in range(i[1]):
                    cur[str(x)] = elements
                names[str(j)] = cur
            element.setup_named_matrix(names)
        else:
            names = {}
            for j in range(i[0]):
                cur = {}
                for x in range(i[1]):
                    cur[str(x)] = elements[j][x]
                names[str(j)] = cur
            element.setup_named_matrix(names)
    else:
        element.setup_matrix(i, elements)

def test_matrix_constant():
    from BPTK_Py import Model
    from BPTK_Py import sd_functions as sd
    from BPTK_Py.bptk import bptk
    import pytest
    import numpy as np

    bptk = bptk()

    # Vector tests (flows, stock, converters)
    elements1 = []
    elements2 = []
    for n in range(2):
        for i in range(1, 10):
            for k in range(1, 10):
                elements1 = []
                elements2 = []
                for temp1 in range(i):
                    elements1.append([])
                    elements2.append([])
                    for temp2 in range(k):
                        elements1[temp1].append(get_random(0))
                        elements2[temp1].append(get_random(0))

                index = str(i) + "_" + str(k) + "_" + str(n)
                model = Model(starttime=0.0, stoptime=2.0, dt=1.0,
                            name='setup_func_mat_' + str(i) + "_" + str(k))
                # Setup tests
                test_element = model.constant("test_element_setup_default" + index)
                setup_matrix(test_element, [i, k], float(i), n)

                transposed = []
                for j in range(k):
                    cur = []
                    for x in range(i):
                        cur.append(elements2[x][j])
                    transposed.append(cur)

                test_element_2_transposed = model.constant(
                    "test_element_2_transposed" + index)
                setup_matrix(test_element_2_transposed, [k, i], transposed, n)

                assert(test_element._elements.matrix_size() == [i, k])
                assert(test_element._elements.vector_size() == i)
                for j in range(i):
                    for x in range(k):
                        assert(get_element_data(test_element[j][x]) == i)
                        assert(get_element_data(test_element[j][x]) != i + 1)

                test_element = model.constant("test_element_setup_individual" + index)
                setup_matrix(test_element, [i, k], elements1, n)

                for j in range(i):
                    for x in range(k):
                        assert(get_element_data(
                            test_element[j][x]) == elements1[j][x])
                        assert(get_element_data(
                            test_element[j][x]) != elements1[j][x] + 1)

                # Element-wise tests
                test_element_val = model.converter("test_element_val" + index)
                test_element_val.equation = get_random(0)

                test_element1 = model.converter("test_element_element_wise1" + index)
                setup_matrix(test_element1, [i, k], elements1, n)

                test_element2 = model.converter("test_element_element_wise2" + index)
                setup_matrix(test_element2, [i, k], elements2, n)

                # Add
                test_element3 = model.converter("test_element_element_wise_add" + index)
                test_element3.equation = test_element1 + test_element2

                for j in range(i):
                    for x in range(k):
                        assert(get_element_data(
                            test_element3[j][x]) == elements1[j][x] + elements2[j][x])
                        assert(get_element_data(
                            test_element3[j][x]) != elements1[j][x] + elements2[j][x] + 1)

                # Subtract
                test_element3 = model.converter("test_element_element_wise_sub" + index)
                test_element3.equation = test_element1 - test_element2

                for j in range(i):
                    for x in range(k):
                        assert(get_element_data(
                            test_element3[j][x]) == elements1[j][x] - elements2[j][x])
                        assert(get_element_data(
                            test_element3[j][x]) != elements1[j][x] - elements2[j][x] + 1)

                # Multiply
                test_element3 = model.converter("test_element_element_wise_mul" + index)
                test_element3.equation = test_element1 * test_element2

                for j in range(i):
                    for x in range(k):
                        assert(get_element_data(
                            test_element3[j][x]) == elements1[j][x] * elements2[j][x])
                        assert(get_element_data(
                            test_element3[j][x]) != elements1[j][x] * elements2[j][x] + 1)

                # Divide
                test_element3 = model.converter("test_element_element_wise_div" + index)
                test_element3.equation = test_element1 / test_element2
                for j in range(i):
                    for x in range(k):
                        if(elements2[j][x] == 0):
                            assert(get_element_data(
                                test_element3[j][x]) == 0)
                        else:
                            assert(get_element_data(
                                test_element3[j][x]) == elements1[j][x] / elements2[j][x])
                            assert(get_element_data(
                                test_element3[j][x]) != elements1[j][x] / elements2[j][x] + 1)

                # Dot tests
                try:
                    test_element3 = model.converter("test_element_dot" + index)
                    test_element3.equation = test_element1.dot(
                        test_element_2_transposed)

                    temp = np.dot(elements1, transposed)

                    for j in range(i):
                        for x in range(i):
                            assert(get_element_data(
                                test_element3[j][x]) == pytest.approx(temp[j][x]))
                            assert(get_element_data(
                                test_element3[j][x]) != pytest.approx(temp[j][x]+1000000.0))
                except:
                    assert(n == 1)

                # Functions
                test_element3 = model.converter("test_element_sum" + index)
                test_element3.equation = test_element1.arr_sum()

                assert(get_element_data(test_element3) ==
                    pytest.approx(np.sum(elements1)))
                assert(get_element_data(test_element3)
                    != np.sum(elements1) + 1)

                test_element3 = model.converter("test_element_mean" + index)
                test_element3.equation = test_element1.arr_mean()
                assert(get_element_data(test_element3) ==
                    pytest.approx(np.mean(elements1)))
                assert(get_element_data(test_element3)
                    != np.mean(elements1) + 1)

                test_element3 = model.converter("test_element_median" + index)
                test_element3.equation = test_element1.arr_median()
                assert(get_element_data(test_element3) ==
                    pytest.approx(np.median(elements1)))
                assert(get_element_data(test_element3)
                    != np.median(elements1) + 1)

                test_element3 = model.converter("test_element_prod" + index)
                test_element3.equation = test_element1.arr_prod()
                assert(get_element_data(test_element3) ==
                    pytest.approx(np.prod(elements1)))
                assert(get_element_data(test_element3)
                    != np.prod(elements1) * 200 + 1)

                test_element3 = model.converter("test_element_stddev" + index)
                test_element3.equation = test_element1.arr_stddev()
                assert(get_element_data(test_element3) ==
                    pytest.approx(np.std(elements1)))
                assert(get_element_data(test_element3)
                    != np.std(elements1) + 1)

                test_element3 = model.converter("test_element_size" + index)
                test_element3.equation = test_element1.arr_size()
                assert(get_element_data(test_element3) == i)
                assert(get_element_data(test_element3)
                    != i + 1)

                temp = []
                for j in range(i):
                    for x in range(k):
                        temp.append(elements1[j][x])

                temp.sort(reverse=True)

                # for j in range(i * k):
                #     test_element3 = get_element(
                #         t, model, "test_element_rank_" + str(j))

                temp_val = temp[j]

                test_element3.equation = test_element1.arr_rank(j + 1)

                assert(get_element_data(test_element3)
                    == pytest.approx(temp_val))
                assert(get_element_data(test_element3) != temp_val + 1)

                # Exception testing
                for j in range(1, i + 1):
                    for x in range(1, k + 1):
                        test_element4 = model.constant(
                            "test_element4_exc_" + str(j) + "_" + str(x) + index)
                        setup_matrix(test_element4, [j, x], 2.0, n)
                        try:
                            test_element3 = model.constant("test_element_exc" + str(j) + "_" + str(x) + index)
                            test_element3.equation = test_element4.dot(
                                test_element2)
                            assert(x == i)
                        except:
                            assert(x != i or n == 1)

                        try:
                            test_element3 = model.constant("test_element_exc" + str(j) + "_" + str(x) + index)
                            setup_matrix(test_element3, [j, x], elements1, n)
                            assert(j == i and x == k)
                        except:
                            assert(not (j == i and x == k))

""" def test_vector():
    from BPTK_Py import Model
    from BPTK_Py import sd_functions as sd
    from BPTK_Py.bptk import bptk
    import pytest
    import numpy as np

    bptk = bptk()

    def get_element(num, model, name):
        if num == 0:
            return model.converter(name)
        if num == 1:
            return model.stock(name)
        if num == 2:
            return model.flow(name)
        if num == 3:
            return model.constant(name)

    # Vector tests (flows, stock, converters)
    for n in range(2):
        for t in range(3):
            elements1 = [get_random(t)]
            elements2 = [get_random(t)]
            for i in range(1, 10):
                model = Model(starttime=0.0, stoptime=2.0, dt=1.0,
                            name='setup_func_vec_' + str(i))
                index = str(n) + "_" + str(t) + "_" + str(i)
                # Setup tests
                test_element = get_element(t, model, "test_element_setup_default")
                setup_vector(test_element, i, float(i), n)

                assert(test_element._elements.matrix_size() == [i, 0])
                assert(test_element._elements.vector_size() == i)

                for j in range(i):
                    assert(get_element_data(test_element[j]) == i)
                    assert(get_element_data(test_element[j]) != i + 1)

                test_element = get_element(
                    t, model, "test_element_setup_individual")
                setup_vector(test_element, i, elements1, n)
                # print(test_element[0])
                for j in range(i):
                    assert(get_element_data(test_element[j]) == elements1[j])
                    assert(get_element_data(test_element[j]) != elements1[j] + 1)

                # Element-wise tests

                test_element_val = model.converter("test_element_val" + index)
                test_element_val.equation = get_random(t)

                test_element1 = model.converter("test_element_element_wise1" + index)
                setup_vector(test_element1, i, elements1, n)

                test_element2 = model.converter("test_element_element_wise2" + index)
                setup_vector(test_element2, i, elements2, n)

                # Add
                test_element3 = get_element(
                    t, model, "test_element_element_wise_add")
                test_element3.equation = test_element1 + test_element2

                for j in range(i):
                    assert(get_element_data(
                        test_element3[j]) == elements1[j] + elements2[j])
                    assert(get_element_data(
                        test_element3[j]) != elements1[j] + elements2[j] + 1)

                # Subtract
                test_element3 = get_element(
                    t, model, "test_element_element_wise_sub")
                test_element3.equation = test_element1 - test_element2

                for j in range(i):
                    if t == 2:  # Flows
                        assert(get_element_data(test_element3[j]) == max(
                            elements1[j] - elements2[j], 0.0))
                        assert(get_element_data(test_element3[j]) != max(
                            elements1[j] - elements2[j] + 1, 1.0))
                    else:
                        assert(get_element_data(
                            test_element3[j]) == elements1[j] - elements2[j])
                        assert(get_element_data(
                            test_element3[j]) != elements1[j] - elements2[j] + 1)

                # Multiply
                test_element3 = get_element(
                    t, model, "test_element_element_wise_mul")
                test_element3.equation = test_element1 * test_element2

                for j in range(i):
                    assert(get_element_data(
                        test_element3[j]) == elements1[j] * elements2[j])
                    assert(get_element_data(
                        test_element3[j]) != elements1[j] * elements2[j] + 1)

                # Divide
                test_element3 = get_element(
                    t, model, "test_element_element_wise_div")
                test_element3.equation = test_element1 / test_element2

                for j in range(i):
                    assert(get_element_data(
                        test_element3[j]) == elements1[j] / elements2[j])
                    assert(get_element_data(
                        test_element3[j]) != elements1[j] / elements2[j] + 1)

                try:
                    # Dot tests
                    test_element3 = get_element(t, model, "test_element_dot")
                    test_element3.equation = test_element1.dot(test_element2)

                    assert(get_element_data(test_element3)
                        == np.dot(elements1, elements2))
                    assert(get_element_data(test_element3) !=
                        np.dot(elements1, elements2) + 1)
                        
                    test_element3 = get_element(t, model, "test_element_dot_val_vec")
                    test_element3.equation = test_element_val.dot(test_element2)

                    np_res = np.dot(test_element_val, elements2)

                    for j in range(i):
                        assert(get_element_data(test_element3[j]) == np_res[j])
                        assert(get_element_data(test_element3[j]) != np_res[j] + 1)

                    test_element3 = get_element(t, model, "test_element_dot_vec_val")
                    test_element3.equation = test_element2.dot(test_element_val)

                    np_res = np.dot(elements2, test_element_val)

                    for j in range(i):
                        assert(get_element_data(test_element3[j]) == np_res[j])
                        assert(get_element_data(test_element3[j]) != np_res[j] + 1)
                except:
                    assert(n == 1)

                # Functions
                test_element3 = get_element(t, model, "test_element_sum")
                test_element3.equation = test_element1.arr_sum()

                assert(get_element_data(test_element3) ==
                    pytest.approx(np.sum(elements1)))
                assert(get_element_data(test_element3) != np.sum(elements1) + 1)

                test_element3 = get_element(t, model, "test_element_mean")
                test_element3.equation = test_element1.arr_mean()
                assert(get_element_data(test_element3) ==
                    pytest.approx(np.mean(elements1)))
                assert(get_element_data(test_element3) != np.mean(elements1) + 1)

                test_element3 = get_element(t, model, "test_element_median")
                test_element3.equation = test_element1.arr_median()
                assert(get_element_data(test_element3) ==
                    pytest.approx(np.median(elements1)))
                assert(get_element_data(test_element3) != np.median(elements1) + 1)

                test_element3 = get_element(t, model, "test_element_prod")
                test_element3.equation = test_element1.arr_prod()
                assert(get_element_data(test_element3) ==
                    pytest.approx(np.prod(elements1)))
                assert(get_element_data(test_element3) != np.prod(elements1) * 2)

                test_element3 = get_element(t, model, "test_element_stddev")
                test_element3.equation = test_element1.arr_stddev()
                assert(get_element_data(test_element3) ==
                    pytest.approx(np.std(elements1)))
                assert(get_element_data(test_element3) != np.std(elements1) + 1)

                test_element3 = get_element(t, model, "test_element_size")
                test_element3.equation = test_element1.arr_size()
                assert(get_element_data(test_element3) ==
                    pytest.approx(np.size(elements1)))
                assert(get_element_data(test_element3) != np.size(elements1) + 1)

                for j in range(i):
                    test_element3 = get_element(t, model, "test_element_rank")

                    temp_arr = np.sort(elements1)
                    temp_val = temp_arr[-(j + 1)]

                    test_element3.equation = test_element1.arr_rank(j + 1)

                    assert(get_element_data(test_element3)
                        == pytest.approx(temp_val))
                    assert(get_element_data(test_element3) != temp_val + 1)

                # Exception testing
                for j in range(i + 1):
                    test_element4 = get_element(t, model, "test_element4")
                    setup_vector(test_element4, j, 2.0, n)

                    try:
                        test_element3 = get_element(t, model, "test_element_exc")
                        test_element3.equation = test_element4.dot(test_element2)
                        assert(j == i)
                    except:
                        assert(j != i or n == 1)

                    try:
                        test_element3 = get_element(t, model, "test_element_exc")
                        setup_vector(test_element3, j, elements1, n)
                        assert(j == i)
                    except:
                        assert(j != i)

                elements1.append(get_random(t))
                elements2.append(get_random(t))

def test_vector_constants():
    from BPTK_Py import Model
    from BPTK_Py import sd_functions as sd
    from BPTK_Py.bptk import bptk
    import pytest
    import numpy as np

    bptk = bptk()
    elements1 = []
    elements2 = []
    for n in range(2):
        elements1 = [get_random(0)]
        elements2 = [get_random(0)]
        for i in range(1, 10):
            index = "_" + str(i) + "_" + str(n)
            print(i,n)
            model = Model(starttime=0.0, stoptime=2.0, dt=1.0,
                        name='setup_func_vec_' + str(i))

            # Setup tests
            test_constant = model.constant("test_constant_setup_default" + index)
            setup_vector(test_constant, i, float(i), n)
            print(elements1, elements2)
            assert(test_constant._elements.matrix_size() == [i, 0])
            assert(test_constant._elements.vector_size() == i)

            for j in range(i):
                assert(get_element_data(test_constant[j]) == i)
                assert(get_element_data(test_constant[j]) != i + 1)

            test_constant = model.constant("test_constant_setup_individual" + index)
            setup_vector(test_constant, i, elements1, n)

            for j in range(i):
                assert(get_element_data(test_constant[j]) == elements1[j])
                assert(get_element_data(test_constant[j]) != elements1[j] + 1)

            # Element-wise tests

            test_constant_val = model.constant("test_constant_val" + index)
            test_constant_val.equation = get_random(0)

            test_constant1 = model.constant("test_constant_element_wise1" + index)
            setup_vector(test_constant1, i, elements1, n)

            test_constant2 = model.constant("test_constant_element_wise2" + index)
            setup_vector(test_constant2, i, elements2, n)

            # Add
            test_constant3 = model.converter("test_constant_element_wise_add" + index)
            test_constant3.equation = test_constant1 + test_constant2

            for j in range(i):
                assert(get_element_data(
                    test_constant3[j]) == elements1[j] + elements2[j])
                assert(get_element_data(
                    test_constant3[j]) != elements1[j] + elements2[j] + 1)

            # Subtract
            test_constant3 = model.converter("test_constant_element_wise_sub" + index)
            test_constant3.equation = test_constant1 - test_constant2

            for j in range(i):
                assert(get_element_data(
                    test_constant3[j]) == elements1[j] - elements2[j])
                assert(get_element_data(
                    test_constant3[j]) != elements1[j] - elements2[j] + 1)

            # Multiply
            test_constant3 = model.converter("test_constant_element_wise_mul" + index)
            test_constant3.equation = test_constant1 * test_constant2

            for j in range(i):
                assert(get_element_data(
                    test_constant3[j]) == elements1[j] * elements2[j])
                assert(get_element_data(
                    test_constant3[j]) != elements1[j] * elements2[j] + 1)

            # Divide
            test_constant3 = model.converter("test_constant_element_wise_div" + index)
            test_constant3.equation = test_constant1 / test_constant2

            for j in range(i):
                assert(get_element_data(
                    test_constant3[j]) == elements1[j] / elements2[j])
                assert(get_element_data(
                    test_constant3[j]) != elements1[j] / elements2[j] + 1)

            try:
                # Dot tests
                test_constant3 = model.converter("test_constant_dot" + index)
                test_constant3.equation = test_constant1.dot(test_constant2)

                assert(get_element_data(test_constant3)
                    == np.dot(elements1, elements2))
                assert(get_element_data(test_constant3) !=
                    np.dot(elements1, elements2) + 1)

                test_constant3 = model.converter("test_constant_dot_val_vec" + index)
                test_constant3.equation = test_constant_val.dot(test_constant2)

                np_res = np.dot(test_constant_val, elements2)

                for j in range(i):
                    assert(get_element_data(test_constant3[j]) == np_res[j])
                    assert(get_element_data(test_constant3[j]) != np_res[j] + 1)

                test_constant3 = model.converter("test_constant_dot_vec_val" + index)
                test_constant3.equation = test_constant2.dot(test_constant_val)

                np_res = np.dot(elements2, test_constant_val)

                for j in range(i):
                    assert(get_element_data(test_constant3[j]) == np_res[j])
                    assert(get_element_data(test_constant3[j]) != np_res[j] + 1)
            except:
                assert(n == 1)

            # Functions
            test_constant3 = model.converter("test_constant_sum" + index)
            test_constant3.equation = test_constant1.arr_sum()

            assert(get_element_data(test_constant3) ==
                pytest.approx(np.sum(elements1)))
            assert(get_element_data(test_constant3) != np.sum(elements1) + 1)

            test_constant3 = model.converter("test_constant_mean" + index)
            test_constant3.equation = test_constant1.arr_mean()
            assert(get_element_data(test_constant3) ==
                pytest.approx(np.mean(elements1)))
            assert(get_element_data(test_constant3) != np.mean(elements1) + 1)

            test_constant3 = model.converter("test_constant_median" + index)
            test_constant3.equation = test_constant1.arr_median()
            assert(get_element_data(test_constant3) ==
                pytest.approx(np.median(elements1)))
            assert(get_element_data(test_constant3) != np.median(elements1) + 1)

            test_constant3 = model.converter("test_constant_prod" + index)
            test_constant3.equation = test_constant1.arr_prod()
            assert(get_element_data(test_constant3) ==
                pytest.approx(np.prod(elements1)))
            assert(get_element_data(test_constant3) != np.prod(elements1) * 2)

            test_constant3 = model.converter("test_constant_stddev" + index)
            test_constant3.equation = test_constant1.arr_stddev()
            assert(get_element_data(test_constant3) ==
                pytest.approx(np.std(elements1)))
            assert(get_element_data(test_constant3) != np.std(elements1) + 1)

            test_constant3 = model.converter("test_constant_size" + index)
            test_constant3.equation = test_constant1.arr_size()
            assert(get_element_data(test_constant3) ==
                pytest.approx(np.size(elements1)))
            assert(get_element_data(test_constant3) != np.size(elements1) + 1)

            for j in range(i + 1):
                test_constant3 = model.converter("test_constant_rank" + index)

                temp_arr = np.sort(elements1)
                temp_val = temp_arr[-j]

                test_constant3.equation = test_constant1.arr_rank(j)
                assert(get_element_data(test_constant3) == pytest.approx(temp_val))
                assert(get_element_data(test_constant3) != temp_val + 1)

            # Exception testing
            for j in range(i + 1):
                test_constant4 = model.constant("test_constant4" + index)
                setup_vector(test_constant4, j, 2.0, n)

                try:
                    test_constant3 = model.converter("test_constant_exc" + index)
                    test_constant3.equation = test_constant4.dot(test_constant2)
                    assert(j == i)
                except:
                    assert(j != i or n == 1)

                try:
                    test_constant3 = model.converter("test_constant_exc" + index)
                    setup_vector(test_constant3, j, elements1, n)
                    assert(j == i)
                except:
                    assert(j != i)

            elements1.append(get_random(0))
            elements2.append(get_random(0))
 """

""" def test_matrix():
    from BPTK_Py import Model
    from BPTK_Py import sd_functions as sd
    from BPTK_Py.bptk import bptk
    import pytest
    import numpy as np

    bptk = bptk()
    element_count = 0
    def get_element(num, model, name):
        if num == 0:
            return model.converter(name + "_" + str(element_count))
        if num == 1:
            return model.stock(name + "_" + str(element_count))
        if num == 2:
            return model.flow(name + "_" + str(element_count))
        if num == 3:
            return model.constant(name + "_" + str(element_count))

    # Vector tests (flows, stock, converters)
    for n in range(2):
        for t in range(3):
            elements1 = []
            elements2 = []
            for i in range(1, 10):
                for k in range(1, 10):
                    elements1 = []
                    elements2 = []
                    for temp1 in range(i):
                        elements1.append([])
                        elements2.append([])
                        for temp2 in range(k):
                            elements1[temp1].append(get_random(t))
                            elements2[temp1].append(get_random(t))
                    index = str(i) + "_" + str(k) + "_" + str(t) + "_" + str(n)
                    model = Model(starttime=0.0, stoptime=2.0, dt=1.0,
                                name='setup_func_mat_' + str(i) + "_" + str(k))
                    # Setup tests
                    test_element = get_element(
                        t, model, "test_element_setup_default")
                    setup_matrix(test_element, [i, k], float(i), n)

                    transposed = []
                    for j in range(k):
                        cur = []
                        for x in range(i):
                            cur.append(elements2[x][j])
                        transposed.append(cur)

                    test_element_2_transposed = model.converter(
                        "test_element_2_transposed" + index)
                    setup_matrix(test_element_2_transposed, [k, i], transposed, n)

                    assert(test_element._elements.matrix_size() == [i, k])
                    assert(test_element._elements.vector_size() == i)

                    for j in range(i):
                        for x in range(k):
                            assert(get_element_data(test_element[j][x]) == i)
                            assert(get_element_data(test_element[j][x]) != i + 1)

                    test_element = get_element(
                        t, model, "test_element_setup_individual")
                    setup_matrix(test_element, [i, k], elements1, n)

                    for j in range(i):
                        for x in range(k):
                            assert(get_element_data(
                                test_element[j][x]) == elements1[j][x])
                            assert(get_element_data(
                                test_element[j][x]) != elements1[j][x] + 1)

                    # Element-wise tests
                    test_element_val = model.converter("test_element_val" + index)
                    test_element_val.equation = get_random(t)

                    test_element1 = model.converter("test_element_element_wise1" + index)
                    setup_matrix(test_element1, [i, k], elements1, n)

                    test_element2 = model.converter("test_element_element_wise2" + index)
                    setup_matrix(test_element2, [i, k], elements2, n)

                    # Add
                    test_element3 = get_element(
                        t, model, "test_element_element_wise_add")
                    test_element3.equation = test_element1 + test_element2

                    for j in range(i):
                        for x in range(k):
                            assert(get_element_data(
                                test_element3[j][x]) == elements1[j][x] + elements2[j][x])
                            assert(get_element_data(
                                test_element3[j][x]) != elements1[j][x] + elements2[j][x] + 1)

                    # Subtract
                    test_element3 = get_element(
                        t, model, "test_element_element_wise_sub")
                    test_element3.equation = test_element1 - test_element2

                    for j in range(i):
                        for x in range(k):
                            if t == 2:  # Flows
                                assert(get_element_data(test_element3[j][x]) == max(
                                    elements1[j][x] - elements2[j][x], 0.0))
                                assert(get_element_data(test_element3[j][x]) != max(
                                    elements1[j][x] - elements2[j][x] + 1, 1.0))
                            else:
                                assert(get_element_data(
                                    test_element3[j][x]) == elements1[j][x] - elements2[j][x])
                                assert(get_element_data(
                                    test_element3[j][x]) != elements1[j][x] - elements2[j][x] + 1)

                    # Multiply
                    test_element3 = get_element(
                        t, model, "test_element_element_wise_mul")
                    test_element3.equation = test_element1 * test_element2

                    for j in range(i):
                        for x in range(k):
                            assert(get_element_data(
                                test_element3[j][x]) == elements1[j][x] * elements2[j][x])
                            assert(get_element_data(
                                test_element3[j][x]) != elements1[j][x] * elements2[j][x] + 1)

                    # Divide
                    test_element3 = get_element(
                        t, model, "test_element_element_wise_div")
                    test_element3.equation = test_element1 / test_element2
                    for j in range(i):
                        for x in range(k):
                            if(elements2[j][x] == 0):
                                assert(get_element_data(
                                    test_element3[j][x]) == 0)
                            else:
                                assert(get_element_data(
                                    test_element3[j][x]) == elements1[j][x] / elements2[j][x])
                                assert(get_element_data(
                                    test_element3[j][x]) != elements1[j][x] / elements2[j][x] + 1)
                    try:
                        # Dot tests
                        test_element3 = get_element(t, model, "test_element_dot")
                        test_element3.equation = test_element1.dot(
                            test_element_2_transposed)

                        temp = np.dot(elements1, transposed)

                        for j in range(i):
                            for x in range(i):
                                assert(get_element_data(
                                    test_element3[j][x]) == pytest.approx(temp[j][x]))
                                assert(get_element_data(
                                    test_element3[j][x]) != pytest.approx(temp[j][x]+1000000.0))

                    except:
                        assert(n == 1)
                    # Functions
                    test_element3 = get_element(t, model, "test_element_sum")
                    test_element3.equation = test_element1.arr_sum()

                    assert(get_element_data(test_element3) ==
                        pytest.approx(np.sum(elements1)))
                    assert(get_element_data(test_element3)
                        != np.sum(elements1) + 1)

                    test_element3 = get_element(t, model, "test_element_mean")
                    test_element3.equation = test_element1.arr_mean()
                    assert(get_element_data(test_element3) ==
                        pytest.approx(np.mean(elements1)))
                    assert(get_element_data(test_element3)
                        != np.mean(elements1) + 1)

                    test_element3 = get_element(t, model, "test_element_median")
                    test_element3.equation = test_element1.arr_median()
                    assert(get_element_data(test_element3) ==
                        pytest.approx(np.median(elements1)))
                    assert(get_element_data(test_element3)
                        != np.median(elements1) + 1)

                    test_element3 = get_element(t, model, "test_element_prod")
                    test_element3.equation = test_element1.arr_prod()
                    assert(get_element_data(test_element3) ==
                        pytest.approx(np.prod(elements1)))
                    assert(get_element_data(test_element3)
                        != np.prod(elements1) * 200 + 1)

                    test_element3 = get_element(t, model, "test_element_stddev")
                    test_element3.equation = test_element1.arr_stddev()
                    assert(get_element_data(test_element3) ==
                        pytest.approx(np.std(elements1)))
                    assert(get_element_data(test_element3)
                        != np.std(elements1) + 1)

                    test_element3 = get_element(t, model, "test_element_size")
                    test_element3.equation = test_element1.arr_size()
                    assert(get_element_data(test_element3) == i)
                    assert(get_element_data(test_element3)
                        != i + 1)

                    temp = []
                    for j in range(i):
                        for x in range(k):
                            temp.append(elements1[j][x])

                    temp.sort(reverse=True)

                    # for j in range(i * k):
                    #     test_element3 = get_element(
                    #         t, model, "test_element_rank_" + str(j))

                    temp_val = temp[j]

                    test_element3.equation = test_element1.arr_rank(j + 1)

                    assert(get_element_data(test_element3)
                        == pytest.approx(temp_val))
                    assert(get_element_data(test_element3) != temp_val + 1)

                    # Exception testing
                    for j in range(1, i + 1):
                        for x in range(1, k + 1):
                            test_element4 = get_element(
                                t, model, "test_element4_exc_" + str(j) + "_" + str(x))
                            setup_matrix(test_element4, [j, x], 2.0, n)
                            try:
                                test_element3 = get_element(
                                    t, model, "test_element3_exc_" + str(j) + "_" + str(x))
                                test_element3.equation = test_element4.dot(
                                    test_element2)
                                assert(x == i)
                            except:
                                assert(x != i or n == 1)

                            try:
                                test_element3 = get_element(
                                    t, model, "test_element_exc_" + str(j) + "_" + str(x))
                                setup_matrix(test_element3, [j, x], elements1, n)
                                assert(j == i and x == k)
                            except:
                                assert(not (j == i and x == k))

 """




# def test_vector_stock_flow():
#     from BPTK_Py import Model
#     from BPTK_Py import sd_functions as sd
#     from BPTK_Py.bptk import bptk
#     import pytest
#     import numpy as np

#     bptk = bptk()


