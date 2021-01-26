def timeRepr(*seconds, joint=", "):
    res = []
    for p in seconds:
        mins = p // 60
        remainSeconds = p - mins * 60
        res.append(f"{mins}:{remainSeconds}")
    if(len(seconds) == 1):
        return res[0]
    # return res
    return joint.join(res)

def average(iterable):
    s = 0
    l = 0
    for x in iterable:
        s += x
        l += 1
    return s / l # TODO: raises exception if length is 0

def groupclosest(valuesList, tolerance=8):
    #? 1. We may make this function by clustering points using machine learning kmeans algo
    #? 2. We want to use variance of every group, the variance give info about the rate of speaking ==> sound should have high variance
    groups = []
    valuesList = sorted(valuesList)[::-1]
    basei = 0
    for i, val in enumerate(valuesList):
        if (abs(val[0] - valuesList[basei][0]) > tolerance):
            newGroup = valuesList[basei:i]
            newGroup = sorted(newGroup, key=lambda x: x[1]) # sort over the group over item itself
            # print("newGroup", newGroup)
            # groups.append(valuesList[basei:i])
            groups.append(newGroup)
            basei = i
    lastGroup = valuesList[basei:len(valuesList)]
    lastGroup = sorted(lastGroup, key=lambda x: x[1])
    groups.append(lastGroup)
    return groups

import wave
import pydub

import gc
def readWaveFile(path, start = 0, end = None, sequential=True):
    '''
        sequential: default to true, read the file sequentially and return bytearray to be editable to add silence or any sound without copying
        if false, that will be read entirely at one read and the object returned in bytes type
    '''
    # read data
    wav = wave.open(path, 'rb')
    nchannels, sampwidth, framerate, nframes, *_ = wav.getparams()
    epos = end * framerate if end != None else nframes
    spos = start * framerate
    wav.setpos(spos)
    duration = (epos - spos)

    def readSequentially(spos, epos):
        print("readSequentially", spos, epos, framerate)
        maxOneRead = 5 * 60 * framerate
        res = bytearray()
        remained = duration
        while (spos < epos): #? should be <=, or <
            print(spos)
            wav.setpos(spos) #? can we delete this line
            data = wav.readframes(min(maxOneRead, remained) )
            data = bytearray(data)
            gc.collect()
            remained -= maxOneRead
            res.extend(data)
            spos += maxOneRead
        return res
    data = readSequentially(spos, epos) if sequential else wav.readframes(duration)
    wav.close()
    
    # move to audio segment
    audio = pydub.AudioSegment.silent(duration=0, frame_rate=framerate)
    audio._data = bytearray(data)
    audio.sample_width = sampwidth
    audio.frame_rate = framerate
    audio.channels = nchannels
    audio.frame_width = audio.channels * audio.sample_width
    return audio

def incDbfs(obj):
    lenObj = len(obj)
    if (lenObj < 1000 * 9 * 60):
        return obj.dBFS
    every = 2 * 60 * 1000
    currentOffset = 0
    sumall = 0
    while currentOffset < lenObj:
        seg = obj[currentOffset:every]
        sumall += seg.dBFS
        currentOffset += every
try:
    from audio_metadata import load as fileInfo
    getFileLength = lambda path: ('duration', fileInfo(path)["streaminfo"]["duration"])
except:
    from os import stat as fileInfo
    getFileLength = lambda p: ('size', fileInfo(p).st_size)

from os.path import getsize as getFileSize

from math import ceil
def approxToNearestSeconds(time):
    return ceil(time / 1000) * 1000

def isDiff(x, y, tolerance):
    return abs(x - y) > tolerance

def circularIncIndex(arrayLength, currentIndex): return (currentIndex + 1) % arrayLength
def circularDecIndex(arrayLength, currentIndex): return (currentIndex - 1) % arrayLength

import json
def is_jsonable(x):
    try:
        json.dumps(x)
        return True
    except (TypeError, OverflowError):
        return False

class QuranPersistor:
    _quran = None
    _path = "quran-simple-clean.txt"


    @staticmethod
    def quran():
        if (not QuranPersistor._quran):
            with open(QuranPersistor._path, 'r', encoding="utf-8") as quranFile:
                QuranPersistor._quran = quranFile.read().splitlines(False)
        return QuranPersistor._quran


if __name__ == "__main__":
    print(QuranPersistor.quran()[0:5])
