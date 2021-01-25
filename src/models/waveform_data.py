import struct
import math

# TODO: we doesn't support version 2 in any at methods
class WaveformData(object):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self._data = None
        with open(path, 'rb') as binaryFile:
            self._data = binaryFile.read()
        if(not self.isCompatible()): raise TypeError("not compatable waveform dat file, Version should be 1, version 2 will be supported in next release")
        
    def isCompatible(self):
        return self.version in [1,]

    def ietr_all_samples(self, start, end):
        'return minSambles, maxSamples given a time range in seconds from start to end'
        d = end - start # seconds
        pixels = math.floor(d * self.pixels_per_second) # TODO: this omit last value in the duration
        firstPixelIndex = self.at_time(start)
        #* using target channel, and not one line syntax
        channelIndex = 0
        for pixelIndex in range(firstPixelIndex, firstPixelIndex + pixels):
            mni = pixelIndex * 2 + pixelIndex * channelIndex
            mxi = mni + 1
            yield self.at(mni), self.at(mxi)

    @property
    def version(self):
        return self.getInt32(0)
    
    @property
    def channels(self):
        if self.version == 1: return 1
        return self.getInt32(20)
    
    @property
    def scale(self):
        return self.getUint32(12)
        
    @property
    def bits(self):
        return 8 if bool(self.getUint32(4)) else 16

    @property
    def sample_rate(self):
        return self.getInt32(8)
    
    @property
    def length(self):
        'Number of pixels'
        return self.getUint32(16)
    
    @property
    def samples_length(self):
        infoSize = 2 
        return self.length / self.info_size

    @property
    def info_size(self):
        oneChannelDataSize = 2 # 0: max_sample, 1: min_sample
        return self.channels * oneChannelDataSize

    @property
    def headerSize(self):
        if(self.version == 1): return 20
        return 24

    def at_time(self, time):
        '''
        Returns the pixel location for a given time.
        @param {number} time
        @return {integer} Index location for a specific time.
        '''
        return math.floor(time * self.sample_rate / self.scale)

    @property
    def time(self, index):
        '''
        Returns the time in seconds for a given index
        '''
        return index * self.scale / self.sample_rate

    @property
    def seconds_per_pixel(self):
        '''Return the amount of time represented by a single pixel.'''
        return self.scale / self.sample_rate

    @property
    def duration(self):
        '''Returns the (approximate) duration of the audio file, in seconds.'''
        return self.length * self.scale / self.sample_rate
        
    @property
    def pixels_per_second(self):
        return self.sample_rate / self.scale
        # L * S * R
        # -----
        #   R * S
        #
        #

    def at(self, index):
        'returns sample(max or min, any channel) at given index'
        return self.getInt8(20 + index)

    def max_sample(self, sample_index):
        if(sample_index >= self.sample_rate): 
            raise IndexError(f"sample index out of bound, {sample_index} >= {self.sample_rate}")
        return self.at((sample_index / self.info_size) + 1)

    def min_sample(self, sample_index):
        if(sample_index >= self.sample_rate): 
            raise IndexError(f"sample index out of bound, {sample_index} >= {self.sample_rate}")
        return self.at(sample_index / self.info_size)


    def __getitem__(self, items):
        if(isinstance(items, slice)):
            s, e = items[0], items[1]
            res = [0]*(e - s)
            for i in range(s, e):
                res[i] = self.at(i)
            return res
        return self.at(i)

    def getInt32(self, offset):
        return struct.unpack_from("<i", self._data, offset=offset)[0]

    def getUint32(self, offset):
        return struct.unpack_from("<I", self._data, offset=offset)[0]

    def getInt8(self, offset):
        return struct.unpack_from("<b", self._data, offset=offset)[0]
        # vbyte = self._data[offset]
        # unsignedVal = struct.unpack('<h', vbyte.to_bytes(1, "little") + b"\x00" )[0]
        # signedVal = (unsignedVal + 127) % 256 - 127
        # print(v1, signedVal)
        # return signedVal


if __name__ == "__main__":
    # wr = WaveformData("D:\\shaban\\A-sheikh sh3ban\\2019___gadeen zoom\\01. first week\\ZOOM0023\\ZOOM0023_LR.dat")
    # wr = WaveformData("D:\\shaban\\A-sheikh sh3ban\\2019___gadeen zoom\\03. final\\ZOOM0005\\ZOOM0005_LR-0002__16.dat")
    wr = WaveformData("D:\\shaban\\A-sheikh sh3ban\\2019___gadeen zoom\\03. final\\ZOOM0005\\ZOOM0005_LR-0001.dat")
    print("testing...")
    print("version:", wr.version)
    print("channels:", wr.channels)
    print("scale:", wr.getUint32(12))
    print("length:", wr.length)
    print("bits:", wr.bits)
    print("sample rate:", wr.sample_rate)

    print("calculation..")
    print("duration:", wr.duration)
    i = 0
    # while i < wr.length * 2:
    #     print(i / 2, ":", wr.at(i), wr.at(i + 1))
    #     i += 2
    for mn, mx in wr.ietr_all_samples(wr.duration - 1, wr.duration):
        print(i, ":", mn, mx)
        i += 1
