import os
import numpy as np
from BPTK_Py.sdcompiler.compile import compile_xmile

def test_compilation():
    """
    Compile models and make sure they exist afterwards. Not more, not less
    :return:
    """

    import os

    src = "./test_models/test_expressions.stmx"
    dest = "./test_models/test_expressions.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os

    src = "./test_models/test_safediv.stmx"
    dest = "./test_models/test_safediv.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os

    src = "./test_models/test_pareto.stmx"
    dest = "./test_models/test_pareto.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os

    src = "./test_models/test_weibull.stmx"
    dest = "./test_models/test_weibull.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os

    src = "./test_models/test_delayn.stmx"
    dest = "./test_models/test_delayn.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os

    src = "./test_models/test_sinwave.stmx"
    dest = "./test_models/test_sinwave.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os

    src = "./test_models/test_smthn.stmx"
    dest = "./test_models/test_smthn.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os
    import numpy as np

    src = "./test_models/test_lookup.stmx"
    dest = "./test_models/test_lookup.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os

    src = "./test_models/test_ramp.stmx"
    dest = "./test_models/test_ramp.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os

    src = "./test_models/test_trend.stmx"
    dest = "./test_models/test_trend.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os

    src = "./test_models/test_poisson.stmx"
    dest = "./test_models/test_poisson.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os

    src = "./test_models/test_logistic.stmx"
    dest = "./test_models/test_logistic.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    os.remove("./test_models/test_logistic.py")

    import os
    import numpy as np

    src = "./test_models/test_negbinomial.stmx"
    dest = "./test_models/test_negbinomial.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os
    import numpy as np

    src = "./test_models/test_lognormal.stmx"
    dest = "./test_models/test_lognormal.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)
    os.remove( "./test_models/test_lognormal.py")

    import os

    src = "./test_models/test_financials.stmx"
    dest = "./test_models/test_financials.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os

    src = "./test_models/test_log10.stmx"
    dest = "./test_models/test_log10.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os

    src = "./test_models/test_lookuparea.stmx"
    dest = "./test_models/test_lookuparea.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os

    src = "./test_models/test_sqrt.stmx"
    dest = "./test_models/test_sqrt.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os

    src = "./test_models/test_percent.stmx"
    dest = "./test_models/test_percent.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os

    src = "./test_models/test_clocktime.stmx"
    dest = "./test_models/test_clocktime.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os

    src = "./test_models/test_if.stmx"
    dest = "./test_models/test_if.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os
    import numpy as np

    src = "./test_models/test_triangular.stmx"
    dest = "./test_models/test_triangular.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os

    src = "./test_models/test_step.stmx"
    dest = "./test_models/test_step.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)


    src = "./test_models/test_dt_fraction.stmx"
    dest = "./test_models/test_dt_fraction.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)


    src = "./test_models/test_dt_rational.stmx"
    dest = "./test_models/test_dt_rational.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)


    src = "./test_models/test_no_dimensions.stmx"
    dest = "./test_models/test_no_dimensions.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os

    src = "./test_models/test_rootn.stmx"
    dest = "./test_models/test_rootn.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)


    src = "./test_models/test_time.stmx"
    dest = "./test_models/test_time.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)


    src = "./test_models/test_smooth.stmx"
    dest = "./test_models/test_smooth.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)


    src = "./test_models/test_abs.stmx"
    dest = "./test_models/test_abs.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)


    src = "./test_models/test_npv.stmx"
    # src ="./test_models/delay_example.itmx"
    dest = "./test_models/test_npv.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)


    src = "./test_models/test_cos.stmx"
    dest = "./test_models/test_cos.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os

    src = "./test_models/test_tan.stmx"
    dest = "./test_models/test_tan.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os

    src = "./test_models/test_sim_builtins.stmx"
    dest = "./test_models/test_sim_builtins.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    src = "./test_models/test_random.stmx"
    dest = "./test_models/test_random.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os

    src = "./test_models/test_array.stmx"
    dest = "./test_models/test_array.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os

    src = "./test_models/test_delay.stmx"
    dest = "./test_models/test_delay.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os
    import numpy as np

    src = "./test_models/test_endval.stmx"
    dest = "./test_models/test_endval.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os

    src = "./test_models/test_array_extended.stmx"
    dest = "./test_models/test_array_extended.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os

    src = "./test_models/test_array_3dimensional.stmx"
    dest = "./test_models/test_array_3dimensional.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)


    import os

    src = "./test_models/test_array_2dimensional.stmx"
    dest = "./test_models/test_array_2dimensional.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os

    src = "./test_models/test_permutation.stmx"
    dest = "./test_models/test_permutation.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os

    src = "./test_models/test_forecast.stmx"
    dest = "./test_models/test_forecast.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import os

    src = "./test_models/test_smth3.stmx"
    dest = "./test_models/test_smth3.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)


def test_trend_model():
    """
    TREND
    :return:
    """
    test_data = {1.0: 0.693147, 1.1: 0.697040160401, 1.2: 0.700323219004, 1.3: 0.703089928837, 1.4: 0.705420181666,
                 1.5: 0.707381895491,
                 1.6: 0.709032694287,
                 1.7: 0.710421386843,
                 1.8: 0.711589257659,
                 1.9: 0.712571186098,
                 2.0: 0.713396611268,
                 2.1: 0.714090360164,
                 2.2: 0.71467335582,
                 2.3: 0.71516322101,
                 2.4: 0.715574791619,
                 2.5: 0.71592055229,
                 2.6: 0.716211005471,
                 2.7: 0.716454983599,
                 2.8: 0.716659912871,
                 2.9: 0.71683203587,
                 3.0: 0.71697659933,
                 3.1: 0.717098012368,
                 3.2: 0.717199979768,
                 3.3: 0.717285614178,
                 3.4: 0.717357530533,
                 3.5: 0.717417925486,
                 3.6: 0.717468644203,
                 3.7: 0.717511236531,
                 3.8: 0.717547004206,
                 3.9: 0.717577040536,
                 4.0: 0.717602263746,
                 4.1: 0.717623444997,
                 4.2: 0.717641231926,
                 4.3: 0.717656168424,
                 4.4: 0.717668711245,
                 4.5: 0.717679243966,
                 4.6: 0.717688088705,
                 4.7: 0.717695515965,
                 4.8: 0.717701752905,
                 4.9: 0.717706990285,
                 5.0: 0.717711388292,
                 5.1: 0.717715081448,
                 5.2: 0.717718182712,
                 5.3: 0.717720786944,
                 5.4: 0.717722973802,
                 5.5: 0.717724810175,
                 5.6: 0.717726352235,
                 5.7: 0.717727647151,
                 5.8: 0.717728734532,
                 5.9: 0.71772964764,
                 6.0: 0.717730414404,
                 6.1: 0.717731058279,
                 6.2: 0.71773159896,
                 6.3: 0.717732052986,
                 6.4: 0.717732434246,
                 6.5: 0.717732754401,
                 6.6: 0.717733023245,
                 6.7: 0.717733249002,
                 6.8: 0.717733438576,
                 6.9: 0.717733597767,
                 7.0: 0.717733731445,
                 7.1: 0.717733843698,
                 7.2: 0.71773393796,
                 7.3: 0.717734017115,
                 7.4: 0.717734083584,
                 7.5: 0.717734139399,
                 7.6: 0.717734186269,
                 7.7: 0.717734225628,
                 7.8: 0.717734258678,
                 7.9: 0.717734286431,
                 8.0: 0.717734309737,
                 8.1: 0.717734329307,
                 8.2: 0.71773434574,
                 8.3: 0.71773435954,
                 8.4: 0.717734371128,
                 8.5: 0.717734380859,
                 8.6: 0.71773438903,
                 8.7: 0.717734395892,
                 8.8: 0.717734401654,
                 8.9: 0.717734406492,
                 9.0: 0.717734410556,
                 9.1: 0.717734413967,
                 9.2: 0.717734416832,
                 9.3: 0.717734419238,
                 9.4: 0.717734421258,
                 9.5: 0.717734422955,
                 9.6: 0.71773442438,
                 9.7: 0.717734425576,
                 9.8: 0.71773442658,
                 9.9: 0.717734427424,
                 10: 0.717734428132}
    from test_models.test_trend import simulation_model
    sim = simulation_model()

    assert sim.dt == 0.1
    assert sim.starttime == 1
    assert sim.stoptime == 10

    for i in np.arange(sim.starttime, sim.stoptime, sim.dt):
        i = round(i, 1)
        assert round(sim.equation('trendOfInputFunction', i), 3) == round(test_data[i], 3)



