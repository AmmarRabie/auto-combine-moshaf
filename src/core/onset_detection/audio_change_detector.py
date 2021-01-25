from helpers.utils import timeRepr
from .interface import IAudioChangeDetector, IDetectorData

class AudioChangeDetector(IAudioChangeDetector):
    '''
    simple onset detection using audio dbfs change feature
    '''
    def __init__(self, window_size, shift_value, max_diff_thre=15, function='dBFS'):
        self.window_size = window_size
        self.shift_value = shift_value
        self.max_diff_thre = max_diff_thre # percentage of all levels (from 0 to 100)
        self.function = function
        if(self.function != "dBFS"): 
            raise TypeError(f"AudioChangeDetector supports dbFS as a function only for now. found {function}")

    def detect_minmax(self, audio: IDetectorData, plot=False):
        offset = 0
        currentMin = float("infinity")
        currentMax = -float("infinity")
        pltData = {'time': [],'perc': [],'dval': [],'minv': [],'maxv': [], 'diff': []}
        while(offset + self.window_size < audio.duration * 1000):
            wind = offset, offset + self.window_size
            detectionVal = audio.detectionValue(wind[0] / 1000, wind[1] / 1000)
            # print("> at time", timeRepr(offset))
            # print("\t\t detection value:", detectionVal)
            currentMin = min(currentMin, detectionVal)
            currentMax = max(currentMax, detectionVal)
            currentPerc = audio.percentage(abs(currentMax - currentMin))
            # print("\t\t", currentMin, currentMax, abs(currentMax - currentMin))
            # print("\t\t", audio.percentage(abs(currentMax - currentMin)))
            if(plot):
                pltData['time'].append(offset)
                pltData['perc'].append(currentPerc)
                pltData['dval'].append(detectionVal)
                pltData['minv'].append(currentMin)
                pltData['maxv'].append(currentMax)
                pltData['diff'].append(abs(currentMax - currentMin))
            if (currentPerc >= self.max_diff_thre):
                # see what current detectionVal close to (min or max) => to know at this offset the change was increasing or decreasing
                # false mean decreasing (we cut here because of the value decreased), true mean increasing (we cut because of increasing)
                inc = abs(detectionVal - currentMax) < abs(detectionVal - currentMin)
                yield offset, inc
                # if(inc):
                #     currentMin = float("infinity")
                # else:
                #     currentMax = -float("infinity")
                currentMin = float("infinity")
                currentMax = -float("infinity")
            offset += self.shift_value
        if(plot):
            return pltData


def testDatFile(path):
    from .adapters.audiowaveform_adapter import AudioWaveformAdapter
    from models.waveform_data import WaveformData

    wind, shift = 0.5 * 60, 1
    wind, shift = 15, 5
    wind, shift = 0.5 * 60, 0.5 * 60 * 0.5
    detector = AudioChangeDetector(wind * 1000, shift * 1000)
    audio = WaveformData(path)
    audioDetectorAdapter = AudioWaveformAdapter(audio)
    gen = detector.detect_minmax(audioDetectorAdapter, plot=True)
    return gen

def testWavFile(path):
    from .adapters.audio_segment_adapter import AudioSegmentAdapter, AudioSegment

    wind, shift = 0.5 * 60, 1
    wind, shift = 15, 5
    wind, shift = 0.5 * 60, 0.5 * 60 * 0.5
    detector = AudioChangeDetector(wind * 1000, shift * 1000)
    audio = AudioSegment.from_file(path)
    audioDetectorAdapter = AudioSegmentAdapter(audio)
    gen = detector.detect_minmax(audioDetectorAdapter, plot=True)
    return gen
    

def displayResult(generator, testID):
    st = tick(f"start timing test {testID}")
    while(True):
        try:
            t, inc = next(generator)
            print(timeRepr(t), inc)
        except StopIteration as e:
            tock(testID, fromTime=st)
            pltData = e.value
            if(not pltData): break
            # display plt
            ax = sns.lineplot(data=pltData, x="time", y="dval")
            sns.lineplot(data=pltData, x="time", y="perc", ax=ax)
            # sns.lineplot(data=pltData, x="time", y="minv", ax=ax)
            # sns.lineplot(data=pltData, x="time", y="maxv", ax=ax)
            sns.lineplot(data=pltData, x="time", y="diff", ax=ax)
            plt.show()
            break

if __name__ == "__main__":
    from helpers.ticktock import tick, tock
    import seaborn as sns
    import matplotlib.pyplot as plt
    sns.set_theme(style="ticks")

    testFile = "C:\\Data\\workspace\\qur2an salah splitter\\audio_tests\\ex2.wav"
    print("Start dat file testing")
    res = testDatFile(testFile.replace(".wav", ".dat"))
    displayResult(res, "dat")

    print("Start wav file testing")
    res = testWavFile(testFile)
    displayResult(res, "wav")