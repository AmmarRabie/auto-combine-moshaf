'''
    This module should be able to create a text file creating all chapters it founds with the beginning of it and the end
    It works over multiple folders and files not only one
'''
# first of all, for each audio file, output what is the beginning index and what is the end index ==> the result is directed to a txt file
# then another module who know where is the chapters indexes are => and label the files that have the beginning of a chapter
# this file should be deeply analysed to find the actual position of chapter
from sys import path
path.append("../")
from asr import ASR, QuranASR
from sentmatacher.SentMatcher import SentMatcher
from myutils import getFileLength

class QuranChaptersFinder():
    def __init__(self):
        pass

    @classmethod
    def fromScratch(cls):
        self = cls()
        self.asr = ASR()
        self.sentMatcher = SentMatcher(corpus="../quran-simple-clean.txt")

    @classmethod
    def fromAudioLabeling(cls, audioLabeling):
        self = cls(audioLabeling.basedir)
        self.asr = audioLabeling.asr
        self.sentMatcher = audioLabeling.sentMatcher

    def getChaptersPositions(self, filePath, fileLabels):
        '''
            filepath: audio file path
            fileLabels: a dictionary of the labels contaning first and last indexes of verses in the file (usually generated from audiolabeling class)
            this function tends to get where the whole chapters within this audio
        '''
        # validate first the firstIndex and lastIndex
        # get a list of chapters that is presented between two indexes
        # try to make a formula to initialize the window in most probably region that have the beginning of the chapter
        # use QuranAsr with corpus contaning only the first verses of chapters to get it quickly and with good performance

        # for now, this function is scanning the file and find if it noisy or not
        duration = 15 # in seconds
        starts = range(0, 10*60*60*1000, duration)
        unrecognizedTime = 0
        for s in starts:
            text = self.asr.recognizeGoogle(filePath, start=s, duration=duration)
            print("asr text:", text)
            # text = text[::-1]
            unrecognizedTime += text == None
            if text:
                print("text:", text)
                result = self.sentMatcher.match(text)
                print("sentMatcher result:", result)
            if (unrecognizedTime == 7):
                print("file is so noisy, we can't find any word in it")
                return
            return
    def _getChaptersInRegion(self, fromIndex = 1, toIndex = 6236):
        chapters = None
        with open("chapters_begin_end.txt", 'r') as chaptersPosFile:
            chapters = chaptersPosFile.read().splitlines(False)
        res = []
        for chapter in chapters:
            sura, start, end = [int(x) for x in chapter.split(" ")]
            if (start >= fromIndex and start <= toIndex):
                # beginning of the chapter in this region
                res.append({"sura": sura, 'actualLocation': start, 'type':'start'})
            if (end >= fromIndex and end <= toIndex):
                # end of the chapter in this region
                res.append({"sura": sura, 'actualLocation': end, 'type':'end'})
        return res
import os
from math import floor
from myutils import QuranPersistor as QuranPersistor
import json
class AudioLabeling:
    def __init__(self, corpusPath = "../quran-simple-clean.txt"):
        self.quranAsr = QuranASR(corpusLocation=corpusPath)
    
    def labelFiles(self, inputPath, outFileLocation = None):
        outFileLocation = outFileLocation or os.path.join(os.path.dirname(inputPath), f"{os.path.basename(inputPath)}_labels.json")
        runs = []
        with open(inputPath, encoding="utf-8") as f:
            origInput = f.read().splitlines(False)
            # origInput = [r.split(" ") for r in runs]
            print(origInput)
            for run in origInput:
                if(os.path.isfile(run)):
                    runs.append(run)
                else:
                    runs.extend([ os.path.join(root, filename) for root, subdirs, files in os.walk(run) if len(subdirs) == 0 for filename in files])
        if (len(runs) == 0):
            raise Exception("runs can't be zero, make sure that your file is correct or if it a folder that contains audio files")
        res = {}
        totalScore = 0
        for target in runs:
            abspath = os.path.abspath(target)
            firstAyaIndex, lastAyaIndex, score = self.labelOne(abspath)
            res[abspath] = {"first of file aya index": firstAyaIndex, "end of file aya index": lastAyaIndex, "score": score}
            if firstAyaIndex:
                totalScore += score
                res[abspath]["faya"] = QuranPersistor.quran()[firstAyaIndex]
                res[abspath]["laya"] = QuranPersistor.quran()[lastAyaIndex]
        res["total-score"] = totalScore / len(runs)
        with open(outFileLocation, 'w', encoding="utf-8") as outFile:
            outFile.write(json.dumps(res))
    def labelOne(self, filePath):
        totalLength = getFileLength(filePath)
        lengthToListen = 30 # 15 seconds
        firstAyaIndex, _,  s1 = self.quranAsr.recognizeGoogle(filePath, start=0, duration=lengthToListen)
        _, lastAyaIndex, s2 = self.quranAsr.recognizeGoogle(filePath, start=floor(totalLength) - lengthToListen, duration=lengthToListen)
        if not (firstAyaIndex and lastAyaIndex):
            # raise(f"file {filePath} can't be labeled {firstAyaIndex} {lastAyaIndex}")
            return None, None, None
        return firstAyaIndex, lastAyaIndex, (s1 + s2) / 2

if __name__ == "__main__":
    # print(QuranChaptersFinder()._getChaptersInRegion(1, 492))
    labeler = AudioLabeling()
    labeler.labelFiles("input.txt")