def test_smooth():
    """
    SMTH1
    :return:
    """
    from test_models.test_smooth import simulation_model
    sim = simulation_model()
    assert sim.dt == 0.1
    assert sim.starttime == 1
    assert sim.stoptime == 10

    for i in np.arange(sim.starttime, sim.stoptime, sim.dt):
        assert sim.equation('exponentialAverage', i) == sim.equations['smooth'](i)



def test_abs():
    """
    ABS(x)
    :return:
    """
    import numpy as np
    import os
    from test_models.test_abs import simulation_model
    sim = simulation_model()
    assert sim.dt == 0.25
    assert sim.starttime == 1
    assert sim.stoptime == 61

    assert sum([sim.equation("stock1", t) for t in np.arange(sim.starttime, sim.stoptime, sim.dt)]) == (
            sim.stoptime - 1) * (1 / sim.dt) * 100



def test_dt_fraction():
    """
    DT as fraction (1/4)
    :return:
    """
    from test_models.test_dt_fraction import simulation_model
    sim = simulation_model()
    assert sim.dt == 0.25
    assert sim.starttime == 1
    assert sim.stoptime == 61


def test_dt_rational():
    """
    DT rational
    :return:
    """
    from test_models.test_dt_rational import simulation_model
    sim = simulation_model()
    assert sim.dt == 0.25
    assert sim.starttime == 1
    assert sim.stoptime == 61


def test_expressions():

    from test_models.test_expressions import simulation_model
    sim = simulation_model()

    assert sim.dt == 0.25
    assert sim.starttime == 1
    assert sim.stoptime == 13

    for t in np.arange(sim.starttime, sim.stoptime, sim.dt):
        assert sim.equation("diffEsf", t) == 0.0
        assert sim.equation("diffExpression", t) == 0.0
        assert sim.equation("diffDifficultNames", t) == 0.0


def test_no_dimensions():
    """
    Simple model without dimensions.
    :return:
    """
    from test_models.test_no_dimensions import simulation_model
    sim = simulation_model()
    assert sim.dt == 0.25
    assert sim.starttime == 1
    assert sim.stoptime == 61


def test_time():
    """
    TIME
    :return:
    """
    from test_models.test_time import simulation_model
    sim = simulation_model()
    assert sim.dt == 0.25
    assert sim.starttime == 1
    assert sim.stoptime == 61


def test_cos():
    """
    COS(X)
    :return:
    """
    import numpy as np
    import os
    from test_models.test_cos import simulation_model
    sim = simulation_model()
    assert sim.dt == 0.25
    assert sim.starttime == 1
    assert sim.stoptime == 61

    for t in np.arange(sim.starttime, sim.stoptime, sim.dt):
        assert sim.equation("stock1", t) == np.cos(1.0)


def test_tan():
    """
    TAN(x)
    :return:
    """
    import numpy as np
    import os
    from test_models.test_tan import simulation_model
    sim = simulation_model()
    assert sim.dt == 0.25
    assert sim.starttime == 1
    assert sim.stoptime == 61

    for t in np.arange(sim.starttime, sim.stoptime, sim.dt):
        assert sim.equation("stock1", t) == np.tan(1.0)


def test_sim_builtins():
    """
    DT, starttime, stoptime
    :return:
    """
    import numpy as np
    import os
    from test_models.test_sim_builtins import simulation_model
    sim = simulation_model()
    assert sim.dt == 0.25
    assert sim.starttime == 1
    assert sim.stoptime == 61

    for t in np.arange(sim.starttime, sim.stoptime, sim.dt):
        assert sim.equation("p", t) == np.pi
        assert sim.equation("start", t) == sim.starttime
        assert sim.equation("stop", t) == sim.stoptime


def test_random():
    '''
    Random and Random with seed
    :return:
    '''
    import numpy as np
    import os
    from test_models.test_random import simulation_model
    sim = simulation_model()
    assert sim.dt == 0.25
    assert sim.starttime == 1
    assert sim.stoptime == 61

    for t in np.arange(sim.starttime, sim.stoptime, sim.dt):
        val_btw_0_10 = sim.equation('rndBetween0And10', t)
        x = sim.equation("uni", t)
        y = sim.equation("uniNoseed", t)

        assert val_btw_0_10 < 10 and val_btw_0_10 > 0
        assert sim.equation("rnd", t) == 1
        assert sim.equation("rndSeed", t) == 1
        assert x >= sim.equation("mini", t) and x <= sim.equation("maxi", t)
        assert y >= sim.equation("mini", t) and y <= sim.equation("maxi", t)


def test_step():
    import numpy as np
    import os
    from test_models.test_step import simulation_model
    sim = simulation_model()
    assert sim.dt == 0.25
    assert sim.starttime == 1
    assert sim.stoptime == 13

    for t in np.arange(sim.starttime, sim.stoptime, sim.dt):
        assert sim.equation("function", t) == 100.0 if t < 4.0 else sim.equation("function", t) == 150



def test_delay():
    import numpy as np
    import os
    from test_models.test_delay import simulation_model
    sim = simulation_model()
    assert sim.dt == 0.25
    assert sim.starttime == 1
    assert sim.stoptime == 13

    for t in np.arange(sim.starttime, sim.stoptime, sim.dt):
        assert sim.equation("function", t) == 100.0 if t < 5.0 else sim.equation("function", t) == 150



