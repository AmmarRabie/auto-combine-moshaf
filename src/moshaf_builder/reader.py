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
            start, end, name = segment.split('\t')
            s = Segment(name, float(start), float(end))
            res.append(s)
        return res

    @staticmethod
    def chapters(path):
        '''read segments from .segments file. return list of Segment'''
        res = []
        with open(path) as f:
            chapters = f.read().splitlines(False)
        for chapter in chapters:
            chapter, globalStart = chapter.split('\t')
            s = ChapterLocation(chapter, globalStart)
            res.append(s)
        return res