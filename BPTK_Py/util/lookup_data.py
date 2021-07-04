def lookup_data(model, names):
    """
    Get interpolated data of lookup function
    :param name: Name(s) of lookup function as a list or string (comma,seperated
    :return: None
    """

    from BPTK_Py import sd_functions as sd
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

        try:
            x_vals = np.array([x[0] for x in points])
            y_vals = np.array([x[1] for x in points])
            xmax = np.max(x_vals)
            xmin = np.min(x_vals)

            x2 = np.arange(xmin, xmax, 0.01)
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
            # df = df.join(elem)
    else:
        df = dfs.pop(0)

    return df

def find_lookup(name,model):
    from BPTK_Py import sd_functions as sd
    for _, value in model.converters.items():
        if isinstance(value._equation,sd.Lookup):
            if value.name == name:
                return value._equation.points