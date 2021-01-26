from typing import TypedDict
import logging
import os

from pydub import AudioSegment

from .interface import ISplitter
from models.waveform_data import WaveformData
from core.onset_detection import (
    AudioChangeDetector,
    AudioSegmentAdapter,
    AudioWaveformAdapter,
)
from core.onset_detection.interface import IDetectorData, IAudioChangeDetector
from helpers.utils import timeRepr, groupclosest


class Splitter(ISplitter):
    def __init__(
        self,
        detector: IAudioChangeDetector,
        fineDetector: IAudioChangeDetector,
        useFiltering=None,
        useAdjusting=None,
        useGrouping=None,
        usePostFiltering=None,
        bypassFiltering=False,
        bypassAdjusting=False,
        bypassGrouping=False,
        bypassPostFiltering=None,
    ):
        self.useFiltering = useFiltering
        self.useAdjusting = useAdjusting
        self.useGrouping = useGrouping
        self.usePostFiltering = usePostFiltering
        self.bypassFiltering = bypassFiltering
        self.bypassAdjusting = bypassAdjusting
        self.bypassGrouping = bypassGrouping
        self.bypassPostFiltering = bypassPostFiltering
        self.detector = detector
        self.fineDetector = fineDetector

        # fine detector look outbound (of first suggests range) by which value
        self.min_duration_time = 50  # min duration time for a range
        self.fd_lookOutbound = self.detector.window_size
        self.max_group_to_largest_diff = 20  # if one group have the value smaller than largest group by this value, this group will be ignored (considered silence according to the file)
        self.same_group_tolerance = 5  # if two ranges percentages is lessthan this value, they will be in the same group

    # acts like a factory method for adapters
    def prepareAudio(self, source) -> IDetectorData:
        data = source  # stores .dat file content
        if isinstance(source, str):  # path
            if source.endswith(".dat"):
                data = WaveformData(source)
            else:
                data = AudioSegment.from_file(source)
        if isinstance(data, AudioSegment):
            data = AudioSegmentAdapter(data)
        elif isinstance(data, WaveformData):
            data = AudioWaveformAdapter(data)

        if not isinstance(data, AudioSegmentAdapter) and not isinstance(
            data, AudioWaveformAdapter
        ):
            raise TypeError(
                "source of prepare audio should be path to .dat file or audio file, AudioSegment, WaveformData, AudioSegmentAdapter or AudioWaveformAdapter"
            )
        return data

    def split(self, source):
        # prepare
        audioDetectorData = self.prepareAudio(source)

        # get change points locations
        changePoints = self.detector.detect_minmax(audioDetectorData)
        changePoints = list(changePoints)  # TODO: how to make it online ?

        # transform change points locations into usefull ranges
        ranges = self.calcRanges(audioDetectorData, changePoints)
        logging.info(f"ranges:")
        print(ranges)

        # filtering (runs on ranges)
        if not self.bypassFiltering:
            ranges = self.filter(audioDetectorData, ranges)
        if self.useFiltering:
            ranges = self._execPipe(
                self.useFiltering,
                ranges,
                [
                    audioDetectorData,
                ],
            )
        logging.info(f"ranges after filtering:")
        print(ranges)

        # adjusting (should not add any new range or remove)
        if not self.bypassFiltering:
            # ? should we instead use another value, to cache original suggestion
            ranges = self.adjust(audioDetectorData, ranges)
        if self.useAdjusting:
            ranges = self._execPipe(
                self.useAdjusting,
                ranges,
                [
                    audioDetectorData,
                ],
            )
        logging.info(f"ranges after adjusting:")
        print(ranges)

        # grouping
        ## some sort of validation checking
        if self.bypassGrouping and not self.useGrouping:
            raise ValueError(
                "Invalid state, you should provide useGrouping when bypassing default group function"
            )
        if not self.bypassGrouping and self.useGrouping:
            logging.warning(
                "bypassing default grouping to use 'useGrouping' user functions"
            )
        if self.useGrouping:
            groups = self._execPipe(
                self.useGrouping,
                ranges,
                [
                    audioDetectorData,
                ],
            )
        elif not self.bypassGrouping:
            groups = self.group(audioDetectorData, ranges)

        # post filtering (runs on groups)
        if not self.bypassPostFiltering:
            groups = self.postFiltering(audioDetectorData, ranges, groups)
        if self.usePostFiltering:
            groups = self._execPipe(
                self.useGrouping,
                ranges,
                [
                    audioDetectorData,
                ],
            )

        return groups

    def calcRanges(self, audioDetectorData, changePoints):
        if len(changePoints) == 0:
            logging.info(f"number of changes = 0")
            logging.info("seems that you have no sound in this audio")
            return []
        self._correctStartEndProblem(audioDetectorData, changePoints)
        return tuple(
            (lastPos[0], pos[0])
            for lastPos, pos in zip(changePoints, changePoints[1:])
            if (lastPos[1] and (not pos[1]))
        )

    def filter(self, audioDetectorData, ranges):
        originalCount = len(ranges)
        if originalCount == 0:
            return ranges

        # general filtering function
        def f(ranges, shouldRemove):
            resRanges = []
            for currentRange in ranges:
                startTime, endTime = currentRange
                remove, text = shouldRemove(ranges, startTime, endTime)
                if not remove:
                    resRanges.append(currentRange)
                    continue
                logging.info(
                    f"ignoring sound from {timeRepr(startTime)} to {timeRepr(endTime)}: {text}"
                )
            return resRanges

        # 1. filter by range duration time
        def f1(ranges, start, end):
            duration = end - start
            remove = duration < self.min_duration_time
            text = (
                f"{duration} is less that min duration time of {self.min_duration_time}"
            )
            return remove, text

        ranges = f(ranges, f1)
        return ranges

    def adjust(self, audioDetectorData, ranges):
        adjustedRanges = []
        for i, currentRange in enumerate(ranges):
            start, end = currentRange
            start = max(0, start - self.fd_lookOutbound)
            end = min(audioDetectorData.duration, end + self.fd_lookOutbound)
            changePoints = self.fineDetector.detect_minmax(
                audioDetectorData, start=start, end=end
            )
            changePoints = list(changePoints)  # TODO: how to make it online ?
            print(f"new change points from {currentRange[0]} to {currentRange[1]}")
            print(changePoints)
            self._correctStartEndProblem(audioDetectorData, changePoints)
            newRanges = self.calcRanges(audioDetectorData, changePoints)
            if len(newRanges) == 1:
                newStart, newEnd = newRanges[0]
                logging.info(
                    f"adjusting range [{timeRepr(start)}__{timeRepr(end)}] to be [{timeRepr(newStart)}__{timeRepr(newEnd)}]"
                )
                adjustedRanges.append(newRanges[0])
            else:
                logging.warning(
                    f"adjusting range from {timeRepr(start)} to {timeRepr(end)} doesn't return one range, find {len(newRanges)} new ranges, return range before adjusting"
                )
                adjustedRanges.append(currentRange)
        return adjustedRanges

    def group(self, audioDetectorData, ranges):
        percentages = [
            audioDetectorData.percentage(audioDetectorData.detectionValue(s, e))
            for s, e in ranges
        ]
        print(percentages)
        rangesWithPerc = [
            (percentage, rng) for percentage, rng in zip(percentages, ranges)
        ]
        groups = groupclosest(rangesWithPerc, tolerance=self.same_group_tolerance)
        return groups

    def postFiltering(self, audioDetectorData, ranges, groups):
        # filter low group percentages
        print(groups)
        if not groups or len(groups) == 0:
            return groups  # nothing to do here
        groupAverages = tuple(sum(p for p, _ in g) / len(g) for g in groups)
        maxAvg = max(groupAverages)
        groups = filter(
            lambda ix_grp: maxAvg - groupAverages[ix_grp[0]]
            <= self.max_group_to_largest_diff,
            enumerate(groups),
        )
        return list(zip(*groups))[1]

    def _execPipe(self, functions, startValue, constants):
        lastRes = startValue
        for f in functions:
            lastRes = f(*constants, lastRes)
        return lastRes

    def _correctStartEndProblem(self, audio: IDetectorData, changePoints):
        logging.info("try to correct if start with sound or end with sound probelm")
        count = len(changePoints)
        if count == 0:
            return  # nothing to do with empty list
        if not changePoints[0][1]:
            logging.warning(
                "oh, first cut position was decreasing, we will add an increasing in the beginning"
            )
            changePoints.insert(0, (0, True))
        if changePoints[-1][1]:
            logging.warning(
                "oh, last cut position was increasing, we will add a decreasing in the end"
            )
            changePoints.append((audio.duration, False))


# class IFilter(object):
#     def __init__(self):
#         super().__init__()

#     def filter(self, audioDetectorData, ranges):
#         pass

# def createFilter(callback) -> Filter:
#     newFilter = type(f'Filter_{callback.__name__}', (IFilter,), {
#         "__init__": lambda: (), # empty init
#         "filter": lambda self, audioDetectorData, ranges: callback(audioDetectorData, ranges)
#     })

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("main")
    basicDetector = AudioChangeDetector(30, 15, 15)
    fineDetector = AudioChangeDetector(2, 1, 30)
    splitter = Splitter(basicDetector, fineDetector)
    groups = splitter.split(
        "C:\\Data\\workspace\\qur2an salah splitter\\audio_tests\\ex1.dat"
    )
    print(groups)
