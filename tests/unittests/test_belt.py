import unittest

from BPTK_Py.sddsl.belt import Belt, Cohort, filled, slat_count

# The reference scenarios of the Simlin conveyor specification: dt 0.25, transit 4,
# 250 entering per time unit.
DT = 0.25


def run(fifo=False, exponential=False, fractions=(), initial=1000.0, steps=200,
        transit=lambda t: 4.0, inflow=250.0, fractions_at=None):
    belt = filled(fifo, exponential, 0.0, DT, transit(0.0), list(fractions), initial)
    rows = []
    for step in range(steps):
        t = step * DT
        current = fractions_at(t) if fractions_at else list(fractions)
        exited, leaked, following = belt.advance(t, DT, inflow * DT, transit(t), current)
        rows.append((t, belt.contents(), exited / DT, [amount / DT for amount in leaked]))
        assert abs(inflow * DT - exited - sum(leaked) - (following.contents() - belt.contents())) < 1e-6
        belt = following
    return rows


class TestBothBelts(unittest.TestCase):
    """With a constant transit time the traditional and the FIFO belt agree."""

    def test_the_reference_scenarios(self):
        for fifo in (False, True):
            with self.subTest(fifo=fifo):
                steady = run(fifo=fifo)
                self.assertEqual(steady[0][1:3], (1000.0, 250.0))
                self.assertEqual(steady[-1][1:3], (1000.0, 250.0))

                empty = run(fifo=fifo, initial=0.0)
                self.assertEqual(next(t for t, _, out, _ in empty if out > 0), 4.0)
                self.assertEqual(empty[16][1], 1000.0)

                linear = run(fifo=fifo, fractions=[0.2])[-1]
                self.assertAlmostEqual(linear[1], 906.25)
                self.assertAlmostEqual(linear[2], 200.0)
                self.assertAlmostEqual(linear[3][0], 50.0)

                exponential = run(fifo=fifo, exponential=True, fractions=[0.1])[-1]
                self.assertAlmostEqual(exponential[1], 832.699579, places=6)
                self.assertAlmostEqual(exponential[2], 166.730042, places=6)

                two = run(fifo=fifo, exponential=True, fractions=[0.1, 0.1])[-1]
                self.assertAlmostEqual(two[2], 110.031667, places=6)
                self.assertAlmostEqual(two[3][0], two[3][1])

                switching = run(fifo=fifo, fractions=[0.2],
                                fractions_at=lambda t: [0.2 if t < 4 else 0.4])
                self.assertAlmostEqual(switching[16][3][0], 100.0)
                self.assertAlmostEqual(switching[-1][2], 150.0)

                shrinking = run(fifo=fifo, fractions=[0.2], steps=400,
                                transit=lambda t: 4.0 if t < 2 else 2.0)
                self.assertAlmostEqual(shrinking[-1][2], 200.0)

    def test_slats_round_half_away_from_zero(self):
        self.assertEqual(slat_count(4.1, DT), 16)
        self.assertEqual(slat_count(4.125, DT), 17)
        self.assertEqual(slat_count(0.01, DT), 1)


class TestTransitChanges(unittest.TestCase):
    def outflow(self, fifo, transit):
        return {t: out for t, _, out, _ in run(fifo=fifo, transit=transit, steps=96)}

    def test_a_shorter_transit_time_lets_new_material_overtake(self):
        out = self.outflow(False, lambda t: 4.0 if t < 8 else 2.0)
        self.assertEqual([out[t] for t in (8.0, 9.75, 10.0, 11.75, 12.0)], [250.0, 250.0, 500.0, 500.0, 250.0])

    def test_a_shorter_transit_time_speeds_up_a_fifo_belt(self):
        out = self.outflow(True, lambda t: 4.0 if t < 8 else 2.0)
        self.assertEqual([out[t] for t in (7.75, 8.0, 9.75, 10.0)], [250.0, 500.0, 500.0, 250.0])

    def test_a_longer_transit_time(self):
        traditional = self.outflow(False, lambda t: 4.0 if t < 8 else 8.0)
        fifo = self.outflow(True, lambda t: 4.0 if t < 8 else 8.0)
        self.assertEqual([traditional[t] for t in (11.75, 12.0, 15.75, 16.0)], [250.0, 0.0, 0.0, 250.0])
        self.assertEqual([fifo[t] for t in (7.75, 8.0, 15.75, 16.0)], [250.0, 125.0, 125.0, 250.0])

    def test_a_fifo_belt_takes_a_transit_time_between_slats(self):
        # Transit 1.1 is 4.4 steps: the front edge of the first cohort arrives after four,
        # with 0.6 of it, and from then on what leaves is what enters.
        rows = run(fifo=True, initial=0.0, transit=lambda t: 1.1, steps=12)
        self.assertEqual(rows[3][2], 0.0)
        self.assertAlmostEqual(rows[4][2], 150.0)
        self.assertAlmostEqual(rows[5][2], 250.0)

    def test_a_fifo_cohort_leaving_in_part_keeps_its_leak_in_proportion(self):
        # The part of a cohort that lay at the front of the entry edge leaves before it
        # has travelled the whole belt, and leaks for less time: a little under f.
        rows = run(fifo=True, fractions=[0.2], initial=0.0, transit=lambda t: 1.1, steps=40)
        self.assertGreater(rows[-1][3][0], 45.0)
        self.assertLess(rows[-1][3][0], 50.0)


