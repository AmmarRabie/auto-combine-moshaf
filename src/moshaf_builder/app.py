import os
import logging
from multiprocessing import Pool
import json
from datetime import datetime
from itertools import groupby

from functions.splitter import SalahSplitter
from functions.chapterfinder import ChapterFinder
from helpers.commands import generateDatFile
from helpers.utils import replaceExt
from .writer import Writer
from .reader import Reader
from .data import AudioFile, Segment, ChapterLocation

class MoshafBuilder():

    def __init__(self):
        super().__init__()
        self.audioExtSupported = ['wav',]
        self.files = []
        self.moshaf = []
        self.splitter = SalahSplitter()
        self.finder = ChapterFinder()

    def addFile(self, file, inDirInfo=False):
        '''Add file to the project'''
        if(not isinstance(file, AudioFile)):
            file = AudioFile(file)
            # raise ValueError("MoshafBuilder.addFile: file should be AudioFile")
        if(inDirInfo):
            self._loadFileInfo(file)
        if(not file.datPath):
            # generate dat file and point to it
            logging.info(f"generating dat file for {file.path} in same dir")
            datPath = replaceExt(file.path, "dat")
            generateDatFile(file.path, datPath)
            logging.info(f"done generating (written)")
            file.datPath = datPath
        self.files.append(file)

    def addFolder(self, folderPath, inDirInfo=False):
        '''
        Add all supported files under given folder to the project
        @inDirInfo: if True, .segments, .chapters files inside the folder
                    will be loaded if exists to corresponding file
        '''
        audioFilesGenerator = self._walk(folderPath, self.audioExtSupported)
        for audioFilePath in audioFilesGenerator:
            audioFile = AudioFile(audioFilePath)
            self.addFile(audioFile, inDirInfo=inDirInfo)
    
    def updateFileSegments(self, fileIndex, segments):
        self.files[fileIndex].addSegments(segments)

    def updateSegmentChapters(self, fileIndex, segmentIndex, chapters):
        self.files[fileIndex].segments[segmentIndex].addChapters(chapters)

    def clear(self):
        self.files = []
        self.moshaf = []

    def clearFileSegments(self, fileIndex):
        self.files[fileIndex].segments.clear()

    def clearSegmentChapters(self, fileIndex, segmentIndex):
        self.files[fileIndex].segments[segmentIndex].chapterLocations.clear()

    def getFiles(self):
        '''return files in this project. list of AudioFile'''
        return self.files

    def getSegments(self):
        '''return segments of each file in this project if exists. segments calculated in compile or manual by user
        returns list of list of segments. first index indicates file and second index indicates segment'''
        return [f.segments for f in self.files]

    def getChapters(self):
        '''return chapters in each segment of each file
        returns list of list of chapters. first index indicates segment in inflated count, second index indicates chapter'''
        return [s.chapterLocations for f in self.files for s in f.segments]

    def compile(self, segments=True, chapters=True, checkDuplicates=True):
        '''
        find segments(if segments = True) and chapters(if chapters = True) in each segment for all files
        if file has one or more segments already loaded in it. file is escaped
        if segment has one or more chapters already loaded in it. segment is escaped
        so you might want to clear all before compiling
        '''
        # TODO: support threading here
        if(checkDuplicates):
            self.files = self._removeDuplicates()
        if(segments):
            for audioFile in self.files:
                if(len(audioFile.segments) > 0): continue
                audio = audioFile.availablePath # returns dat path if exist, otherwise wav path
                audio = self.splitter.prepareAudio(audioFile.path)
                for igroup, group in enumerate(self.splitter.split(audio)):
                    for irange, rng in enumerate(group):
                        scp, ecp = rng[1]
                        label = f"G{igroup + 1}_{irange + 1}"
                        seg = Segment(label, scp, ecp)
                        audioFile.addSegment(seg)
        if(chapters):
            agents = 4 # my number of cores, TODO: make it number of logical cores
            chunksize = 3
            targets = [s for audioFile in self.files for s in audioFile.segments if(len(s.chapterLocations) == 0)]
            # with Pool(processes=agents) as pool:
            #     r = pool.map(self._action, targets, chunksize)
            for seg in targets:
                p, s, e = seg.sourceFile.path, seg.start, seg.end
                print(f"process finding file={p} from {s} to {e} (segment #{seg.name})")
                if(seg.processed):
                    print("ignoreing as it is processed before")
                    continue
                if(seg.name == 'watr'):
                    print("ignoreing as it is not salah, it is the watr")
                    continue
                print("start at", datetime.now().time())
                chaptersResults = self.finder.find(p, s, e)
                if(chaptersResults == None):
                    print("unexpected error, can't process this segment")
                    continue
                for info in chaptersResults:
                    aya = info['best_aya']
                    c = ChapterLocation(aya["sura"], info["expected_start"], info["expected_end"], extras=info)
                    seg.addChapter(c)
                print("end at", datetime.now().time())
                seg.processed = True
                self.save()
    # def _action(self, seg):
    #     for chapterIndex, chapterLocation in self.finder.find(seg.sourceFile.path, seg.start, seg.end):
    #         c = ChapterLocation(chapterIndex, chapterLocation)
    #         seg.addChapter(c)

    def build(self):
        '''
            main function, build the moshaf from segments and chapters
        '''
        # __s1__   __s2__   __s3__   __s4__   __s5__
        # __c_c_   __s2__   __c___   __s4__   __s5__
        # __s1__   __s2__   __s3__   __s4__   __s5__ 
        self.moshaf = []
        allChapters = [c for chapters in self.getChapters() for c in chapters]
        chapter_key = lambda chapter: chapter.chapter
        allChapters.sort(key=chapter_key)
        groups = groupby(allChapters, key=chapter_key)
        for chapter, chapterParts in groups:
            chapterParts = list(chapterParts)
            chapterParts.sort(key= lambda chapter: chapter.extras["best_aya"]["index"])
            print(f"Chapter #{chapter}")
            parts = []
            for p in chapterParts:
                parts.append({
                    "sourceFile": p.sourceSegment.sourceFile.path,
                    "start": p.globalStart,
                    "end": p.globalEnd
                })
            self.moshaf.append({
                "chapter": chapter,
                "parts": parts
            })
        return

        def buildAssumeSort():
            for i in range(1, len(allChapters)):
                c2 = allChapters[i]
                c1 = allChapters[i - 1]
                f1, f2 = c1.sourceSegment.sourceFile, c2.sourceSegment.sourceFile
                if f1 == f2:
                    parts = [{
                        "sourceFile": f1.path,
                        "globalStart": c1.globalStart,
                        "globalEnd": c2.globalStart,
                    }]
                else:
                    parts = [{
                        "sourceFile": f1.path,
                        "globalStart": c1.globalStart,
                        "globalEnd": f1.duration,
                    },{
                        "sourceFile": f2.path,
                        "globalStart": 0,
                        "globalEnd": c2.globalEnd,
                    }]
                self.moshaf.append({
                    "chapter": c1.chapter,
                    "parts": parts,
                })
            return self.moshaf
        return buildAssumeSort()

    def save(self):
        # TODO: support custom paths,...
        projStr = json.dumps({
            "project": {
                "files": self.files,
                "moshaf": self.moshaf,
            }
        }, default=dumper)
        with open("tmp.mb", 'w') as f:
            f.write(projStr)

    def load(self):
        p = "tmp.mb"
        with open(p, encoding="utf-8") as f:
            projDict = json.loads(f.read())['project']
        filesDict = projDict['files']
        moshafArr = projDict['moshaf']
        for fileDict in filesDict:
            self.files.append(AudioFile.from_dict(fileDict))
        self.moshaf = moshafArr

    def exportMoshaf(self, rootPath):
        if(len(self.moshaf) == 0):
            return print("Build first before export")
        Writer.moshafAudio(self.moshaf, rootPath)
        pass

    def _commonPath(self):
        '''
        return common path of all source files ("C:\\Data\\alquran kamel\\")
        '''
        pass
    def _walk(self, path, extSupported, returnList=False):
        resGenerator = (os.path.join(root, filename) for root, subdirs, files in os.walk(path) 
            for filename in files if (filename.split(".")[-1].lower() in extSupported))
        if(returnList): return list(resGenerator)
        return resGenerator

    def _loadFileInfo(self, audioFile):
        audioFilePath = audioFile.path
        audioExt = audioFilePath.split('.')[-1]
        hypoSegmentFilePath = audioFilePath.replace(audioExt, 'segments')
        hypoChapterLocationsFilePath = audioFilePath.replace(audioExt, 'chapters')
        hypoDatFilePath = audioFilePath.replace(audioExt, 'dat')
        segments = []
        if(os.path.exists(hypoSegmentFilePath)):
            segments = Reader.segments(hypoSegmentFilePath)
            audioFile.addSegments(segments)
        if(os.path.exists(hypoChapterLocationsFilePath)):
            chapters = Reader.chapters(hypoChapterLocationsFilePath)
            for chapter in chapters:
                chapterInSegment = lambda seg: chapter.globalStart >= seg.start and chapter.globalStart <= seg.end
                targetSeg = next(filter(chapterInSegment, segments), None)
                if(targetSeg == None):
                    audioFile.pendingChapters.append(chapter) # TODO: support this functionality
                else:
                    targetSeg.addChapter(chapter)
        if(os.path.exists(hypoDatFilePath)):
            audioFile.datPath = hypoDatFilePath
    
    def _removeDuplicates(self):
        return list(dict.fromkeys(self.files))

def dumper(obj):
    if hasattr(obj, "__serialize__"):
        return obj.__serialize__()
    return obj.__dict__