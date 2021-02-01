from collections import namedtuple
from pydub import AudioSegment
from audio_metadata import load as audioInfo
from pathlib import Path
# AudioFile = namedtuple('AudioFile', ['path', 'segments'])
# Segment = namedtuple('Segment', ['audioFile', 'start', 'end', 'chapterLocations'])
# ChapterLocation = namedtuple('ChapterLocation', ['segment', 'globalStart', 'globalEnd', 'start', 'end'])


class AudioFile:
    def __init__(self, path, datPath=None, segments=None):
        super().__init__()
        self.path = path
        self.datPath = datPath
        self.segments = segments or []
        self.pendingChapters = [] # chapters that doesn't added to any segment yet
        self.processed = False

    def addSegment(self, segment):
        '''Add one segment with backref'''
        if(not isinstance(segment, Segment)):
            raise ValueError("Segment.addSegment: segment should be Segment instance")
        segment.sourceFile = self
        self.segments.append(segment)
    
    def addSegments(self, segments):
        for s in segments: self.addSegment(s)
    
    def loadAudio(self):
        return AudioSegment.from_file(self.path)
        self.__str__

    @property
    def duration(self):
        return audioInfo(self.path)["streaminfo"]["duration"]

    @property
    def availablePath(self):
        '''returns dat path if exist, otherwise wav path'''
        if(self.datPath): return self.datPath
        ext = self.path.split(".")[-1]
        datPath = self.path.replace("." + ext, ".dat")
        if(Path(datPath).exists()): return datPath
        return self.path

    def __repr__(self):
        return f"{self.path} ({len(self.segments)} segments)"

    def __eq__(self, other):
        return Path(self.path).samefile(Path(other.path))

    def __hash__(self):
        return hash(self.path)
    
    def __serialize__(self):
        d = {
            "path": self.path,
            "segments": self.segments,
            "pending_chapters": self.pendingChapters,
            "processed": self.processed,
        }
        if(self.datPath):
            d["data_path"] = self.datPath
        return d

    @classmethod
    def from_dict(cls, d):
        path, segments, pendingChapters = d['path'], d['segments'], d['pending_chapters']
        audioFile = cls(path)
        for seg in segments:
            seg = Segment.from_dict(seg)
            audioFile.addSegment(seg)
        for pendingChapter in pendingChapters:
            pc = ChapterLocation.from_dict(pendingChapter)
            audioFile.pendingChapters.append(pc)
        audioFile.processed = d.get('processed', False)
        audioFile.datPath = d.get('datPath', None)
        return audioFile


class Segment:
    def __init__(self, name, start, end, sourceFile = None, chapterLocations=None):
        super().__init__()
        if(sourceFile != None and not isinstance(sourceFile, AudioFile)):
            raise ValueError("init of Segment: audioFile should be AudioFile instance or None")
        self.sourceFile = sourceFile
        self.name = name
        self.start = start
        self.end = end
        self.chapterLocations = chapterLocations or []
        self.processed = False
        
    def addChapter(self, chapter):
        '''Add one chapter with backref'''
        if(not isinstance(chapter, ChapterLocation)):
            raise ValueError("Segment.addChapter: chapter should be ChapterLocation instance")
        chapter.sourceSegment = self
        self.chapterLocations.append(chapter)

    def addChapters(self, chapters):
        for c in chapters: self.addChapter(c)
    
    def __repr__(self):
        return f"{self.name}: from {self.start} to {self.end} ({len(self.chapterLocations)} chapters)"

    def __serialize__(self):
        return {
            "name": self.name,
            "start": self.start,
            "end": self.end,
            "chapters": self.chapterLocations,
            "processed": self.processed,
        }

    @classmethod
    def from_dict(cls, d):
        name, start, end, chapters = d['name'], d['start'], d['end'], d['chapters']
        segment = cls(name, start, end)
        for chapter in chapters:
            chapter = ChapterLocation.from_dict(chapter)
            segment.addChapter(chapter)
        segment.processed = d.get('processed', False)
        return segment


class ChapterLocation:
    def __init__(self, chapter, globalStart, globalEnd, sourceSegment=None, extras={}):
        super().__init__()
        if(sourceSegment != None and not isinstance(sourceSegment, Segment)):
            raise ValueError("init of Segment: audioFile should be Segment instance or None")
        self.chapter = chapter
        self.sourceSegment = sourceSegment
        self.globalStart = globalStart
        self.globalEnd = globalEnd
        self.processed = False
        self.extras = extras

    def __repr__(self):
        return f"{self.chapter} starting at {self.globalStart}"

    def __serialize__(self):
        return {
            "chapter": self.chapter,
            "globalStart": self.globalStart,
            "globalEnd": self.globalEnd,
            "processed": self.processed,
            "extras": self.extras
        }

    @classmethod
    def from_dict(cls, d):
        chapter, globalStart, globalEnd = d['chapter'], d['globalStart'], d['globalEnd']
        chapter = cls(chapter, globalStart, globalEnd)
        chapter.processed = d.get('processed', False)
        chapter.extras = d.get('extras', {})
        return chapter

'''
Project
    [AudioFile, AudioFile, ...]
AudioFile
    [Segment, Segment, ...]
Segment
    [ChapterLocation, ChapterLocation, ...]
'''
# class Segment(object):
#     def __init__(self, sourceFile):
#         super().__init__()
#         self.sourceFile = sourceFile