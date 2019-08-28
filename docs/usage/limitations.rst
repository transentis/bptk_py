###########
Limitations
###########

Currently the BPTK_Py framework is geared towards our own need and has a number of limitations. We are more than happy to extend the framework to suit YOUR need, so please let us what you need so that we can prioritize our activities. You can reach us at `support@transentis.com <mailto:support@transentis.com>`_

Here are the known limitations:

* Currently the simulator only supports the Euler method, Runge-Kutta Integration is not supported.
* The SD model transpiler for XMILE models only supports stocks, flows/biflows and converters. The other modeling elements (such as ovens and conveyors) are not supported.
* The SD model transpiler for XMILE currently only supports the following builtin functions: size, stddev, sum, mean, rank, previous, abs, max, min, int, sin, cos, round, savediv, if, delay, init, normal, random, pulse, step.