def test_if():
    import numpy as np
    import os
    from test_models.test_if import simulation_model
    sim = simulation_model()
    assert sim.dt == 0.25
    assert sim.starttime == 1
    assert sim.stoptime == 13

    for t in np.arange(sim.starttime, sim.stoptime, sim.dt):
        assert sim.equation("diffFunction", t) == 0.0
        assert sim.equation("diffNestedIf",t) == 0.0
        assert sim.equation("diffCapacityIncrease",t) == 0.0
        assert sim.equation("diffLimit",t) == 0.0
        assert sim.equation("diffAtomIf", t) == 0.0
        assert sim.equation("diffCapacitySufficiency", t) == 0.0


def test_array():
    expected_result = {1.0: 0.0,
                       1.25: 0.25,
                       1.5: 0.5,
                       1.75: 0.75,
                       2.0: 1.0,
                       2.25: 1.25,
                       2.5: 1.5,
                       2.75: 1.75,
                       3.0: 2.0,
                       3.25: 2.25,
                       3.5: 2.5,
                       3.75: 2.75,
                       4.0: 3.0,
                       4.25: 3.25,
                       4.5: 3.5,
                       4.75: 3.75,
                       5.0: 4.0,
                       5.25: 4.25,
                       5.5: 4.5,
                       5.75: 4.75,
                       6.0: 5.0,
                       6.25: 5.25,
                       6.5: 5.5,
                       6.75: 5.75,
                       7.0: 6.0,
                       7.25: 6.25,
                       7.5: 6.5,
                       7.75: 6.75,
                       8.0: 7.0,
                       8.25: 7.25,
                       8.5: 7.5,
                       8.75: 7.75,
                       9.0: 8.0,
                       9.25: 8.25,
                       9.5: 8.5,
                       9.75: 8.75,
                       10.0: 9.0,
                       10.25: 9.25,
                       10.5: 9.5,
                       10.75: 9.75,
                       11.0: 10.0,
                       11.25: 10.25,
                       11.5: 10.5,
                       11.75: 10.75,
                       12.0: 11.0,
                       12.25: 11.25,
                       12.5: 11.5,
                       12.75: 11.75,
                       13.0: 12.0}
    import numpy as np
    result = {}
    from test_models.test_array import simulation_model
    mod = simulation_model()
    for t in np.arange(1, 13 + 0.25, 0.25):
        result[t] = mod.equations["stock[1]"](t)
        assert mod.equation("inflow[1]", t) == 1
        assert mod.equation("inflow[2]", t) == 2
        assert mod.equation("inflow[3]", t) == 3
        assert sum(mod.equation("inflow[*]", t)) == 6
        #assert mod.equation("inflow[1:3,2,1]", t) == 9

    assert result == expected_result

