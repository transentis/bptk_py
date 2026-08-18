#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018 transentis labs GmbH
# MIT License


from tqdm.auto import tqdm


class ProgressBar:
    """A progress indicator driven by a fractional value, rendered with tqdm.

    Exposes the ``value`` attribute in the range 0.0 to 1.0 that the schedulers
    already write to, so nothing downstream needs to know which library renders
    the bar. This replaces the ipywidgets ``FloatProgress`` used until 2.4.1,
    which only ever worked inside Jupyter - tqdm renders in the terminal, in
    marimo and in Jupyter alike.
    """

    def __init__(self, description="Running"):
        self._bar = tqdm(total=1.0, desc=description,
                         bar_format="{desc}: {percentage:3.0f}%|{bar}|")
        self._value = 0.0

    @property
    def value(self):
        """The progress as a fraction between 0.0 and 1.0."""
        return self._value

    @value.setter
    def value(self, value):
        value = min(max(float(value), 0.0), 1.0)
        delta = value - self._value
        self._value = value
        # tqdm only ever moves forward; a scheduler resetting its progress
        # should not rewind the rendered bar.
        if delta > 0:
            self._bar.update(delta)

    def close(self):
        """Complete and close the bar. Safe to call more than once."""
        if self._bar.disable:
            return
        # Fill up from the bar's own position, not from `value`: after a reset
        # the two have diverged, and closing on the difference would overshoot.
        remaining = self._bar.total - self._bar.n
        if remaining > 0:
            self._bar.update(remaining)
        self._value = 1.0
        self._bar.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False
