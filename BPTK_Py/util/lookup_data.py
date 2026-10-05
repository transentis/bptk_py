import math


def lookup_points(name, points):
    """The points of lookup table `name` in the order interpolation needs.

    Sorted by x, because the order a list was written in carries no meaning and the
    interpolation reads the first point as the left edge. A table with no points, a point
    whose x is not a finite number, or two points at the same x raise `ValueError`: the
    last has two values at one x, and the engines used to pick different ones. The Rust
    engine applies the same rule (`sorted_points` in `src/model.rs`).

    Returns `points` itself when it is in order already, which is the usual case and is
    what makes this cheap enough to call on every lookup.
    """
    if len(points) == 0:
        raise ValueError("Lookup table '{}' has no points".format(name))
    xs = [point[0] for point in points]
    for x in xs:
        if not math.isfinite(x):
            raise ValueError(
                "Lookup table '{}' has a point at x={}; x must be a finite number".format(
                    name, float(x)))
    if all(a < b for a, b in zip(xs, xs[1:])):
        return points
    ordered = sorted(points, key=lambda point: point[0])
    for a, b in zip(ordered, ordered[1:]):
        if a[0] == b[0]:
            raise ValueError("Lookup table '{}' has two points at x={}".format(name, float(a[0])))
    return ordered


def lookup_data(model, names):
    """
    Get interpolated data of lookup function
    :param name: Name(s) of lookup function as a list or string (comma,seperated
    :return: None
    """

    from scipy.interpolate import interp1d
    import numpy as np
    import pandas as pd

    if type(names) is str:
        names = names.split(",")



    dfs = []
    for name in names:

        if name in model.points.keys():
            points = model.points[name]
        else:
            points = find_lookup(name,model)
        if points is not None:
            points = lookup_points(name, points)

        try:
            x_vals = np.array([x[0] for x in points])
            y_vals = np.array([x[1] for x in points])

            # Sampled at the given points rather than on a grid. For linear
            # interpolation that is the same polyline, whether or not the lookup is
            # indexed by time - a denser grid would add rows and no information. The
            # `xmin`/`xmax` that used to be computed here were never used by anything.
            x2 = x_vals
            f = interp1d(x_vals, y_vals)
            data = {}
            data[name] = []
            index = list(x2)
            for i in x2:
                data[name] += [float(f(i))]

            dfs += [pd.DataFrame(data, index=index)]
        except TypeError:  # -> lookup function not found
            pass

    if len(dfs) > 1:
        df = dfs.pop(0)
        for elem in dfs:
            df = df.combine_first(elem)
    else:
        df = dfs.pop(0)

    return df

def find_lookup(name,model):
    from BPTK_Py import sd_functions as sd
    for _, value in model.converters.items():
        if isinstance(value._equation,sd.Lookup):
            if value.name == name:
                return value._equation.points