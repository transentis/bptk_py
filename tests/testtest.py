import random
import os
import numpy as np
from BPTK_Py.sdcompiler.compile import compile_xmile
from BPTK_Py.sddsl.operators import BinaryOperator, ArrayedEquation
from BPTK_Py.util import timerange
from BPTK_Py import Model
from BPTK_Py import sd_functions as sd
import math
from BPTK_Py.sddsl.element import Element
from BPTK_Py.sddsl.stock import Stock


start = 0.0
dt = 1.0
stop = 10.0
model = Model(starttime=start, stoptime=stop, dt=dt, name='and')
model.fn = {
    "times2": lambda model, t: 2*t
}

x = model.flow("x")
testFunction = model.function("testFunction", lambda model, t: 2*t)
x.equation = testFunction()

for i in range(

print(model.fn)