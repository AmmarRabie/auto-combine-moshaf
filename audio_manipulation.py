def detectAudioChanges(audio, window_size, shift_value, max_diff_thre=6, function='dbfs', algo="avg"):
    '''
        audio: AudioSegment-like object of the whole audio
        window_size: window size in milli seconds
        shift_value: shift value or seek points of the algo, the window is shifted by this value every iteration
        max_diff_thre: maximum difference that will be considered a change 
        method: 'avg' or minmax'
        function: 'dbfs' or 'rms'

        returns: generator of (position of cut in millis, boolean whether it increasing or decreasing change)
    '''
    return globals()[f"detectAudioChanges_{algo}"](audio, window_size, shift_value, max_diff_thre=6, function='dbfs')



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
    offsets = range(shift_value, audioLen - shift_value, shift_value)
    currentSum = getattr(audio[0: window_size], function)
    currentAvg = currentSum
    for windowsToken, offset in enumerate(offsets):
        currentValue = getattr(audio[offset: offset + window_size], function)
        diff = abs(currentValue, currentAvg)
        if diff > max_diff_thre:
            inc = currentValue > max_diff_thre
            yield currentValue, inc
        currentAvg = currentSum / (windowsToken + 1)


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
        if (abs(currentMax - currentMin) >= max_diff_thre):
            # see what current dbfs close to (min or max) => to know at this offset the change was increasing or decreasing
            # false mean decreasing (we cut here because of the value decreased), true mean increasing (we cut because of increasing)
            inc = abs(dbfs - currentMax) < abs(dbfs - currentMin)
            yield offset, inc
            currentMin = float("infinity")
            currentMax = -float("infinity")
        offset += shift_value