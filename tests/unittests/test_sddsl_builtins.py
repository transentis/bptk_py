import math
import unittest

from BPTK_Py import Model
from BPTK_Py import sd_functions as sd
from BPTK_Py.sddsl import sddsl_builtins

# Every random function of sd_functions, with arguments it accepts.
SEEDED = {
    "random": lambda seed: sd.random(0.0, 1.0, seed=seed),
    "uniform": lambda seed: sd.uniform(0.0, 1.0, seed=seed),
    "normal": lambda seed: sd.normal(10.0, 2.0, seed=seed),
    "lognormal": lambda seed: sd.lognormal(10.0, 2.0, seed=seed),
    "logistic": lambda seed: sd.logistic(10.0, 2.0, seed=seed),
    "beta": lambda seed: sd.beta(2.0, 3.0, seed=seed),
    "binomial": lambda seed: sd.binomial(20, 0.5, seed=seed),
    "negbinomial": lambda seed: sd.negbinomial(5, 0.5, seed=seed),
    "exprnd": lambda seed: sd.exprnd(2.0, seed=seed),
    "gamma": lambda seed: sd.gamma(2.0, 1.0, seed=seed),
    "geometric": lambda seed: sd.geometric(0.3, seed=seed),
    "pareto": lambda seed: sd.pareto(2.0, 1.0, seed=seed),
    "poisson": lambda seed: sd.poisson(4.0, seed=seed),
    "triangular": lambda seed: sd.triangular(0.0, 1.0, 3.0, seed=seed),
    "weibull": lambda seed: sd.weibull(2.0, 1.0, seed=seed),
    "montecarlo": lambda seed: sd.montecarlo(50.0, seed=seed),
    "lookuprandom": lambda seed: sd.lookuprandom([[0.0, 0.0], [2.0, 1.0], [4.0, 0.0]], seed=seed),
}


def _series(build, seed, name="draw", stoptime=20.0, dt=1.0):
    model = Model(starttime=0.0, stoptime=stoptime, dt=dt, name="seeded")
    model.converter(name).equation = build(seed)
    return [model.evaluate_equation(name, t) for t in range(int(stoptime) + 1)]


