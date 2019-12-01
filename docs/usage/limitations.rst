###########
Limitations
###########

Currently the BPTK_Py framework is geared towards our own need and has a number of limitations. We are more than happy to extend the framework to suit YOUR need, so please let us what you need so that we can prioritize our activities. You can reach us at `support@transentis.com <mailto:support@transentis.com>`_

Here are the known limitations:

* Currently the simulator only supports the Euler method, Runge-Kutta Integration is not supported.
* The SD model transpiler for XMILE models only supports stocks, flows/biflows and converters. The other modeling elements (such as ovens and conveyors) are not supported.
* Arrayed variables in XMILE models are not supported.
* The SD model transpiler for XMILE currently only supports the following builtin functions: abs, cos, delay, exp, if, init, int, max, mean, min, normal, previous, pulse, random, rank, round, savediv, sin, size, smth1, stddev, step, sum, trend.