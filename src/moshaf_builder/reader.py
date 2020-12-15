from .data import AudioFile, Segment, ChapterLocation

class Reader:
    def __init__(self):
        super().__init__()

    @staticmethod
    def segments(path):
        '''read segments from .segments file. return list of Segment'''
        res = []
        with open(path) as f:
            segments = f.read().splitlines(False)
        for segment in segments:
            name, start, end = segment.split(' ')
            s = Segment(name, start, end)
            res.append(s)
        return res

    @staticmethod
    def chapters(path):
        '''read segments from .segments file. return list of Segment'''
        res = []
        with open(path) as f:
            chapters = f.read().splitlines(False)
        for chapter in chapters:
            chapter, globalStart = chapter.split(' ')
            s = ChapterLocation(chapter, globalStart)
            res.append(s)
        return res