class TestLeakage(unittest.TestCase):
    def test_linear_leaks_beyond_the_content_are_served_in_order(self):
        # Each step both take their share until a cohort runs short; from then on the
        # first comes first, and nothing is left to leave at the front.
        last = run(fractions=[0.7, 0.7])[-1]
        self.assertGreater(last[3][0], last[3][1])
        self.assertAlmostEqual(last[3][0] + last[3][1], 250.0)
        self.assertAlmostEqual(last[2], 0.0)

    def test_exponential_leaks_beyond_the_content_are_scaled_together(self):
        last = run(exponential=True, fractions=[5.0, 5.0])[-1]
        self.assertAlmostEqual(last[3][0], last[3][1])
        self.assertAlmostEqual(last[2], 0.0)

    def test_an_empty_cohort_leaks_nothing(self):
        belt = Belt(False, True, [Cohort(0.0, 0.0, [0.0], [0.0], depth=2)])
        _, leaked, _ = belt.advance(0.0, 1.0, 0.0, 2.0, [0.5])
        self.assertEqual(leaked, [0.0])


class TestFilling(unittest.TestCase):
    def test_a_list_gives_one_value_per_time_unit_the_first_leaving_first(self):
        rows = run(initial=[1.0, 2.0, 3.0, 4.0], inflow=0.0, steps=16)
        self.assertEqual([rows[step][2] for step in (0, 3, 4, 8, 12, 15)], [1.0, 1.0, 2.0, 3.0, 4.0, 4.0])

    def test_a_list_with_one_value_per_slat_fills_the_slats(self):
        rows = run(initial=[float(value) for value in range(16)], inflow=0.0, steps=16)
        self.assertEqual([rows[step][2] * DT for step in (0, 1, 15)], [0.0, 1.0, 15.0])

    def test_a_short_list_repeats_its_last_value_and_a_long_one_is_cut(self):
        short = run(initial=[1.0, 2.0], inflow=0.0, steps=16)
        long = run(initial=[1.0, 2.0, 3.0, 4.0, 5.0], inflow=0.0, steps=16)
        self.assertEqual(short[15][2], 2.0)
        self.assertEqual(long[0][1], 10.0)

    def test_an_empty_list_fills_nothing(self):
        self.assertEqual(filled(False, False, 0.0, DT, 4.0, [], []).contents(), 0.0)

    def test_slats_a_leak_empties_start_empty(self):
        belt = filled(False, False, 0.0, DT, 4.0, [1.0] * 2, 100.0)
        self.assertAlmostEqual(belt.contents(), 100.0)
        self.assertEqual(len(belt.cohorts), 8)

    def test_a_fifo_belt_fills_like_a_traditional_one(self):
        for initial in (1000.0, [1.0, 2.0, 3.0, 4.0]):
            with self.subTest(initial=initial):
                fifo = run(fifo=True, fractions=[0.1], initial=initial, steps=20)
                traditional = run(fractions=[0.1], initial=initial, steps=20)
                for (_, contents, out, _), (_, expected, expected_out, _) in zip(fifo, traditional):
                    self.assertAlmostEqual(contents, expected)
                    self.assertAlmostEqual(out, expected_out)


class TestAgecount(unittest.TestCase):
    def test_counts_by_time_on_the_belt(self):
        belt = filled(False, False, 0.0, 1.0, 4.0, [], [1.0, 2.0, 3.0, 4.0])
        self.assertEqual(belt.agecount(0.0, 0.0, 1.0), 4.0)
        self.assertEqual(belt.agecount(0.0, 0.0, 2.0), 7.0)
        self.assertEqual(belt.agecount(0.0, 3.0, 4.0), 1.0)
        _, _, later = belt.advance(0.0, 1.0, 9.0, 4.0, [])
        self.assertEqual(later.agecount(1.0, 0.0, 1.0), 9.0)
        self.assertEqual(later.agecount(1.0, 1.0, 2.0), 4.0)
