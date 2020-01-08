###########
Limitations
###########

Currently the BPTK_Py framework is geared towards our own need and has a number of limitations. We are more than happy to extend the framework to suit YOUR need, so please let us what you need so that we can prioritize our activities. You can reach us at `support@transentis.com <mailto:support@transentis.com>`_

Here are the known limitations:

* Currently the simulator only supports the Euler method, Runge-Kutta Integration is not supported.
* The SD model transpiler for XMILE models only supports stocks, flows/biflows and converters. The discrete modeling elements (such as ovens and conveyors) are not supported.
* The following table gives an overview of all XMILE builtins, whether they are supported by the SD model transpiler for XMILE and their equivalent in the SD DSL library – blank cells indicate that the operator is currently not supported. We are working hard to ensure support for all operators is included ASAP. Built-ins pertaining to discrete elements are not listed.

=============  ===================  =================
Built-In       SD model transpiler  SD DSL equivalent
-------------  -------------------  -----------------
ABS            x                    abs
AND
ARCCOS         x
ARCSIN         x
ARCTAN         x
BETA           x
BINOMIAL       x
COMBINATIONS   x
COS            x
CGROWTH
CLOCKTIME      x
COUNTER        x
DELAY          x                    delay
DELAY1
DELAY3
DELAYN
DERIVN
DT             x                    dt
ELSE           x
EXP            x                    exp
EXPRND         x
ENDVAL
FACTORIAL      x
FORCST
FV
GAMMA          x
GAMMALN        x
GEOMETRIC      x
HISTORY        x
IF             x
INF
INTERPOLATE
INIT           x
INT            x
INVNORM
IRR
LOG10
LOGISTIC
LOGNORMAL
LOOKUP         x                    lookup
LOOKUPAREA
LOOKUPINV
LN
MAX            x                    max
MEAN           x
MIN            x                    min
MOD            x
MONTECARLO
NAN
NEGBINOMIAL
NORMAL         x
NORMALCDF
NOT
NPV
OR             x
PARETO
PERCENT
PERMUTATIONS
PI             x
PMT
POISSON
PREVIOUS       x
PULSE          x                    pulse
PV
PROD           x
RANDOM         x
RANK           x
RAMP
REWORK
ROUND          x
ROOTN
RUNCOUNT
SAFEDIV        x
SELF           x
SENSIRUNCOUNT
SIN            x
SINWAVE
SIZE           x
SMTH1          x                    smooth
SMTH3
SMTHN
SQRT
STARTTIME      x                    starttime
STDDEV         x
STEP           x                    step
STOPTIME       x                    stoptime
SUM            x
TAN            x
THEN           x
TIME           x                    time
TREND          x                    trend
TRIANGULAR
UNIFORM
WEIBULL
=============  ===================  =================
