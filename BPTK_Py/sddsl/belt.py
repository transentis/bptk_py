#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2026 transentis labs GmbH
# MIT License

"""The belt of a conveyor: what lies on it, and how one timestep moves it.

Nothing here knows about models. A belt is a list of cohorts - the material that entered
in one timestep - and `advance` takes the inputs of one step and returns the belt of the
next, with what left it at the front and through each leakage.

Two belts, as in Stella:

- **Traditional** (not FIFO): a cohort enters at a depth of `round(transit / dt)` slats
  and moves one slat per timestep. When the transit time shrinks, new material can
  overtake older material.
- **FIFO**: the belt has length 1 and moves `dt / transit` per timestep, at the transit
  time of the moment. A cohort covers `dt / transit` of it when it enters. Nothing
  overtakes; a shorter transit time speeds up the whole belt.

With a constant transit time that is a whole number of timesteps the two are the same.

Leakage takes a fraction per leak flow. Linear, the fraction is the share of a cohort
that leaks out over its whole time on the belt, spread evenly over that time; the share
itself is read anew each step. Exponential, the fraction is a rate per time unit taken
from what each cohort still holds. Several linear leaks are served in their order and a
later one may get less; several exponential ones are computed from the same content and
scaled down together where they would take more than there is.

Where Stella documents nothing, this follows the conveyor specification of the Simlin
project, which sets out to reproduce Stella.
"""

import math

# Material at a position this close to the end of the belt has arrived.
_EPSILON = 1e-9


def slat_count(transit, dt):
    """The number of slats for a transit time: rounded half away from zero, at least 1."""
    ratio = transit / dt
    return max(1, int(math.floor(abs(ratio) + 0.5)))


class Cohort:
    """The material that entered the belt in one timestep."""

    __slots__ = ("entered", "content", "basis", "window", "depth", "low", "high")

    def __init__(self, entered, content, basis, window, depth=0, low=0.0, high=0.0):
        self.entered = entered     # the time from which it lies on the belt
        self.content = content
        self.basis = basis         # per linear leak: what one step of travel leaks per unit of fraction
        self.window = window       # per linear leak: what is still to leak per unit of fraction
        self.depth = depth         # traditional: steps until it leaves
        self.low = low             # FIFO: the part of the unit belt it covers
        self.high = high

    def copy(self):
        return Cohort(self.entered, self.content, list(self.basis), list(self.window),
                      self.depth, self.low, self.high)


class Belt:
    """What lies on a conveyor at one moment."""

    def __init__(self, fifo, exponential, cohorts):
        self.fifo = fifo
        self.exponential = exponential
        self.cohorts = cohorts

    def contents(self):
        return sum(cohort.content for cohort in self.cohorts)

    def agecount(self, t, minimum, maximum):
        """The material that has been on the belt for at least `minimum` and less than
        `maximum` time units at time `t`."""
        return sum(cohort.content for cohort in self.cohorts
                   if minimum - _EPSILON <= t - cohort.entered < maximum - _EPSILON)

    def advance(self, t, dt, inflow, transit, fractions):
        """One timestep from `t`: returns (what left at the front, what each leak took,
        the belt at `t + dt`). `inflow` is the amount entering, `fractions` one per leak."""
        cohorts = [cohort.copy() for cohort in self.cohorts]
        speed = dt / transit
        leaked = self._leak(cohorts, dt, speed, fractions)
        exited, cohorts = self._move(cohorts, speed)
        if inflow != 0.0:
            cohorts.append(self._enter(t + dt, inflow, transit, dt, len(fractions)))
        return exited, leaked, Belt(self.fifo, self.exponential, cohorts)

    def _leak(self, cohorts, dt, speed, fractions):
        leaked = [0.0] * len(fractions)
        for cohort in cohorts:
            if self.exponential:
                takes = [cohort.content * fraction * dt for fraction in fractions]
                total = sum(takes)
                if total > cohort.content > 0.0:
                    takes = [take * cohort.content / total for take in takes]
                elif cohort.content <= 0.0:
                    takes = [0.0] * len(fractions)
                for k, take in enumerate(takes):
                    leaked[k] += take
                cohort.content -= sum(takes)
            else:
                for k, fraction in enumerate(fractions):
                    # One step of travel: a slat on the traditional belt, `speed` of the
                    # unit belt on a FIFO one - a share of the cohort's entering amount.
                    step = cohort.basis[k] * (speed if self.fifo else 1.0)
                    use = min(step, cohort.window[k])
                    take = min(fraction * use, cohort.content)
                    cohort.window[k] -= use
                    cohort.content -= take
                    leaked[k] += take
        return leaked

    def _move(self, cohorts, speed):
        exited = 0.0
        remaining = []
        for cohort in cohorts:
            if not self.fifo:
                if cohort.depth <= 1:
                    exited += cohort.content
                    continue
                cohort.depth -= 1
                remaining.append(cohort)
                continue
            cohort.low += speed
            cohort.high += speed
            if cohort.low >= 1.0 - _EPSILON:
                exited += cohort.content
                continue
            if cohort.high > 1.0 + _EPSILON:
                share = (cohort.high - 1.0) / (cohort.high - cohort.low)
                exited += cohort.content * share
                cohort.content *= 1.0 - share
                cohort.basis = [value * (1.0 - share) for value in cohort.basis]
                cohort.window = [value * (1.0 - share) for value in cohort.window]
                cohort.high = 1.0
            remaining.append(cohort)
        return exited, remaining

    def _enter(self, entered, amount, transit, dt, leaks):
        if self.fifo:
            # The whole entering amount is the basis; each step leaks its share of the
            # distance travelled.
            return Cohort(entered, amount, [amount] * leaks, [amount] * leaks,
                          low=0.0, high=dt / transit)
        depth = slat_count(transit, dt)
        return Cohort(entered, amount, [amount / depth] * leaks, [amount] * leaks, depth=depth)


