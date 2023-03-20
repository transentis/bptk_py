import math

def precision_and_scale(x):
    max_digits = 14
    int_part = int(abs(x))
    magnitude = 1 if int_part == 0 else int(math.log10(int_part)) + 1
    if magnitude >= max_digits:
        return (magnitude, 0)
    frac_part = abs(x) - int_part
    multiplier = 10 ** (max_digits - magnitude)
    frac_digits = multiplier + int(multiplier * frac_part + 0.5)
    while frac_digits % 10 == 0:
        frac_digits /= 10
    scale = int(math.log10(frac_digits))
    return (magnitude + scale, scale)

def scale(x):
    return precision_and_scale(x)[1]


def normalize(x, base=1, offset=0.0,precision=2):
    # round to base from a given offset
    return 1.0*round(base * round((x-offset)/base)+offset,precision)

def timerange(starttime,stoptime,dt,exclusive=True):
    starttime=starttime*1.0
    stoptime=stoptime*1.0
    dt=dt*1.0
    i=starttime
    timerange=[]
    while i <= stoptime*1.0:
        if i < stoptime*1.0 or not exclusive:
            timerange.append(i)
        
        i=normalize(i+dt,base=dt,offset=starttime,precision=max(scale(starttime),scale(dt)))

    return timerange