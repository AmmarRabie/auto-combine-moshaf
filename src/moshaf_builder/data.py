from collections import namedtuple
from pydub import AudioSegment
from audio_metadata import load as audioInfo
from pathlib import Path
# AudioFile = namedtuple('AudioFile', ['path', 'segments'])
# Segment = namedtuple('Segment', ['audioFile', 'start', 'end', 'chapterLocations'])
# ChapterLocation = namedtuple('ChapterLocation', ['segment', 'globalStart', 'globalEnd', 'start', 'end'])


class AudioFile:
    def __init__(self, path, segments=None):
        super().__init__()
        self.path = path
        self.segments = segments or []
        self.pendingChapters = [] # chapters that doesn't added to any segment yet

    def addSegment(self, segment):
        '''Add one segment with backref'''
        if(not isinstance(segment, Segment)):
            raise ValueError("Segment.addSegment: segment should be Segment instance")
        segment.sourceFile = self
        self.segments.append(Segment)
    
    def addSegments(self, segments):
        for s in segments: self.addSegment(s)
    
    def loadAudio(self):
        return AudioSegment.from_file(self.path)
        self.__str__

    @property
    def duration(self):
        return audioInfo(self.path)["streaminfo"]["duration"]

    def __repr__(self):
        return f"{self.path} ({len(self.segments)} segments)"

    def __eq__(self, other):
        return Path(self.path).samefile(Path(other.path))

    def __hash__(self):
        return hash(self.path)


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

class ChapterLocation:
    def __init__(self, chapter, globalStart, sourceSegment=None):
        super().__init__()
        if(sourceSegment != None and not isinstance(sourceSegment, Segment)):
            raise ValueError("init of Segment: audioFile should be Segment instance or None")
        self.chapter = chapter
        self.sourceSegment = sourceSegment
        self.globalStart = globalStart

    def __repr__(self):
        return f"{self.chapter} starting at {self.globalStart}"


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