# from pyo import *
from .audio_manipulation import detectAudioChanges
from myutils import *
import logging
from os import makedirs
from pydub import AudioSegment
from ticktock import tick, tock # TODO: remove this line after testing
# logging.basicConfig(level=logging.DEBUG)

# optimizations:
# in adjust range we can make a loop over adjust range with every time update the avergae dbfs after updating the range
# so it wil be (averageDBFS => adjust => averageDBFS => adjust => ..) till the convergence

# features:
# we need to detect allah okbar in the end: you may use the info that there is before the end there will be a little drop
from ticktock import tick, tock
class SalahSplitter:
    def __init__(self, initial_window_size = 0.5 * 60 * 1000, initial_shift_value = 1 * 1000, initial_diff_thre = 6,
     adjust_window_size = 3*1000, adjust_shift_value = 0.5*1000, adjust_diff_thre = 8, min_duration_time = 1 * 60 * 1000):
        self.initial_window_size = initial_window_size
        self.initial_shift_value = initial_shift_value
        self.initial_diff_thre = initial_diff_thre
        self.min_duration_time = min_duration_time
        self.adjust_window_size = adjust_window_size
        self.adjust_shift_value = adjust_shift_value
        self.adjust_diff_thre = adjust_diff_thre
        self.adjust_max_offset = 5 * 60 * 1000

        #* groups thre
        self.same_group_tolerance = 2 # if two ranges dbfs is lessthan this value, they will be in the same group
        self.largest_group_diff = 15 # if one group have the value smaller than largest group by this value, this group will be ignored (considered silence according to the file)
   
    def groupSoundRanges(self, audio, ranges):
        tick("[groupSoundRanges]: getting all ranges")
        ranges = list(ranges)
        tock()
        tick("calculating all dbfs of the ranges...")
        alldbfs = [audio[soundRange[0]:soundRange[1]].dBFS for soundRange in ranges]
        tock()
        largest = max(alldbfs)
        # ranges = zip(alldbfs, ranges)
        ranges = filter(lambda obj: largest - obj[0] < self.largest_group_diff, zip(alldbfs, ranges))
        groups = self._groupclosest(ranges)
        return groups
    
    def split(self, audio, grouping=False):
        # silence = AudioSegment.silent(frame_rate=audio.frame_rate, duration=self.initial_window_size)
        # audio = silence.append(audio.append(silence)) # to make sure that we will find changes if file has sound
        def ranges():
            cutPositions = detectAudioChanges(audio, window_size=self.initial_window_size, shift_value=self.initial_shift_value, max_diff_thre=self.initial_diff_thre, function="dBFS", algo="minmax")
            cutPositions = list(cutPositions)
            if (len(cutPositions) <= 1):
                logging.warn(f"number of changes < 1 (={len(cutPositions)})")
                print("seems that you have no sound in this audio")
            for lastPos, pos in zip(cutPositions, cutPositions[1:]):
                if(lastPos[1] and (not pos[1])): # transition from increasing to decreasing
                    duration = pos[0] - lastPos[0]
                    if (duration < self.min_duration_time): # remove short durations
                        logging.info(f"ignoring sound from {timeRepr(lastPos[0])} to {timeRepr(pos[0])}, {timeRepr(duration)} < {timeRepr(self.min_duration_time)}")
                        continue
                    soundRange = lastPos[0], pos[0]
                    soundRange = self._adjustSoundRage(audio, soundRange)
                    # sound = audio[soundRange[0]:soundRange[1]]
                    yield soundRange
        return ranges() if not grouping else self.groupSoundRanges(audio, ranges())

    def splitWithExport(self, audio, outDir, outFormat, countFrom = 1):
        # sound.export(f"output/{inputPath.replace('.wav', '').replace('/', '.')}_{soundNumber}.wav", format="wav")
        makedirs(outDir, exist_ok=True)
        
        soundNumber = countFrom
        for _, soundrange in self.split(audio, grouping=True)[0]: # highest group only
            sound = audio[soundrange[0]:soundrange[1]]
            sound.export(f"{outDir}/{soundNumber}.{outFormat}", format=outFormat)
            soundNumber += 1
        return soundNumber - countFrom
    def _adjustSoundRage(self, audio, initialRange):
        '''
            adjust the given start and end positions by applying shorter window size.
            It expects to increase the percession of your initial range
        '''
        logging.info(f"adjustSoundRage:{timeRepr(*initialRange)}")
        s, e = initialRange
        averageDbfs = audio[s:e].dBFS
        logging.info(f"averageDbfs:{averageDbfs}")
        MAX_DIFF_THRE = self.adjust_diff_thre # very large value mean no sharpen will happen
        # move left and right from s and 
        def move(start, shift, windowSize=self.adjust_window_size, maxOffset=self.adjust_max_offset):
            '''
                put the start in the range of average dbfs and then sharpen it
                when calling this method, you have to assume that the cursor start is in the average
            '''
            isBackward = shift < 0
            if (isBackward):
                windowSize = -windowSize
            getse = lambda offset: (offset + windowSize, offset) if isBackward else (offset, offset + windowSize)
            offset = start
            # if you want to move with positive shift (right, e.g when end) then you have to try moving left first if you are not in range
            # if the first window we take is less than the average, move the start opposite of direction and check again if it in the avg
            s, e = getse(offset)
            while (isDiff(audio[s:e].dBFS, averageDbfs, MAX_DIFF_THRE)):
                s -= shift
                e -= shift
                offset -= shift
                if (not (s < initialRange[1] and e > initialRange[0])):
                    logging.warn("can't find a position to start move algo from, bad range !!")
                    return start

            relativeOffset = 0
            while(abs(relativeOffset) <= maxOffset):
                s, e = offset, offset + windowSize
                if (isBackward):
                    s,e = e,s
                logging.info(f"{timeRepr(s, e)} diff= {abs(audio[s:e].dBFS - averageDbfs)}")
                if (isDiff(audio[s:e].dBFS, averageDbfs, MAX_DIFF_THRE)):
                    return offset + windowSize if isBackward else offset
                offset += shift
                relativeOffset += shift
            logging.info(f"end with no change, {timeRepr(relativeOffset)} > {timeRepr(maxOffset)}")
            return start
        getCloser = lambda center, v1, v2: v1 if abs(center - v1) < abs(center - v2) else v2
        startBias, endBias = 0, 500 # todo: remove this value or put in paramerers
        e = approxToNearestSeconds(move(e, self.adjust_shift_value))
        e = min(len(audio), e + endBias)
        s = move(s, -self.adjust_shift_value) #
        startBias = 0
        s = max(0, s - startBias)
        logging.info(f"return:{timeRepr(s, e, joint=' ==> ')}")
        return s, e

    def _groupclosest(self, rangeslist):
        groups = []
        rangeslist = sorted(rangeslist)[::-1]
        basei = 0
        for i, val in enumerate(rangeslist):
            if (abs(val[0] - rangeslist[basei][0]) > self.same_group_tolerance):
                groups.append(rangeslist[basei:i])
                basei = i
        groups.append(rangeslist[basei:len(rangeslist)])
        return groups

def main(audio, outDir, outFormat):
    s = SalahSplitter()
    s.splitWithExport(audio, outDir, outFormat)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    from sys import argv
    import pydub

    inputPath = "tests/ex1.wav"
    outFormat = "wav"
    if (len(argv) >= 2):
        inputPath = argv[1]
    if (len(argv) >= 3):
        outFormat = argv[2]
    audio = pydub.AudioSegment.from_file(f"./{inputPath}")
    main(audio, f"output/{inputPath.replace('.wav', '').replace('/', '.')}", outFormat)

def _groupclosest(rangeslist, thre):
    groups = []
    rangeslist = sorted(rangeslist)[::-1]
    basei = 0
    for i, val in enumerate(rangeslist):
        if (abs(val[0] - rangeslist[basei][0]) > thre):
            groups.append(rangeslist[basei:i])
            basei = i
    groups.append(rangeslist[basei:len(rangeslist)])
    return groups

rangeslist = [(1.0, (0, 5000)), (2.4, (600, 6000)), (3.5, (600, 6000))]
print(_groupclosest(rangeslist, 2.0))