def test_array_extended():
    from test_models.test_array_extended import simulation_model
    from numpy import arange

    sim = simulation_model()
    dt = sim.dt
    starttime = sim.starttime
    stoptime = sim.stoptime

    min_expected_results = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5, 3.75, 4.0, 4.25, 4.5, 4.75, 5.0, 5.25, 5.5, 5.75, 6.0, 6.25, 6.5, 6.75, 7.0, 7.25, 7.5, 7.75, 8.0, 8.25, 8.5, 8.75, 9.0, 9.25, 9.5, 9.75, 10.0, 10.25, 10.5, 10.75, 11.0, 11.25, 11.5, 11.75, 12.0]
    max_expected_results = [0.0,  0.75,1.5,  2.25, 3.0,3.75, 4.5, 5.25, 6.0, 6.75, 7.5, 8.25, 9.0, 9.75, 10.5, 11.25, 12.0,12.75, 13.5,  14.25,  15.0, 15.75,  16.5, 17.25, 18.0, 18.75, 19.5,20.25, 21.0, 21.75,22.5, 23.25,24.0,24.75,25.5, 26.25,27.0, 27.75, 28.5,29.25,  30.0,30.75, 31.5, 32.25,33.0, 33.75, 34.5,35.25,36.0]
    mean_expected_results = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0, 13.5, 14.0, 14.5, 15.0, 15.5, 16.0, 16.5, 17.0, 17.5, 18.0, 18.5, 19.0, 19.5, 20.0, 20.5, 21.0, 21.5, 22.0, 22.5, 23.0, 23.5, 24.0]
    array_expected_results = {'germany': [0.0, 1.25, 2.5, 3.75, 5.0, 6.25, 7.5, 8.75, 10.0, 11.25, 12.5, 13.75, 15.0, 16.25, 17.5, 18.75, 20.0, 21.25, 22.5, 23.75, 25.0, 26.25, 27.5, 28.75, 30.0, 31.25, 32.5, 33.75, 35.0, 36.25, 37.5, 38.75, 40.0, 41.25, 42.5, 43.75, 45.0, 46.25, 47.5, 48.75, 50.0, 51.25, 52.5, 53.75, 55.0, 56.25, 57.5, 58.75, 60.0], 'england': [1.0, 3.5, 6.0, 8.5, 11.0, 13.5, 16.0, 18.5, 21.0, 23.5, 26.0, 28.5, 31.0, 33.5, 36.0, 38.5, 41.0, 43.5, 46.0, 48.5, 51.0, 53.5, 56.0, 58.5, 61.0, 63.5, 66.0, 68.5, 71.0, 73.5, 76.0, 78.5, 81.0, 83.5, 86.0, 88.5, 91.0, 93.5, 96.0, 98.5, 101.0, 103.5, 106.0, 108.5, 111.0, 113.5, 116.0, 118.5, 121.0], 'austria': [3.0, 6.75, 10.5, 14.25, 18.0, 21.75, 25.5, 29.25, 33.0, 36.75, 40.5, 44.25, 48.0, 51.75, 55.5, 59.25, 63.0, 66.75, 70.5, 74.25, 78.0, 81.75, 85.5, 89.25, 93.0, 96.75, 100.5, 104.25, 108.0, 111.75, 115.5, 119.25, 123.0, 126.75, 130.5, 134.25, 138.0, 141.75, 145.5, 149.25, 153.0, 156.75, 160.5, 164.25, 168.0, 171.75, 175.5, 179.25, 183.0], 'greece': [4.0, 9.0, 14.0, 19.0, 24.0, 29.0, 34.0, 39.0, 44.0, 49.0, 54.0, 59.0, 64.0, 69.0, 74.0, 79.0, 84.0, 89.0, 94.0, 99.0, 104.0, 109.0, 114.0, 119.0, 124.0, 129.0, 134.0, 139.0, 144.0, 149.0, 154.0, 159.0, 164.0, 169.0, 174.0, 179.0, 184.0, 189.0, 194.0, 199.0, 204.0, 209.0, 214.0, 219.0, 224.0, 229.0, 234.0, 239.0, 244.0]}
    stddev_expected_results = [0.0, 0.2041241452319315, 0.408248290463863, 0.6123724356957945, 0.816496580927726, 1.0206207261596576, 1.224744871391589, 1.4288690166235205, 1.632993161855452, 1.8371173070873836, 2.041241452319315, 2.2453655975512468, 2.449489742783178, 2.6536138880151094, 2.857738033247041, 3.0618621784789726, 3.265986323710904, 3.4701104689428357, 3.6742346141747673, 3.8783587594066984, 4.08248290463863, 4.286607049870562, 4.4907311951024935, 4.694855340334425, 4.898979485566356, 5.103103630798288, 5.307227776030219, 5.5113519212621505, 5.715476066494082, 5.919600211726014, 6.123724356957945, 6.327848502189877, 6.531972647421808, 6.73609679265374, 6.940220937885671, 7.144345083117603, 7.3484692283495345, 7.552593373581465, 7.756717518813397, 7.960841664045329, 8.16496580927726, 8.369089954509192, 8.573214099741124, 8.777338244973055, 8.981462390204987, 9.185586535436919, 9.38971068066885, 9.593834825900782, 9.797958971132712]
    sum_expected_results = [0.0, 1.5, 3.0, 4.5, 6.0, 7.5, 9.0, 10.5, 12.0, 13.5, 15.0, 16.5, 18.0, 19.5, 21.0, 22.5, 24.0, 25.5, 27.0, 28.5, 30.0, 31.5, 33.0, 34.5, 36.0, 37.5, 39.0, 40.5, 42.0, 43.5, 45.0, 46.5, 48.0, 49.5, 51.0, 52.5, 54.0, 55.5, 57.0, 58.5, 60.0, 61.5, 63.0, 64.5, 66.0, 67.5, 69.0, 70.5, 72.0]
    prod_expected_results = [0.0, 0.09375, 0.75, 2.53125, 6.0, 11.71875, 20.25, 32.15625, 48.0, 68.34375, 93.75, 124.78125, 162.0, 205.96875, 257.25, 316.40625, 384.0, 460.59375, 546.75, 643.03125, 750.0, 868.21875, 998.25, 1140.65625, 1296.0, 1464.84375, 1647.75, 1845.28125, 2058.0, 2286.46875, 2531.25, 2792.90625, 3072.0, 3369.09375, 3684.75, 4019.53125, 4374.0, 4748.71875, 5144.25, 5561.15625, 6000.0, 6461.34375, 6945.75, 7453.78125, 7986.0, 8542.96875, 9125.25, 9733.40625, 10368.0]

    max_results = [sim.equation("maxconverter",t) for t in arange(starttime,stoptime+dt,dt)]
    min_results = [sim.equation("minconverter", t) for t in arange(starttime, stoptime + dt, dt)]
    mean_results = [sim.equation("meanconverter",t) for t in arange(starttime,stoptime+dt,dt)]
    stddev_results = [round(sim.equation("stddevconverter",t),3)for t in arange(starttime,stoptime+dt,dt)] # 3 digits accuracy required
    sum_results = [sim.equation("sumconverter",t) for t in arange(starttime,stoptime+dt,dt)]
    prod_results = [round(sim.equation("prodconverter",t),3) for t in arange(starttime,stoptime+dt,dt)] # 3 digits accuracy required



    array_results = {"germany": [], "england": [], "austria": [], "greece": []}
    for i in arange(starttime, stoptime + dt, dt):
        array_results["germany"] += [sim.equation("countryStock[germany]", i)]
        array_results["england"] += [sim.equation("countryStock[england]", i)]
        array_results["austria"] += [sim.equation("countryStock[austria]", i)]
        array_results["greece"] += [sim.equation("countryStock[greece]", i)]
        assert sim.equation("sizeconverter", i) == 4


    assert max_expected_results == max_results
    assert min_expected_results == min_results
    assert mean_expected_results == mean_results
    assert array_expected_results == array_results
    assert [round(x,3) for x in stddev_expected_results] == stddev_results
    assert sum_expected_results == sum_results
    assert [round(x,3) for x in prod_expected_results] == prod_results


