###########
Limitations
###########

Currently the BPTK_Py framework is geared towards our own need and has a number of limitations. We are more than happy to extend the framework to suit YOUR need, so please let us what you need so that we can prioritize our activities. You can reach us at `support@transentis.com <mailto:support@transentis.com>`_

Here are the known limitations:

* Currently the simulator only supports the Euler method, Runge-Kutta Integration is not supported.
* The SD model transpiler for XMILE models only supports stocks, flows/biflows and converters. The discrete modeling elements (such as ovens and conveyors) are not supported.
* The random number operators (LOGNORMAL, LOGISTIC etc.) support seed but uses the Python seed and random number generator as the Stella Architect random number function is not open source. Secondly, these operators only support the mandatory arguments (usually mean/scale/stddev) as given in `in the official documentation <hhttps://www.iseesystems.com/resources/help/v1-9/default.htm#08-Reference/07-Builtins/Statistical_builtins.htm>`_
* The following table gives an overview of all XMILE builtins, whether they are supported by the SD model transpiler for XMILE and their equivalent in the SD DSL library – blank cells indicate that the operator is currently not supported. We are working hard to ensure support for all operators is included ASAP. Built-ins pertaining to discrete elements are not listed.

=============  ===================  =================
Built-In       SD model transpiler  SD DSL equivalent
-------------  -------------------  -----------------
ABS            x                    abs
AND            x
ARCCOS         x
ARCSIN         x
ARCTAN         x
BETA           x
BINOMIAL       x
COMBINATIONS   x
COS            x
CGROWTH        x
CLOCKTIME      x
COUNTER        x
DELAY          x                    delay
DELAY1         x
DELAY3         x
DELAYN         x
DERIVN         x
DT             x                    dt
ELSE           x
EXP            x                    exp
EXPRND         x
ENDVAL         x
FACTORIAL      x
FORCST         x
FV             x
GAMMA          x
GAMMALN        x
GEOMETRIC      x
HISTORY        x
IF             x
INF            x
INTERPOLATE    x
INIT           x
INT            x
INVNORM        x
IRR            x
LOG10          x
LOGISTIC       x
LOGNORMAL      x
LOOKUP         x                    lookup
LOOKUPAREA     x
LOOKUPINV      x
LN             x
MAX            x                    max
MEAN           x
MIN            x                    min
MOD            x
MONTECARLO     x
NAN            x
NEGBINOMIAL    x
NORMAL         x
NORMALCDF      x
NOT            x
NPV            x
OR             x
PARETO         x
PERCENT        x
PERMUTATIONS   x
PI             x
PMT            x
POISSON        x
PREVIOUS       x
PULSE          x                    pulse
PV             x
PROD           x
RANDOM         x
RANK           x
RAMP           x
REWORK
ROUND          x
ROOTN          x
RUNCOUNT
SAFEDIV        x
SELF           x
SENSIRUNCOUNT
SIN            x
SINWAVE        x
SIZE           x
SMTH1          x                    smooth
SMTH3          x
SMTHN          x
SQRT           x
STARTTIME      x                    starttime
STDDEV         x
STEP           x                    step
STOPTIME       x                    stoptime
SUM            x
TAN            x
THEN           x
TIME           x                    time
TREND          x                    trend
TRIANGULAR     x
UNIFORM        x
WEIBULL        x
=============  ===================  =================
