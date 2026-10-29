"""Reading Stella's runs of the XMILE models under `tests/test_models/`.

A model checked against Stella has its run beside it, `<model>_results.csv`. Those the SD DSL
cannot express - RK4, the conveyor options, data imports - wait in `stella_parked/`, beside
the backlog items they belong to."""

from pathlib import Path

import numpy as np
import pandas as pd

TEST_MODELS = Path(__file__).resolve().parent.parent / "test_models"
PARKED = TEST_MODELS / "stella_parked"


def _export(name):
    for directory in (TEST_MODELS, PARKED):
        if (directory / "{}_results.csv".format(name)).exists():
            return directory / "{}_results.csv".format(name)
    raise FileNotFoundError("No Stella run of '{}' beside the models".format(name))


def _separator(path):
    """The decimal separator of an export: `,` from a German locale, as most are, `.` otherwise."""
    with open(path, encoding="utf-8-sig") as export:
        lines = [export.readline() for _ in range(6)]
    return "," if any("," in line for line in lines[1:]) else "."


def stella_results(name):
    """Stella's export `<name>_results.csv`, indexed by time, with Stella's column names.

    The exports separate fields by `;`, and most write `,` before decimals.
    """
    path = _export(name)
    return pd.read_csv(path, sep=";", decimal=_separator(path), encoding="utf-8-sig").set_index("time")


def stella_precision(name):
    """For each value of the export, the largest error its written digits allow: half a
    unit of its last decimal. Some cells come with fewer digits than the rest - 35.5 where
    Stella computed 35.4636 - and are as precise as they are written."""
    text = pd.read_csv(_export(name), sep=";", dtype=str,
                       keep_default_na=False, encoding="utf-8-sig").set_index("time")
    separator = _separator(_export(name))
    decimals = text.map(lambda value: _decimals(value, separator))
    precision = 0.5 * 10.0 ** -decimals.astype(float)
    precision.index = stella_results(name).index
    return precision


def _decimals(value, separator):
    """The decimals a value is written with; Excel writes some in scientific notation, 2,25E+00."""
    mantissa, _, exponent = value.upper().partition("E")
    places = len(mantissa.split(separator)[1]) if separator in mantissa else 0
    return places - (int(exponent) if exponent else 0)


def matches_stella(computed, stella, precision, rel=1e-9, floor=1e-12):
    """Whether computed values agree with Stella's, each within what its digits allow - and
    never closer than `floor`: Stella writes the rounding noise of a double, 1.11e-16 where a
    table crosses 0, with digits that would allow no difference at all."""
    computed, stella = np.asarray(computed, dtype=float), np.asarray(stella, dtype=float)
    # Equal values, infinity included, whose difference is no number
    same = (np.isnan(computed) & np.isnan(stella)) | (computed == stella)
    # A value exactly on the rounding boundary, 15.75 written as 15.8, is within its digits
    allowed = np.maximum(np.maximum(np.asarray(precision, dtype=float) * (1.0 + 1e-9), rel * np.abs(stella)), floor)
    with np.errstate(invalid="ignore"):
        within = np.abs(computed - stella) <= allowed
    return same | within
