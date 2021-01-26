class IDetectorData(object):
    'interface for audio change detector data'
    def __init__(self):
        raise NotImplementedError(f"Can't construct interface IAudioDetector")

    def detectionValue(self, start, end):
        'returns detection value from start to end..'
        raise NotImplementedError(f"{self.__class__.__name__} class should implement detectionValue method")

    @property
    def minValue(self):
        'min value ever for detectionValue'
        raise NotImplementedError(f"{self.__class__.__name__} class should implement minValue method")
    
    @property
    def maxValue(self):
        'max value ever for detectionValue'
        raise NotImplementedError(f"{self.__class__.__name__} class should implement maxValue method")

    def percentage(self, value):
        'percentage of value scaled to minValue to maxValue'
        raise NotImplementedError(f"{self.__class__.__name__} class should implement percentage method")


    @property
    def duration(self):
        'duration of initialized audio'
        raise NotImplementedError(f"{self.__class__.__name__} class should implement duration method")



class IAudioChangeDetector(object):
    'interface for any audio change detector'
    def __init__(self, window_size, shift_value, max_diff_thre=15, function='dBFS'):
        raise NotImplementedError(f"Can't construct interface IAudioDetector")

    def detect_minmax(self, audio: IDetectorData, start=None, end=None, plot=False):
        raise NotImplementedError(f"{self.__class__.__name__} class should implement detect_minmax method")