def test_array_2dimensional():
    from test_models.test_array_2dimensional import simulation_model
    from numpy import arange

    sim = simulation_model()
    dt = sim.dt
    starttime = sim.starttime
    stoptime = sim.stoptime

    rankinv_expected_results = [1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
    smallestinventory_expected_results = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0]
    largestinventory_expected_results = [0.0, 0.0, 0.0, 0.0, 0.0, 2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 17.5, 20.0, 22.5, 25.0, 27.5, 30.0, 32.5, 35.0, 37.5, 40.0, 42.5, 45.0, 47.5, 50.0, 52.5, 60.0, 70.0, 80.0, 90.0, 100.0, 110.0, 120.0, 130.0, 140.0, 150.0, 160.0, 170.0, 180.0, 190.0, 200.0, 210.0, 220.0, 230.0, 240.0, 250.0, 260.0, 270.0, 280.0]
    totalinventory_expected_results = [0.0, 0.0, 0.0, 0.0, 0.0, 2.5, 5.0, 7.5, 10.0, 17.5, 25.0, 32.5, 40.0, 55.0, 70.0, 85.0, 100.0, 125.0, 150.0, 175.0, 200.0, 235.0, 270.0, 305.0, 340.0, 382.5, 425.0, 467.5, 510.0, 555.0, 600.0, 645.0, 690.0, 740.0, 790.0, 840.0, 890.0, 945.0, 1000.0, 1055.0, 1110.0, 1172.5, 1235.0, 1297.5, 1360.0, 1432.5, 1505.0, 1577.5, 1650.0]
    avginventory_expected_results = [0.0, 0.0, 0.0, 0.0, 0.0, 0.20833333333333334, 0.4166666666666667, 0.625, 0.8333333333333334, 1.4583333333333333, 2.0833333333333335, 2.7083333333333335, 3.3333333333333335, 4.583333333333333, 5.833333333333333, 7.083333333333333, 8.333333333333334, 10.416666666666666, 12.5, 14.583333333333334, 16.666666666666668, 19.583333333333332, 22.5, 25.416666666666668, 28.333333333333332, 31.875, 35.416666666666664, 38.958333333333336, 42.5, 46.25, 50.0, 53.75, 57.5, 61.666666666666664, 65.83333333333333, 70.0, 74.16666666666667, 78.75, 83.33333333333333, 87.91666666666667, 92.5, 97.70833333333333, 102.91666666666667, 108.125, 113.33333333333333, 119.375, 125.41666666666667, 131.45833333333334, 137.5]
    germanInventory_expected = [0.0, 0.0, 0.0, 0.0, 0.0, 2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 17.5, 20.0, 22.5, 25.0, 27.5,
                                30.0, 32.5, 35.0, 37.5, 40.0, 52.5, 65.0, 77.5, 90.0, 102.5, 115.0, 127.5, 140.0, 152.5,
                                165.0, 177.5, 190.0, 202.5, 215.0, 227.5, 240.0, 257.5, 275.0, 292.5, 310.0, 327.5,
                                345.0, 362.5, 380.0, 397.5, 415.0, 432.5, 450.0]
    smallestGermanInventory_expected = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                        0.0, 0.0, 0.0, 0.0, 0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0,
                                        50.0, 55.0, 60.0]
    largestGermanInventory_expected = [0.0, 0.0, 0.0, 0.0, 0.0, 2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 17.5, 20.0, 22.5, 25.0,
                                       27.5, 30.0, 32.5, 35.0, 37.5, 40.0, 42.5, 45.0, 47.5, 50.0, 52.5, 60.0, 70.0,
                                       80.0, 90.0, 100.0, 110.0, 120.0, 130.0, 140.0, 150.0, 160.0, 170.0, 180.0, 190.0,
                                       200.0, 210.0, 220.0, 230.0, 240.0, 250.0, 260.0, 270.0, 280.0]

    avginventory_results = [round(sim.equation('averageInventory', t),3) for t in arange(starttime, stoptime + dt, dt)]
    avginventoryusingsize_results = [round(sim.equation('averageInventoryUsingSize', t), 3) for t in arange(starttime, stoptime + dt, dt)]
    totalinventory_results = [round(sim.equation('totalInventory', t),3) for t in arange(starttime, stoptime + dt, dt)]
    largestinventory_results = [sim.equation('largestGermanInventory', t) for t in arange(starttime, stoptime + dt, dt)]
    smallestinventory_results = [sim.equation('smallestGermanInventory', t) for t in arange(starttime, stoptime + dt, dt)]
    rankinv_results = [sim.equation('rankinv', t) for t in arange(starttime, stoptime + dt, dt)]

    germanInventory = []
    countryInventory_germany = []
    countryInventoryIndiviudual_germany = []
    smallestGermanInventory = []
    largestGermanInventory = []
    for t in arange(sim.starttime, sim.stoptime+dt, dt):
        germanInventory += [sim.memoize("germanInventory",t)]
        countryInventory_germany += [sim.memoize("countryInventory[germany]",t)]
        countryInventoryIndiviudual_germany += [sim.memoize("countryInventoryIndiviudual[germany]",t)]
        smallestGermanInventory += [sim.memoize("smallestGermanInventory",t)]
        largestGermanInventory += [sim.memoize("largestGermanInventory",t)]


    assert countryInventory_germany == germanInventory_expected
    assert germanInventory == germanInventory_expected
    assert countryInventoryIndiviudual_germany  == germanInventory_expected
    assert smallestGermanInventory == smallestGermanInventory_expected
    assert largestGermanInventory == largestGermanInventory_expected

    assert [round(x,3) for x in avginventory_expected_results] == avginventory_results == avginventoryusingsize_results
    assert totalinventory_results == totalinventory_expected_results
    assert largestinventory_expected_results == largestinventory_results
    assert smallestinventory_expected_results == smallestinventory_results
    assert rankinv_expected_results == rankinv_results

    for t in arange(sim.starttime, sim.stoptime + sim.dt, sim.dt):
        assert sim.memoize('productionDuration[1,germany]', t) == 1
        assert sim.memoize('productionDuration[1,england]', t) == 2
        assert sim.memoize('productionDuration[1,austria]', t) == 3
        assert sim.memoize('productionDuration[1,greece]', t) == 4
        assert sim.memoize('productionDuration[2,germany]', t) == 5
        assert sim.memoize('productionDuration[2,england]', t) == 6
        assert sim.memoize('productionDuration[2,austria]', t) == 8
        assert sim.memoize('productionDuration[2,greece]', t) == 7
        assert sim.memoize('productionDuration[3,germany]', t) == 9
        assert sim.memoize('productionDuration[3,england]', t) == 10
        assert sim.memoize('productionDuration[3,austria]', t) == 11
        assert sim.memoize('productionDuration[3,greece]', t) == 12


def test_arrray_3dimensional():
    from test_models.test_array_3dimensional import simulation_model
    sim = simulation_model()

    for t in np.arange(sim.starttime,sim.stoptime,sim.dt):
        assert sim.equation("diffRelInventory", t) == 0.0
        assert sim.equation("diffAverageInventory", t) == 0.0
        assert sim.equation("diffCountryInventory", t) == 0.0
        assert sim.equation("diffRankinv", t) == 0.0
        assert sim.equation("diffArrayArithmetic", t) == 0.0
        assert sim.equation("sumArrayedInput", t) == 70.0
        assert sim.equation("sumNonarrayedIndividual", t) == 70.0
        assert sim.equation("sumNonarrayedApplyToAll", t) == 70.0
        assert sim.equation("sumNonarrayedApplyToAll3d", t) == 360.0
        assert sim.equation("arrayProduct", t) == 1.0


def test_counter_his():
    from test_models.test_clocktime import simulation_model

    sim = simulation_model()
    dt = sim.dt
    starttime = sim.starttime
    stoptime = sim.stoptime

    counter_expected_result = [1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5, 3.75, 4.0, 4.25, 4.5, 4.75, 5.0, 5.25, 5.5, 5.75, 6.0, 6.25, 6.5, 6.75, 7.0, 7.25, 7.5, 7.75, 0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5, 3.75, 4.0, 4.25, 4.5, 4.75, 5.0, 5.25, 5.5, 5.75, 6.0]

    import numpy as np
    result_counter = []
    for t in np.arange(starttime, stoptime + dt, dt):
        result_counter += [sim.equation("ctr", t)]
        assert sim.equation("ctrtarget",t-dt) == sim.equation("his",t)

    assert result_counter == counter_expected_result


def test_npv():
    from test_models.test_npv import simulation_model
    import numpy as np

    sim = simulation_model()
    dt = sim.dt
    starttime = sim.starttime
    stoptime = sim.stoptime

    npv_expected_result = [10.0, 11.9, 13.343, 14.44, 15.273, 15.906, 16.387, 16.753, 17.031, 17.242, 17.402, 17.524, 17.617, 17.687, 17.74, 17.781, 17.812, 17.835, 17.853, 17.867, 17.877, 17.885, 17.891, 17.895, 17.899, 17.901, 17.903, 17.905, 17.906, 17.907, 17.907, 17.908, 17.908, 17.909, 17.909, 17.909, 17.909, 17.909, 17.909, 17.909, 17.909, 17.909, 17.909, 17.909, 17.909, 17.91, 17.91, 17.91, 17.91]

    result_npv = []
    for t in np.arange(starttime, stoptime + dt, dt):
        result_npv += [round(sim.equation('netpresentvalue', t),3)]

    assert result_npv == npv_expected_result


