from models.waveform_data import WaveformData
from ..interface import IDetectorData
from helpers.utils import average

class AudioWaveformAdapter(IDetectorData):
    def __init__(self, source: WaveformData, use_avg=True):
        self.source = source
        minSamples, maxSamples = zip(*self.source.ietr_all_samples(0, self.duration))
        self.maxSourceValue = max(maxSamples)
        self.minSourceValue = min(minSamples)
        self.use_avg = use_avg


    def detectionValue(self, start, end):
        'returns detection value from start to end..'
        minSamples, maxSamples = zip(*self.source.ietr_all_samples(start, end))

        if(self.use_avg):
            mn = average(minSamples)
            mx = average(maxSamples)
        else:
            #TODO: if we think here with logic of detect_minmax.. we are recalculating values in the overlapped two windows.
            # specifically, overlapped = window_size - shift_value
            # so, min(start, end) = min(currentMin, min(start + overlapped, end))
            mn = min(minSamples)
            mx = max(maxSamples)
        return abs(mx - mn)

    @property
    def minValue(self):
        'min value ever for detectionValue'
        # detection value is the difference between max and min sample at given pixel range
        # because max is always > min. so the min diff will happen when they are equal, so 0 is the min
        if(self.minSourceValue): return self.minSourceValue
        return 0
    
    @property
    def maxValue(self):
        'max value ever for detectionValue'
        # detection value is the difference between max and min sample at given pixel range
        # so the max diff should be the max value * 2
        # (max = 127) - (min = -128) = 255
        if(self.maxSourceValue): return self.maxSourceValue
        return 255

    def percentage(self, value):
        'percentage of value scaled to minValue to maxValue'
        return (value / abs(self.maxValue - self.minValue)) * 100


    @property
    def duration(self):
        'duration of initialized audio'
        return self.source.duration
    