class TestSeededDraws(unittest.TestCase):
    """A seed makes a random function draw the same sequence on every run."""

    def test_every_random_function_repeats_its_sequence(self):
        for name, build in SEEDED.items():
            with self.subTest(name):
                first = _series(build, 42)
                self.assertEqual(first, _series(build, 42))
                self.assertNotEqual(first, _series(build, 43))
                self.assertGreater(len(set(first)), 1)

    def test_the_order_of_evaluation_does_not_matter(self):
        def run(reverse):
            model = Model(starttime=0.0, stoptime=10.0, dt=1.0, name="order")
            model.converter("seeded").equation = sd.normal(0.0, 1.0, seed=5)
            model.converter("other").equation = sd.normal(0.0, 1.0)
            times = list(range(11))
            if reverse:
                times.reverse()
                [model.evaluate_equation("other", t) for t in times]
            return {t: model.evaluate_equation("seeded", t) for t in times}

        self.assertEqual(run(False), run(True))

    def test_a_seeded_draw_leaves_the_others_alone(self):
        import numpy as np
        np.random.seed(1)
        expected = [np.random.normal(0.0, 1.0) for _ in range(3)]

        np.random.seed(1)
        model = Model(starttime=0.0, stoptime=3.0, dt=1.0, name="alone")
        model.converter("seeded").equation = sd.normal(0.0, 1.0, seed=9)
        drawn = []
        for t in range(3):
            model.evaluate_equation("seeded", t)
            drawn.append(np.random.normal(0.0, 1.0))

        self.assertEqual(drawn, expected)

    def test_the_cells_of_an_array_draw_apart(self):
        for shape in ("vector", "named"):
            with self.subTest(shape):
                model = Model(starttime=0.0, stoptime=2.0, dt=1.0, name="cells")
                mean = model.constant("mean")
                if shape == "vector":
                    mean.setup_vector(3, [0.0, 0.0, 0.0])
                    cells = ["draw[0]", "draw[1]", "draw[2]"]
                else:
                    mean.setup_named_vector({"a": 0.0, "b": 0.0, "c": 0.0})
                    cells = ["draw[a]", "draw[b]", "draw[c]"]
                model.converter("draw").equation = sd.normal(mean, 1.0, seed=3)

                values = [model.evaluate_equation(cell, 1.0) for cell in cells]

                self.assertEqual(len(set(values)), 3)

    def test_a_seed_can_be_a_model_element(self):
        model = Model(starttime=0.0, stoptime=3.0, dt=1.0, name="element_seed")
        seed = model.constant("seed")
        seed.equation = 42.0
        model.converter("draw").equation = sd.normal(10.0, 2.0, seed=seed)

        self.assertEqual([model.evaluate_equation("draw", t) for t in range(4)],
                         _series(SEEDED["normal"], 42, stoptime=3.0))

    def test_a_scenario_draws_what_the_registered_model_draws(self):
        from BPTK_Py.scenariomanager.scenario_manager_sd import ScenarioManagerSd
        model = Model(starttime=0.0, stoptime=5.0, dt=1.0, name="clone")
        model.converter("draw").equation = sd.normal(10.0, 2.0, seed=11)

        clone = ScenarioManagerSd().get_cloned_model(model)

        self.assertEqual([clone.evaluate_equation("draw", t) for t in range(6)],
                         [model.evaluate_equation("draw", t) for t in range(6)])

    def test_an_invalid_seed_gives_nan(self):
        for seed in (-1, 1.5, sd.nan()):
            with self.subTest(seed=seed):
                for name in ("normal", "montecarlo"):
                    self.assertTrue(math.isnan(_series(SEEDED[name], seed, stoptime=0.0)[0]))

    def test_invalid_arguments_are_reported_as_without_a_seed(self):
        model = Model(starttime=0.0, stoptime=1.0, dt=1.0, name="invalid")
        model.converter("draw").equation = sd.normal(0.0, -1.0, seed=1)
        model.converter("not_finite").equation = sd.normal(sd.nan(), 1.0, seed=1)

        self.assertTrue(math.isnan(model.evaluate_equation("draw", 0.0)))
        self.assertTrue(math.isnan(model.evaluate_equation("not_finite", 0.0)))

    def test_a_step_is_counted_from_the_start(self):
        late = Model(starttime=10.0, stoptime=12.0, dt=0.5, name="late")
        late.converter("draw").equation = sd.normal(0.0, 1.0, seed=2)
        early = Model(starttime=0.0, stoptime=2.0, dt=0.5, name="early")
        early.converter("draw").equation = sd.normal(0.0, 1.0, seed=2)

        self.assertEqual([late.evaluate_equation("draw", 10.0 + 0.5 * step) for step in range(5)],
                         [early.evaluate_equation("draw", 0.5 * step) for step in range(5)])


class TestCellKey(unittest.TestCase):
    def test_positions_and_labels_become_whole_numbers(self):
        from BPTK_Py.sddsl.operators import _cell_key

        self.assertEqual(_cell_key(None), [])
        self.assertEqual(_cell_key(2), [2])
        self.assertEqual(_cell_key([1, 0]), [1, 0])
        self.assertEqual(_cell_key(["north"]), _cell_key(["north"]))
        self.assertNotEqual(_cell_key(["north"]), _cell_key(["south"]))
        self.assertTrue(all(isinstance(key, int) for key in _cell_key(["north", 3])))


class TestUnseeded(unittest.TestCase):
    def test_without_a_seed_the_global_generators_draw(self):
        import random
        import numpy as np
        model = Model(starttime=0.0, stoptime=1.0, dt=1.0, name="global")
        model.converter("uniform").equation = sd.uniform(0.0, 1.0)
        model.converter("normal").equation = sd.normal(0.0, 1.0)

        random.seed(4)
        np.random.seed(4)
        drawn = (model.evaluate_equation("uniform", 0.0), model.evaluate_equation("normal", 0.0))
        random.seed(4)
        np.random.seed(4)

        self.assertEqual(drawn, (random.uniform(0.0, 1.0), np.random.normal(0.0, 1.0)))
        self.assertIs(sddsl_builtins.np.random, np.random)


class TestLookupRandom(unittest.TestCase):
    def test_a_draw_at_the_very_end_gives_the_last_x(self):
        # The uniform draw times the total area, worn down segment by segment, can reach the
        # end through rounding - or with a draw of 1.0, which numpy never gives
        class Edge:
            @staticmethod
            def uniform(low, high):
                return high

        self.assertEqual(sddsl_builtins._lookup_random(Edge(), 0.0, 0.0, 1.0, 1.0, 2.0, 0.0), 2.0)