def test_financials():
    from test_models.test_financials import simulation_model
    import numpy as np

    sim = simulation_model()
    dt = sim.dt
    starttime = sim.starttime
    stoptime = sim.stoptime

    for t in np.arange(starttime, stoptime + dt, dt):
        assert round(sim.equation('monthlyPayment', t), 3) == -332.143
        assert round(sim.equation('futureValue', t), 3) == 14307.688
        assert sim.equation('presentValue',t) == 10000
        assert np.isnan(sim.equation("na",t))

    assert round(sim.equation('internalRateOfReturn', sim.stoptime),2) == 0.08



def test_percent():
    from test_models.test_percent import simulation_model
    import numpy as np

    sim = simulation_model()
    dt = sim.dt
    starttime = sim.starttime
    stoptime = sim.stoptime


    for t in np.arange(starttime, stoptime + dt, dt):
        assert sim.equation('percentage', t) == 80.0


def test_sqrt():
    from test_models.test_sqrt import simulation_model
    import numpy as np

    sim = simulation_model()
    dt = sim.dt
    starttime = sim.starttime
    stoptime = sim.stoptime

    for t in np.arange(starttime, stoptime + dt, dt):
        assert sim.equation('sqr', t) == 12.0


def test_log10():
    from test_models.test_log10 import simulation_model
    import numpy as np

    sim = simulation_model()
    dt = sim.dt
    starttime = sim.starttime
    stoptime = sim.stoptime

    for t in np.arange(starttime, stoptime + dt, dt):
        assert sim.equation('lo10', t) == 5.0
        assert round(sim.equation('logn', t),3) == 11.513


def test_permutation():
    from test_models.test_permutation import simulation_model
    import numpy as np

    sim = simulation_model()
    dt = sim.dt
    starttime = sim.starttime
    stoptime = sim.stoptime

    for t in np.arange(starttime, stoptime + dt, dt):
        assert sim.equation('p', t) == 60
        assert sim.equation('perm', t) ==  60 if t== starttime else 60 * ((t-starttime)/dt)



def test_forcst():
    from test_models.test_forecast import simulation_model
    import numpy as np

    sim = simulation_model()
    dt = sim.dt
    starttime = sim.starttime
    stoptime = sim.stoptime

    forcst_expected = [49.00000000000001, 25.51063829787234, 17.68557634278817, 13.776586117261964, 11.434020996133743, 9.874664590154426, 8.762852010285311, 7.930750184577448, 7.285117964503175, 6.770010168112645, 6.349824872933841, 6.000827062921056, 5.706584438798756, 5.455359310091451, 5.238543730707643, 5.049681459011136, 4.8838351087554575, 4.737164249978474, 4.6066367414391625, 4.489826663545289, 4.384769984930351, 4.289859592871119, 4.203767707235527, 4.12538769108715, 4.053789826871965, 3.9881872982127033, 3.9279097314025906, 3.872382406663984, 3.821109770598607, 3.7736622462089677, 3.729665595869392, 3.6887922787805296, 3.6507543798270183, 3.6152977863063773, 3.5821973629474657, 3.5512529310995875, 3.5222858999450892, 3.495136429619473, 3.4696610307623477, 3.4457305241180927]

    lis = []
    for t in np.arange(starttime, stoptime + dt, dt):
        lis += [sim.equation('forecast', t)]

    assert [np.isnan(x) for x in lis[0:8]]
    for i, forecast in enumerate(lis[9:]):
        assert forecast == forcst_expected[i]


def test_triangular():
    from test_models.test_triangular import simulation_model
    sim = simulation_model()

    starttime = sim.starttime
    stoptime = sim.stoptime
    dt = sim.dt

    for t in np.arange(starttime, stoptime + dt, dt):
        x = sim.equation("tri", t)
        y = sim.equation("triNoseed", t)
        assert x >= sim.equation("left", t) and x <= sim.equation("right", t)
        assert y >= sim.equation("left", t) and y <= sim.equation("right", t)


def test_endval():
    from test_models.test_endval import simulation_model
    sim = simulation_model()

    starttime = sim.starttime
    stoptime = 10000
    dt = sim.dt

    assert sim.equation("end", 1) == 1.0
    assert sim.equation("endWithoutInitial", 1) == 0.25

    for t in np.arange(starttime, stoptime + dt, dt):
        sim.equation("somecon", t)

    assert sim.equation("end", 10) == 3.25
    assert sim.equation("endWithoutInitial", 10) == 3.25


def test_negbinomial():
    from test_models.test_negbinomial import simulation_model
    sim = simulation_model()

    x = []
    y = []
    for t in range(0, 100000):
        x += [sim.equation('withoutseed', t)]
        y += [sim.equation('withseed', t)]

    assert np.mean(x) >= 88000 and np.mean(x) <= 91000 # Mean should be 90k


def test_lookup():
    import numpy as np
    from test_models.test_lookup import simulation_model
    sim = simulation_model()

    starttime = sim.starttime
    stoptime = sim.stoptime
    dt = sim.dt

    x = []
    y = []
    for t in np.arange(starttime, stoptime + dt, dt):
        assert sim.equation('look', t) == 41
        assert sim.equation("inv", t) == 7.5


def test_lookuparea():
    import numpy as np
    from test_models.test_lookuparea import simulation_model
    sim = simulation_model()

    starttime = sim.starttime
    stoptime = sim.stoptime
    dt = sim.dt

    expected_results = [0.0, 12.625, 25.25, 37.875, 50.5, 63.125, 75.75, 88.375, 101.0, 113.616, 126.212, 138.791,
                        151.35, 163.9, 176.45, 189.0, 201.55, 214.1, 226.65, 239.2, 251.75, 265.353, 281.063, 298.878,
                        318.8, 339.55, 359.85, 379.7, 399.1, 418.147, 436.938, 455.472, 473.75, 491.9, 510.05, 528.2,
                        546.35, 564.488, 582.6, 600.687, 618.75, 636.712, 654.5, 672.112, 689.55, 706.534, 722.787,
                        738.309, 753.1]
    results = []

    for t in np.arange(starttime, stoptime + dt, dt):
        results += [round(sim.equation('area', t), 3)]

    assert results == expected_results


def test_poisson():
    import numpy as np
    from test_models.test_poisson import simulation_model
    sim = simulation_model()

    starttime = sim.starttime
    stoptime = sim.stoptime
    dt = sim.dt

    for t in np.arange(starttime, stoptime + dt, dt):
        val = sim.equation("withseed", t)
        assert val >= 0 and val % 1 == 0
        val = sim.equation("withoutseed", t)
        assert val >= 0 and val % 1 == 0


