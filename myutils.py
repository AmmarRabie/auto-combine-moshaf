def timeRepr(*millis, joint=", "):
    res = []
    for p in millis:
        seconds = p / 1000
        mins = seconds // 60
        remainSeconds = seconds - mins * 60
        res.append(f"{mins}:{remainSeconds}")
    if(len(millis) == 1):
        return res[0]
    # return res
    return joint.join(res)
    
from math import ceil
def approxToNearestSeconds(time):
    return ceil(time / 1000) * 1000



def isDiff(x, y, tolerance):
    return abs(x - y) > tolerance
