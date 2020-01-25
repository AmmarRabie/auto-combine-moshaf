# from wavefile import read as sciread, write as sciwrite
import wave
import gc

def incload(chunkAvailableCond, path):
    print("incload start")
    waveread = wave.open(path, 'rb')
    n = 1000000 * 3 # approx 1 min
    for chunk in iter(lambda: waveread.readframes(n * 5), ''):
        with chunkAvailableCond:
            print("incload continue")
            wavewrite = wave.open("temp.wav", "wb")
            wavewrite.setparams(waveread.getparams())
            wavewrite.writeframes(chunk)
            del chunk
            gc.collect()
            wavewrite.close()
            chunkAvailableCond.notifyAll()
            print("incload notifyAll")

import pydub
import speech_recognition 
from ticktock import tick, tock

class SmartWavLoader(pydub.AudioSegment):
    def __init__(self, path, maxCacheBytes = 300 * 1024 * 1024): # 300 MB
        # super().__init__(data=data, *args, **kwargs)
        self.path = path
        # self.cache = [] # TODO: make it list of dictionaries where every dictionary represents a subsest of audio
        self.cache = {} # e.g {(0:1000): data}
        self.reader = wave.open(path, 'rb')
        self.nchannels, self.sampwidth, self.framerate, self.nframes, *_ = self.reader.getparams()
        self.maxCacheBytes = maxCacheBytes
        self.sample_width = self.sampwidth
        self.frame_rate = self.framerate
        self.channels = self.nchannels
        self.frame_width = self.channels * self.sample_width

    def _parse(self, val):
        if val < 0:
            val = (self.nframes - abs(val) * self.reader.getframerate()) // self.reader.getframerate()
        return int(val)
        val = self.nframes if val == float("inf") else self.frame_count(ms=val)
        return int(val)

    def __getitem__(self, seconds):
        # print("..reading..", seconds)
        if isinstance(seconds, slice):
            start = seconds.start // 1000 if seconds.start is not None else 0
            end = seconds.stop // 1000 if seconds.stop is not None else self.nframes // self.reader.getframerate()

            start = min(start, self.nframes * self.reader.getframerate())
            end = min(end, self.nframes * self.reader.getframerate())
        else:
            start = seconds
            end = seconds + 1000

        # print("seconds...before", seconds, "==>", start, end)
        start = self._parse(start)
        end = self._parse(end)
        # print("seconds...after parse", seconds, "==>", start, end)

        keys = self.cache.keys()
        if (len(keys) != 0):
            cstart, cend = list(keys)[0]
            # print(cstart, cend, '   ', start, end)
            if((start < cstart and end < cstart) or (start > cend and end > cend)):
                # print("there is a cache but new different data is read")
                data = self._read(start, end)
                self._updatecache(start, end, data)
                return self.moveToAudioSegment(data)
            result = bytearray()
            # bytearraytemp = bytearray()
            if (start < cstart):
                # read from start to cstart from scratch
                # print("start < cstart, reading from start to cstart")
                result += self._read(start, cstart)
            temps = max(start, cstart)
            tempe = min(end, cend)
            # read from temps to tempe from the cache
            result += self._cread(temps, tempe)
            if (end > cend):
                # read from scratch from cend to end
                # print("cend < end, reading from cend to end")
                if (cend < len(self) // 1000): 
                    result += self._read(cend, end)
            self._updatecache(start, end, result)
            return self.moveToAudioSegment(result)
        else:
            # first time read, no cache
            # print("first time read, no cache")
            data = self._read(start, end)
            self._updatecache(start, end, data)
            return self.moveToAudioSegment(data)

    def _updatecache(self, start, end, data):
        self.cache.clear()
        self.cache[(start, end)] = bytearray(data)

    def _read(self, start, end):
        # print("_fread from", start, "to", end)
        pos = start * self.reader.getframerate() # 7 * 60 seconds * (frames / seconds) ==> frames
        # print("_read:", start, end)
        self.reader.setpos(pos) # read from frame pos
        duration = (end - start) * self.reader.getframerate() # read 'duration' frames
        return self.reader.readframes(duration)
    
    def _cread(self, start, end):
        # print("_cread from", start, "to", end)
        cs, ce = list(self.cache.keys())[0]
        relativeStart = start - cs
        relativeEnd = relativeStart + end - start
        factor = self.sampwidth*self.framerate*self.nchannels
        return self.cache[(cs, ce)][relativeStart * factor : relativeEnd * factor] # TODO: make this line make no copy of data
    def moveToAudioSegment(self, data):
        audio = pydub.AudioSegment.silent(duration=0, frame_rate=self.framerate)
        audio._data = data
        audio.sample_width = self.sampwidth
        audio.frame_rate = self.framerate
        audio.channels = self.nchannels
        audio.frame_width = audio.channels * audio.sample_width
        return audio

    def __len__(self):
        return round(1000 * (self.nframes / self.frame_rate))
    
    def frame_count(self, ms=None):
        """
        returns the number of frames for the given number of milliseconds, or
            if not specified, the number of frames in the whole AudioSegment
        """
        if ms is not None:
            return ms * (self.frame_rate / 1000.0)
        else:
            return float(self.nframes // self.frame_width)

fPathTest = "tests/ZOOM0022/ZOOM0022_LR-0002.wav"
def test():
    fPathTest = "tests/ZOOM0022/ZOOM0022_LR-0002.wav"
    waveread = wave.open(fPathTest, 'rb')
    nchannels, sampwidth, framerate, *_ = waveread.getparams()
    pos = 7 * 60 * waveread.getframerate() # 7 * 60 seconds * (frames / seconds) ==> frames
    waveread.setpos(pos) # read from frame pos
    duration = 5 * 60 * waveread.getframerate() # read 'duration' frames
    data = waveread.readframes(duration)
    print("pos", pos, "duration", duration, "tell", waveread.tell(), "+", pos + duration, "total frames", waveread.getnframes())
    print("some specs:::type of data", type(data), "first sample of the data", data[0], "try indices", data[0:10])
    tick("joining data with itself")
    data = data + data[0:3*60*sampwidth*framerate*nchannels]
    tock()
    f = wave.open("ammar.wav", 'wb')
    f.setparams(waveread.getparams())
    f.writeframes(data)
    f.close()

    tick("creating the class audio segment")
    nchannels, sampwidth, framerate, *_ = waveread.getparams()
    # audio = pydub.AudioSegment(data=data, sample_width=sampwidth, frame_rate=framerate, channels=nchannels)
    audio = pydub.AudioSegment.silent(duration=0, frame_rate=framerate)
    audio._data = data
    audio.sample_width = sampwidth
    audio.frame_rate = framerate
    audio.channels = nchannels
    audio.frame_width = audio.channels * audio.sample_width
    tock("done")
    tick("exporting")
    audio[0:3*60*1000].export("testtest.wav", format="wav")
    tock("done exporting")


import soundfile as sf
import numpy as np
def testsoundfile():
    # soundfile.blocks(fPathTest)
    # rms = [np.sqrt(np.mean(block**2)) for block in
    #    sf.blocks(fPathTest, blocksize=1024, overlap=512)]
    for block in sf.blocks(fPathTest, blocksize=1024, overlap=512):
        pass
    # np.savetxt("rms.txt", rms)



if __name__ == "__main__":
    # test()
    # testsoundfile()


    fPathTest = "tests/noisy.wav"
    swl = SmartWavLoader(fPathTest)

    tick()
    swl[46*60:60*60].export("__name__.wav", format="wav")
    tock()

    tick()
    swl[46*60 + 60:60*60 + 60].export("__name__.wav", format="wav")
    tock()

    tick()
    swl[46*60 + 1: 60*60 - 1].export("__name__2.wav", format="wav")
    tock()