def test_ramp():
    import numpy as np
    from test_models.test_ramp import simulation_model
    sim = simulation_model()

    starttime = sim.starttime
    stoptime = sim.stoptime
    dt = sim.dt
    res = []

    slope = 1
    start = 2

    def f(slope, start, t):
        if not start:
            start = starttime
        if t <= start: return 0
        return (t - start) * slope

    for t in np.arange(starttime, stoptime + dt, dt):
        assert sim.equation("ram", t)  == f(slope, start, t)
        assert sim.equation("ramNostart", t)  == f(slope, None, t)


def test_rootn():
    import numpy as np
    from test_models.test_rootn import simulation_model
    sim = simulation_model()

    starttime = sim.starttime
    stoptime = sim.stoptime
    dt = sim.dt


    for t in np.arange(starttime, stoptime + dt, dt):
        assert sim.equation("nroot", t) == -3
        assert sim.equation("nroot144", t) == 12


def test_sinwave():
    import numpy as np
    from test_models.test_sinwave import simulation_model
    sim = simulation_model()

    starttime = sim.starttime
    stoptime = sim.stoptime
    dt = sim.dt
    sinwave_res = []
    coswave_res = []
    sinwave_expected = [0.0, 3.09, 5.878, 8.09, 9.511, 10.0, 9.511, 8.09, 5.878, 3.09, 0.0, -3.09, -5.878, -8.09, -9.511, -10.0, -9.511, -8.09, -5.878, -3.09, -0.0, 3.09, 5.878, 8.09, 9.511, 10.0, 9.511, 8.09, 5.878, 3.09, 0.0, -3.09, -5.878, -8.09, -9.511, -10.0, -9.511, -8.09, -5.878, -3.09, -0.0, 3.09, 5.878, 8.09, 9.511, 10.0, 9.511, 8.09, 5.878, 3.09, 0.0, -3.09, -5.878]

    coswave_expected = [10.0, 9.511, 8.09, 5.878, 3.09, 0.0, -3.09, -5.878, -8.09, -9.511, -10.0, -9.511, -8.09, -5.878, -3.09, -0.0, 3.09, 5.878, 8.09, 9.511, 10.0, 9.511, 8.09, 5.878, 3.09, 0.0, -3.09, -5.878, -8.09, -9.511, -10.0, -9.511, -8.09, -5.878, -3.09, -0.0, 3.09, 5.878, 8.09, 9.511, 10.0, 9.511, 8.09, 5.878, 3.09, 0.0, -3.09, -5.878, -8.09, -9.511, -10.0, -9.511, -8.09]
    for t in np.arange(starttime, stoptime + dt, dt):
        sinwave_res += [round(sim.equation("wave", t), 3)]
        coswave_res += [round(sim.equation("wavecos", t), 3)]
    assert sinwave_res == sinwave_expected
    assert coswave_res == coswave_expected


def test_smth3():
    import numpy as np
    from test_models.test_smth3 import simulation_model
    sim = simulation_model()

    starttime = sim.starttime
    stoptime = sim.stoptime
    dt = sim.dt
    res = []
    smth3_expected = [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.034, 5.12, 5.266, 5.473, 5.738, 6.052,
                      6.409, 6.798, 7.212, 7.642, 8.08, 8.521, 8.958, 9.386, 9.802, 10.203, 10.587, 10.951, 11.295,
                      11.618, 11.92, 12.202, 12.463, 12.704, 12.926, 13.129, 13.316, 13.486, 13.641, 13.782, 13.91,
                      14.025, 14.13, 14.224, 14.308, 14.385, 14.453, 14.514]

    for t in np.arange(starttime, stoptime + dt, dt):
        res += [round(sim.equation("sm", t), 3)]
    assert res == smth3_expected


def test_smthn():
    import numpy as np
    from test_models.test_smthn import simulation_model
    sim = simulation_model()

    starttime = sim.starttime
    stoptime = sim.stoptime
    dt = sim.dt
    res = []
    smthn_expected = [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.01, 5.046, 5.129, 5.273, 5.489,
                      5.781, 6.146, 6.576, 7.06, 7.585, 8.135, 8.698, 9.261, 9.813, 10.346, 10.852, 11.326, 11.765,
                      12.168, 12.534, 12.863, 13.156, 13.417, 13.646, 13.847, 14.021, 14.172, 14.302, 14.414, 14.509,
                      14.59, 14.658, 14.716, 14.765, 14.806, 14.84]

    for t in np.arange(starttime, stoptime + dt, dt):
        res += [round(sim.equation("smt", t), 3)]
        assert sim.equation("in",t) == np.inf
    assert res == smthn_expected


def test_delayn():
    import numpy as np
    from test_models.test_delayn import simulation_model
    sim = simulation_model()

    starttime = sim.starttime
    stoptime = sim.stoptime
    dt = sim.dt
    res = []

    expected_result_delayn = [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.126, 5.492, 6.133,
                              7.005, 8.023, 9.092, 10.131, 11.084, 11.917, 12.619, 13.193, 13.649, 14.004, 14.275,
                              14.478, 14.628, 14.737, 14.816, 14.872, 14.912, 14.94, 14.959, 14.972, 14.981, 14.987,
                              14.992, 14.994, 14.996, 14.998, 14.998, 14.999, 14.999, 15.0, 15.0, 15.0, 15.0]
    expected_result_delay3 = [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.156, 5.508, 6.035, 6.694, 7.436,
                              8.215, 8.993, 9.744, 10.448, 11.093, 11.674, 12.189, 12.639, 13.029, 13.363, 13.647,
                              13.887, 14.087, 14.255, 14.394, 14.508, 14.602, 14.679, 14.742, 14.793, 14.834, 14.867,
                              14.894, 14.916, 14.933, 14.947, 14.958, 14.967, 14.974, 14.979, 14.984, 14.987, 14.99]
    expected_result_delay1 = [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.833, 6.597, 7.297, 7.939, 8.528, 9.067,
                              9.561, 10.015, 10.43, 10.811, 11.16, 11.48, 11.773, 12.042, 12.289, 12.515, 12.722,
                              12.912, 13.086, 13.245, 13.391, 13.525, 13.648, 13.761, 13.864, 13.959, 14.046, 14.125,
                              14.198, 14.265, 14.326, 14.382, 14.434, 14.481, 14.524, 14.564, 14.6, 14.634, 14.664,
                              14.692]

    result_delayn = []
    result_delay3 = []
    result_delay1 = []

    for t in np.arange(sim.starttime, sim.stoptime + sim.dt, sim.dt):
        result_delay1 += [round(sim.equation("de1", t), 3)]
        result_delayn += [round(sim.equation("den", t), 3)]
        result_delay3 += [round(sim.equation("de3", t), 3)]

    assert expected_result_delayn == result_delayn
    assert expected_result_delay3 == result_delay3
    assert expected_result_delay1 == result_delay1