def filled(fifo, exponential, start, dt, transit, fractions, initial):
    """The belt at the start of a run.

    `initial` is the total on the belt, spread in the equilibrium its leakage implies, or
    a list: one value per slat if it has as many entries as the belt has slats, else one
    per time unit, each spread evenly over that time unit's slats. The first value leaves
    first. A list too short repeats its last value, one too long is cut.
    """
    slats = slat_count(transit, dt)
    retained = _retained_profile(exponential, slats, dt, fractions)   # front first
    if isinstance(initial, (list, tuple)):
        contents = _from_list([float(value) for value in initial], slats, dt)
    else:
        # The profile starts at 1 at the back of the belt, so it never sums to zero.
        scale = float(initial) / sum(retained)
        contents = [scale * share for share in retained]

    cohorts = []
    leaks = len(fractions)
    for index, content in enumerate(contents):
        depth = index + 1                      # steps until it leaves
        travelled = slats - depth              # steps it has been on the belt
        entering = content / retained[index] if retained[index] > 0.0 else content
        if fifo:
            basis = [entering] * leaks
            window = [entering * depth / slats] * leaks
            cohort = Cohort(start - travelled * dt, content, basis, window,
                            low=1.0 - depth / slats, high=1.0 - (depth - 1) / slats)
        else:
            basis = [entering / slats] * leaks
            window = [entering / slats * depth] * leaks
            cohort = Cohort(start - travelled * dt, content, basis, window, depth=depth)
        if content != 0.0:
            cohorts.append(cohort)
    return Belt(fifo, exponential, cohorts)


def _retained_profile(exponential, slats, dt, fractions):
    """What one unit entering at the back still holds at each slat, front first."""
    profile = [1.0]
    for _ in range(slats - 1):
        last = profile[-1]
        if exponential:
            profile.append(max(0.0, last * (1.0 - sum(fractions) * dt)))
        else:
            profile.append(max(0.0, last - sum(fractions) / slats))
    profile.reverse()
    return profile


def _from_list(values, slats, dt):
    if len(values) == slats:
        return list(values)
    units = int(math.floor((slats - 1) * dt + _EPSILON)) + 1
    values = (values + [values[-1]] * units)[:units] if values else [0.0] * units
    blocks = [int(math.floor(index * dt + _EPSILON)) for index in range(slats)]
    sizes = [blocks.count(unit) for unit in range(units)]
    return [values[block] / sizes[block] for block in blocks]
