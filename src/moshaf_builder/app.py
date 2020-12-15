import os
from glob import glob

from functions.splitter import SalahSplitter
from functions.chapterfinder import ChapterFinder
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
        self.files.append(file)
        if(inDirInfo):
            self._loadFileInfo(file)

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
        self.files[fileIndex].segments[segmentIndex].chapters.clear()

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
        return [s.chapters for f in self.files for s in f.segments]

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
                audio = audioFile.loadAudio()
                audio = self.splitter.prepareAudio(audio)
                for label in self.splitter.split(audio, grouping=1, returnAudio=False):
                    scp, ecp = label['scp'], label['ecp']
                    seg = Segment(label['snum'], scp, ecp)
                    audioFile.addSegment(seg)
        if(chapters):
            targets = (s for audioFile in self.files for s in audioFile.segments if(len(s.chapterLocations) > 0))
            for seg in targets:
                for chapterIndex, chapterLocation in self.finder.find(seg.sourceFile.path, seg.start, seg.end):
                    c = ChapterLocation(chapterIndex, chapterLocation)
                    seg.addChapter(c)

    def build(self):
        '''
            main function, build the moshaf from segments and chapters
        '''
        # __s1__   __s2__   __s3__   __s4__   __s5__
        # __c_c_   __s2__   __c___   __s4__   __s5__
        # __s1__   __s2__   __s3__   __s4__   __s5__ 
        self.moshaf = []
        allChapters = [c for c in chapters for chapters in self.getChapters()]
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
    
    def save(self):
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
    
    def _removeDuplicates(self):
        return list(dict.fromkeys(self.files))