def test_weibull():
    import numpy as np
    from test_models.test_weibull import simulation_model
    sim = simulation_model()

    starttime = sim.starttime
    stoptime = sim.stoptime
    dt = sim.dt

    distseed_results_run1 = []
    distseed_results_run2 = []
    noseed_results = []

    for t in np.arange(starttime, stoptime + dt, dt):
        assert sim.equation("zeroscale", t) == .0
        distseed_results_run1 += [sim.equation("distseed", t)]

    sim = simulation_model()

    for t in np.arange(starttime, stoptime + dt, dt):
        assert sim.equation("zeroscale", t) == .0
        distseed_results_run2 += [sim.equation("distseed", t)]

    sim = simulation_model()
    for t in np.arange(starttime, stoptime + dt, dt):
        assert sim.equation("zeroscale", t) == .0
        noseed_results += [sim.equation("dist", t)]

    assert distseed_results_run2 == distseed_results_run1
    assert np.mean(distseed_results_run1) >= 9.4 and np.mean(distseed_results_run1) <= 10
    assert np.mean(noseed_results) >= 9.4 and np.mean(noseed_results) <= 10
    assert np.min(distseed_results_run1) >= 5 and np.min(noseed_results) >= 5


def test_pareto():
    import numpy as np
    from test_models.test_pareto import simulation_model
    sim = simulation_model()

    starttime = sim.starttime
    stoptime = sim.stoptime
    dt = sim.dt

    distseed_results_run1 = []
    distseed_results_run2 = []
    noseed_results = []

    for t in np.arange(starttime, stoptime + dt, dt):
        assert np.isnan(sim.equation("zeroscale", t))
        distseed_results_run1 += [sim.equation("distseed", t)]

    sim = simulation_model()

    for t in np.arange(starttime, stoptime + dt, dt):
        assert np.isnan(sim.equation("zeroscale", t))
        distseed_results_run2 += [sim.equation("distseed", t)]

    sim = simulation_model()
    for t in np.arange(starttime, stoptime + dt, dt):
        assert np.isnan(sim.equation("zeroscale", t))
        noseed_results += [sim.equation("dist", t)]

    assert distseed_results_run2 == distseed_results_run1

def test_cgrowth():
    import os

    src = "./test_models/test_cgrowth.stmx"
    dest = "./test_models/test_cgrowth.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import numpy as np
    from test_models.test_cgrowth import simulation_model
    sim = simulation_model()

    starttime = sim.starttime
    stoptime = sim.stoptime
    dt = sim.dt

    for t in np.arange(starttime, stoptime + dt, dt):
        assert round(sim.equation("growthFrac", t), 3) == 0.096

        if t % 1 == 0:
            assert round(sim.equation("stock1", t), 3) == round((100 * 1.1 ** (t - 1)), 3)

def test_derivn():
    import os

    src = "./test_models/test_derivn.stmx"
    dest = "./test_models/test_derivn.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import numpy as np
    from test_models.test_derivn import simulation_model
    sim = simulation_model()

    derivn_expected_result = [0, 0, 0, 0, 0.987, 0.974, 0.9, 0.77, 0.592, 0.378, 0.14, -0.107, -0.347, -0.566, -0.749,
                              -0.886, -0.967, -0.989, -0.949, -0.85, -0.698, -0.503, -0.277, -0.033, 0.213, 0.445, 0.65,
                              0.815, 0.928, 0.984, 0.979, 0.913, 0.79, 0.618, 0.408, 0.172, -0.074, -0.316, -0.538,
                              -0.727, -0.871, -0.96, -0.99, -0.958, -0.866, -0.721, -0.531, -0.308, -0.066]
    derivn_result = []

    for t in np.arange(sim.starttime, sim.stoptime + sim.dt, sim.dt):
        derivn_result += [round(sim.equation("deriv", t), 3)]

    assert derivn_expected_result == derivn_result

def test_interpolate():
    import os

    src = "./test_models/test_interpolate.stmx"
    dest = "./test_models/test_interpolate.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import numpy as np
    from test_models.test_interpolate import simulation_model
    sim = simulation_model()

    for t in np.arange(sim.starttime, sim.stoptime + sim.dt, sim.dt):
        assert round(sim.equation("inter1", t), 3) == 17.5
        assert round(sim.equation("inter2", t), 3) == 2.5

def test_normalcdf():
    import os

    src = "./test_models/test_normalcdf.stmx"
    dest = "./test_models/test_normalcdf.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import numpy as np
    from test_models.test_normalcdf import simulation_model
    sim = simulation_model()

    expected_results = [0.0, 0.0, 0.0, 0.001, 0.001, 0.003, 0.006, 0.012, 0.023, 0.04, 0.067, 0.106, 0.159, 0.227,
                        0.309, 0.401, 0.5, 0.599, 0.691, 0.773, 0.841, 0.894, 0.933, 0.96, 0.977, 0.988, 0.994, 0.997,
                        0.999, 0.999, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                        1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                        1.0, 1.0, 1.0, 1.0]
    results = []
    for t in np.arange(sim.starttime, sim.stoptime + sim.dt, sim.dt):
        results += [sim.equation("cdf", t)]

    assert expected_results == results

def test_invnorm():
    import os

    src = "./test_models/test_invnorm.stmx"
    dest = "./test_models/test_invnorm.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    from scipy.stats import norm
    import numpy as np
    from test_models.test_invnorm import simulation_model
    sim = simulation_model()

    for t in np.arange(sim.starttime, sim.stoptime + sim.dt, sim.dt):
        if t == 0.0: assert sim.equation("inv", t) == -np.inf
        if t == 1.0: assert sim.equation("inv", t) == np.inf
        if t > 0.0 and t < 1.0:  assert sim.equation("inv", t) == norm.ppf(t)
        if t < 0.0: assert np.isnan(sim.equation("inv", t))
        if t > 1.0: assert np.isnan(sim.equation("inv", t))


def test_safediv():
    import os

    src = "./test_models/test_safediv.stmx"
    dest = "./test_models/test_safediv.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    from scipy.stats import norm
    import numpy as np
    from test_models.test_safediv import simulation_model
    sim = simulation_model()

    for t in np.arange(sim.starttime, sim.stoptime + sim.dt, sim.dt):
        assert sim.equations["stock1"](t) == 8
        assert sim.equations["stock2"](t) == 1
        assert sim.equations["converter3"](t) == 48



def test_doublequote():
    import os
    import numpy as np
    from BPTK_Py.sdcompiler.compile import compile_xmile
    src = "./test_models/test_doublequote.stmx"
    dest = "./test_models/test_doublequote.py"
    target = "py"

    compile_xmile(src, dest, target)
    assert os.path.isfile(dest)

    import numpy as np
    from test_models.test_doublequote import simulation_model
    sim = simulation_model()

    for t in np.arange(sim.starttime, sim.stoptime + sim.dt, sim.dt):
        assert sim.equation("converter(perYear)",t) == t
        assert sim.equation("otherconverter(fooBar)",t) == 2*t


def test_teardown():
    import os
    files = os.listdir("test_models/")

    for file in files:
        if file.endswith(".py"):
            os.remove("test_models/" + file)
