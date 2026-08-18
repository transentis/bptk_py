import unittest

from BPTK_Py.util import ProgressBar


class TestProgressBar(unittest.TestCase):
    """Unit tests for the tqdm-backed progress bar that replaced ipywidgets.

    The schedulers only ever assign to `value`, so that is the surface under
    test. `_bar.n` is checked alongside it because the whole point of the class
    is translating an absolute fraction into the relative updates tqdm expects -
    a `value` that moves while `n` does not would be a silent failure.
    """

    def test_starts_at_zero(self):
        with ProgressBar(description="test") as bar:
            self.assertEqual(bar.value, 0.0)
            self.assertEqual(bar._bar.n, 0.0)

    def test_value_advances_the_bar(self):
        with ProgressBar(description="test") as bar:
            bar.value = 0.25
            self.assertAlmostEqual(bar.value, 0.25)
            self.assertAlmostEqual(bar._bar.n, 0.25)

            # A second absolute assignment must move the bar by the difference,
            # not by the new value.
            bar.value = 0.75
            self.assertAlmostEqual(bar.value, 0.75)
            self.assertAlmostEqual(bar._bar.n, 0.75)

    def test_value_is_clamped(self):
        with ProgressBar(description="test") as bar:
            bar.value = 1.5
            self.assertEqual(bar.value, 1.0)

        with ProgressBar(description="test") as bar:
            bar.value = -0.5
            self.assertEqual(bar.value, 0.0)

    def test_bar_does_not_rewind(self):
        """A scheduler resetting its progress must not rewind the rendered bar."""
        with ProgressBar(description="test") as bar:
            bar.value = 0.6
            bar.value = 0.2

            # The reported value follows the scheduler ...
            self.assertAlmostEqual(bar.value, 0.2)
            # ... but tqdm, which cannot go backwards, stays where it was.
            self.assertAlmostEqual(bar._bar.n, 0.6)

    def test_close_completes_the_bar(self):
        bar = ProgressBar(description="test")
        bar.value = 0.4
        bar.close()

        self.assertEqual(bar.value, 1.0)
        self.assertAlmostEqual(bar._bar.n, 1.0)
        self.assertTrue(bar._bar.disable)

    def test_close_after_a_reset_does_not_overshoot(self):
        """Closing must fill up from the bar's position, not from `value`.

        After a reset the two have diverged; computing the remainder from
        `value` pushes tqdm past its total and makes it warn.
        """
        bar = ProgressBar(description="test")
        bar.value = 0.6
        bar.value = 0.2
        bar.close()

        self.assertAlmostEqual(bar._bar.n, 1.0)

    def test_close_is_idempotent(self):
        bar = ProgressBar(description="test")
        bar.close()
        bar.close()

        self.assertEqual(bar.value, 1.0)

    def test_context_manager_closes_on_exception(self):
        bar = None
        with self.assertRaises(ValueError):
            with ProgressBar(description="test") as opened:
                bar = opened
                bar.value = 0.3
                raise ValueError("simulation failed")

        self.assertTrue(bar._bar.disable)

    def test_accepts_integer_values(self):
        """`progress = episode_count / episodes` can hand over an int 0 or 1."""
        with ProgressBar(description="test") as bar:
            bar.value = 1
            self.assertEqual(bar.value, 1.0)


if __name__ == "__main__":
    unittest.main()
