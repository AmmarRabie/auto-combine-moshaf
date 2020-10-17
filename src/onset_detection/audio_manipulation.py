def detectAudioChanges(audio, window_size, shift_value, max_diff_thre=6, function='dBFS', algo="avg"):
    '''
        audio: AudioSegment-like object of the whole audio
        window_size: window size in milli seconds
        shift_value: shift value or seek points of the algo, the window is shifted by this value every iteration
        max_diff_thre: maximum difference that will be considered a change 
        method: 'avg' or minmax'
        function: 'dbfs' or 'rms'

        returns: generator of (position of cut in millis, boolean whether it increasing or decreasing change)
    '''
    return globals()[f"detectAudioChanges_{algo}"](audio, window_size, shift_value, max_diff_thre=6, function=function)



def detectAudioChanges_avg(audio, window_size, shift_value, max_diff_thre=6, function='dBFS'):
    '''
        audio: AudioSegment-like object of the whole audio
        window_size: window size in milli seconds
        shift_value: shift value or seek points of the algo, the window is shifted by this value every iteration
        max_diff_thre: maximum difference that will be considered a change 
        function: 'dBFS' or 'rms'

        returns: generator of (position of cut in millis, boolean whether it increasing or decreasing change)
    '''
    audioLen = len(audio)
    if (window_size > audioLen):
        return None
    offsets = range(shift_value, audioLen - int(window_size), shift_value)
    currentSum = getattr(audio[0: window_size], function)
    currentAvg = currentSum
    print("sum=", currentSum, "avg", currentAvg)
    cnt = 1
    for windowsToken, offset in enumerate(offsets):
        currentValue = getattr(audio[offset: offset + window_size], function)
        diff = abs(currentValue - currentAvg)
        # print(currentValue, currentAvg)
        print(diff)
        if diff > max_diff_thre:
            inc = currentValue > max_diff_thre
            currentSum = currentValue
            currentAvg = currentValue
            cnt = 1
            yield offset, inc
            continue
        currentSum += currentValue
        currentAvg = currentSum / (cnt + 1)


def detectAudioChanges_minmax(audio, window_size, shift_value, max_diff_thre=6, function='dBFS'):
    '''
        audio: AudioSegment-like object of the whole audio
        window_size: window size in milli seconds
        shift_value: shift value or seek points of the algo, the window is shifted by this value every iteration
        max_diff_thre: maximum difference that will be considered a change 
        function: 'dBFS' or 'rms'

        returns: generator of (position of cut in millis, boolean whether it increasing or decreasing change)
    '''
    offset = 0
    currentMin = float("infinity")
    currentMax = -float("infinity")
    while(offset < len(audio)):
        wind = offset, offset + window_size
        selectedAudio = audio[wind[0]:wind[1]]
        dbfs = selectedAudio.dBFS
        currentMin = min(currentMin, dbfs)
        currentMax = max(currentMax, dbfs)
        # print(currentMin, currentMax, abs(currentMax - currentMin))
        if (abs(currentMax - currentMin) >= max_diff_thre):
            # see what current dbfs close to (min or max) => to know at this offset the change was increasing or decreasing
            # false mean decreasing (we cut here because of the value decreased), true mean increasing (we cut because of increasing)
            inc = abs(dbfs - currentMax) < abs(dbfs - currentMin)
            yield offset, inc
            currentMin = float("infinity")
            currentMax = -float("infinity")
        offset += shift_value



def test():
    from python_speech_features.base import mfcc
    from pydub.audio_segment import AudioSegment as AS

    as1 = AS.from_file("../ex1_ 1.mp3")
    as2 = AS.from_file("../ex1_ 2.mp3")
    # as1 = AS.from_file("../ex1_ 3.mp3")
    features1 = mfcc(as1.raw_data, as1.frame_rate)
    features2 = mfcc(as1.raw_data, as1.frame_rate)

    input(features1)
    input(features2)



if __name__ == "__main__":
    test()