from pydub import AudioSegment
from ..interface import IDetectorData
class AudioSegmentAdapter(IDetectorData):
    use_dbfs = True
    def __init__(self, audioSegment : AudioSegment):
        self.source = audioSegment
        if(self.use_dbfs):
            minDbfs = min(self.source[i:i + 1000].dBFS for i in range(0, int(self.source.duration_seconds * 1000) - 1200, 1000))
            self.minSourceVal = max(minDbfs, -80)
            self.maxSourceVal = self.source.max_dBFS # -2
        else:
            self.maxSourceVal = self.source.rms * 3 # take average * 3 as max
            self.minSourceVal = 0
        print(self.minValue, self.maxValue)


    def detectionValue(self, start, end):
        'returns detection value from start to end..'
        if(self.use_dbfs):
            return self.source[start * 1000:end * 1000].dBFS
        return self.source[start * 1000:end * 1000].rms

    @property
    def minValue(self):
        'min value ever for detectionValue'
        if(self.minSourceVal): return self.minSourceVal
        return 0
    
    @property
    def maxValue(self):
        'max value ever for detectionValue'
        if(self.maxSourceVal): return self.maxSourceVal
        return 100

    def percentage(self, value):
        'percentage of value scaled to minValue to maxValue'
        return 100 * (value / (self.maxValue - self.minValue))


    @property
    def duration(self):
        'duration of initialized audio'
        return self.source.duration_seconds

