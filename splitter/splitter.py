from .audio_manipulation import detectAudioChanges
from myutils import *
import logging
import os
from pydub import AudioSegment
from ticktock import tick, tock # TODO: remove this line after testing
# logging.basicConfig(level=logging.INFO)

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

        # fixed thre
        self.adjust_max_offset = 5 * 60 * 1000
        self.append_silence_before_run = True

        #* groups thre
        self.same_group_tolerance = 2 # if two ranges dbfs is lessthan this value, they will be in the same group
        self.largest_group_diff = 15 # if one group have the value smaller than largest group by this value, this group will be ignored (considered silence according to the file)
    
    def prepareAudio(self, audio):
        '''
            prepare audio for splitting.
            this function should be called before splitting the audio
            now all it do is adding silence at the begin and at the end
            but in the future we may make any other advanced transformations for this audio segment, so make sure
            that before splitting call it e.g 'audio = prepareAudio(audio)' so that split is working best
        '''
        print("preparing audio")
        silenceAdded = False
        if (self.append_silence_before_run):
            if (hasattr(audio, "setleft") and hasattr(audio, "setright")):
                print("audio is smart wav")
                audio.setleft(duration=self.initial_window_size)
                audio.setright(duration=self.initial_window_size)
                silenceAdded = True
            elif(hasattr(audio, "append") and audio.append):
                print("audio is audiosegment")
                silence = AudioSegment.silent(frame_rate=audio.frame_rate, duration=self.initial_window_size)
                audio = silence.append(audio.append(silence)) # to make sure that we will find changes if file has sound
                silenceAdded = True
            else:
                # logging.warn("this audio can't be prepared successfully, try to make it audiosegment or smart wav")
                print("this audio can't be prepared successfully, try to make it audiosegment or smart wav")
        return audio

    def groupSoundRanges(self, audio, ranges):
        tick("[groupSoundRanges]: getting all ranges")
        ranges = list(ranges)
        print("ranges:", ranges)
        if (len(ranges) == 0):
            ranges = [audio.dBFS, (0, len(audio))]   # TODO: this logic shouldn't be here
        tock()
        tick("calculating all dbfs of the ranges...")
        alldbfs = [averageDbfs for averageDbfs, _ in ranges]
        tock()
        ranges = [soundRange for _, soundRange in ranges]
        largest = max(alldbfs)
        # ranges = zip(alldbfs, ranges)
        ranges = filter(lambda obj: largest - obj[0] < self.largest_group_diff, zip(alldbfs, ranges))
        groups = self._groupclosest(ranges)
        print("Groups =", groups)
        return groups

    def split(self, audio, countFrom = 1, grouping="no"):
        '''
            :param grouping: "no" for no grouping, "all" for returning all groups or int > 0 representing the max number of groups
        '''
        def proccessGroup(group):
            soundNumber = countFrom
            for _, soundrange in group: # highest group only
                sound = audio[soundrange[0]:soundrange[1]]
                yield {
                    "audio": sound,
                    "snum": soundNumber,
                    "scp": soundrange[0],
                    "ecp": soundrange[1],
                }
                soundNumber += 1
        isGroup = grouping != "no"
        rangesGenerator = self._split(audio)
        if(isGroup):
            groups = self.groupSoundRanges(audio, rangesGenerator)
            if(grouping != "all"): groups = groups[:grouping]
            for groupNumber, group in enumerate(groups):
                for v in proccessGroup(group): yield {"gnum": groupNumber, **v}
        else:
            for v in proccessGroup(rangesGenerator): yield {"gnum": "", **v}


    def _split(self, audio): # ranges()
        cutPositions = detectAudioChanges(audio,
            window_size=self.initial_window_size,
            shift_value=self.initial_shift_value,
            max_diff_thre=self.initial_diff_thre,
            function="dBFS",
            algo="minmax")
        cutPositions = list(cutPositions) # TODO try to make it online
        if (len(cutPositions) <= 1):
            logging.warn(f"number of changes < 1 (={len(cutPositions)})")
            print("seems that you have no sound in this audio")
        self._correctStartEndProblem(audio, cutPositions)

        for lastPos, pos in zip(cutPositions, cutPositions[1:]):
            if(lastPos[1] and (not pos[1])): # transition from increasing to decreasing
                duration = pos[0] - lastPos[0]
                if (duration < self.min_duration_time): # remove short durations
                    logging.info(f"ignoring sound from {timeRepr(lastPos[0])} to {timeRepr(pos[0])}, {timeRepr(duration)} < {timeRepr(self.min_duration_time)}")
                    continue
                soundRange = lastPos[0], pos[0]
                soundRange = self._adjustSoundRage(audio, soundRange)
                averageDbfs = audio[soundRange[0]:soundRange[1]].dBFS
                yield averageDbfs, soundRange

    def splitWithExport(self, audio, outDir, outFormat, countFrom = 1):
        '''
        @deprecated
        outdir: the outdir including the file itself, function export to that dir directly (filename_soundnumber.wav)
        '''
        logging.warn("this function is deprecated. and will be removed from the splitter functionally")
        # sound.export(f"output/{inputPath.replace('.wav', '').replace('/', '.')}_{soundNumber}.wav", format="wav")
        os.makedirs(outDir, exist_ok=True)
        
        soundNumber = countFrom
        for _, soundrange in self._split(audio, grouping=True)[0]: # highest group only
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
                Try to move in both directions and sharped it
            '''
            # print("--------------- move -------------------", start)
            isBackward = shift < 0
            if (isBackward):
                windowSize = -windowSize
            getse = lambda offset: (offset + windowSize, offset) if isBackward else (offset, offset + windowSize)
            offset = start
            # if you want to move with positive shift (right, e.g when end) then you have to try moving left first if you are not in range
            # if the first window we take is less than the average, move the start opposite of direction and check again if it in the avg
            s, e = getse(offset)
            s = max(0, s)
            e = min(e, len(audio))
            # move the cursor backword first to make sure that it is in the range
            while (isDiff(audio[s:e].dBFS, averageDbfs, MAX_DIFF_THRE)): # while the difference
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
        '''
            groups returned structure is:
            [
                [(avgDBFS, (start, end)), (avgDBFS, (start, end)), (avgDBFS, (start, end))], # first group
                [(avgDBFS, (start, end)), (avgDBFS, (start, end))],                         # second group
                [(avgDBFS, (start, end))],
            ]
        '''
        #? 1. We may make this function by clustering points using machine learning kmeans algo
        #? 2. We want to use variance of every group, the variance give info about the rate of speaking ==> sound should have high variance
        groups = []
        rangeslist = sorted(rangeslist)[::-1]
        basei = 0
        for i, val in enumerate(rangeslist):
            if (abs(val[0] - rangeslist[basei][0]) > self.same_group_tolerance):
                newGroup = rangeslist[basei:i]
                newGroup = sorted(newGroup, key=lambda x: x[1][0]) # sort over the start point
                # print("newGroup", newGroup)
                # groups.append(rangeslist[basei:i])
                groups.append(newGroup)
                basei = i
        lastGroup = rangeslist[basei:len(rangeslist)]
        lastGroup = sorted(lastGroup, key=lambda x: x[1][0])
        # print("lastgroup", lastGroup)
        groups.append(lastGroup)
        return groups

    def _correctStartEndProblem(self, audio, cutPositions):
        print("try to correct if start with sound or end with sound probelm")
        if (len(cutPositions) and not cutPositions[0][1]):
            print("oh, first cut position was decreasing, we will add an increasing in the beginning")
            cutPositions.insert(0, (0, True))
        if (len(cutPositions) and cutPositions[-1][1]):
            print("oh, last cut position was increasing, we will add a decreasing in the end")
            cutPositions.append((len(audio), False))

def main(audio, outDir, outFormat):
    s = SalahSplitter()
    audio = s.prepareAudio(audio)
    s.splitWithExport(audio, outDir, outFormat)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    from sys import argv
    import pydub

    inputPath = "../tests/ex1.wav"
    outFormat = "wav"
    if (len(argv) >= 2):
        inputPath = argv[1]
    if (len(argv) >= 3):
        outFormat = argv[2]
    audio = pydub.AudioSegment.from_file(f"./{inputPath}")
    # main(audio, f"output/{inputPath.replace('.wav', '').replace('/', '.')}", outFormat)
    main(audio, f"tests", outFormat)
