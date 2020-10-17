from time import strftime, localtime, process_time as clock
from datetime import timedelta

class PreserverForTime:
    startOfProgTime = clock()
    ticks = []
__pt__ = PreserverForTime()

def tick(message = None):
    if(message): print(message)
    start = clock()
    __pt__.ticks.append(start)
    return start

def tock(message = "", fromTime = None, log=True):
    if __pt__.ticks.__len__ == 0:
        return progTime()
    end = clock()
    fromTime = fromTime or __pt__.ticks.pop()
    elapsed = end - fromTime
    if(log):
        print(f"{message}: take {logTime(elapsed)} time")
    return elapsed

def progTime(log=True):
    end = clock()
    totalTime = end - __pt__.startOfProgTime
    if(log):
        print(f"execution take {logTime(totalTime)}")
    return totalTime

def logTime(t = None):
    if t is None:
        return strftime("%Y-%m-%d %H-%M-%S", localtime())
    else:
        return str(timedelta(seconds=t))