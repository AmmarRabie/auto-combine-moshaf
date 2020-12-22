

class Writer:
    def __init__(self):
        super().__init__()


    @staticmethod
    def inDirChapters(files):
        for currentFile in files:
            audioPath = currentFile.path
            audioExt = audioPath.split('.')[-1]
            chaptersPath = audioPath.replace(audioExt, "chapters.mb")
            fileChapters = [c for seg in currentFile.segments for c in seg.chapterLocations]
            with open(chaptersPath, 'wt') as f:
                for c in fileChapters:
                    name, start, end = c.chapter, c.globalStart, c.globalEnd
                    f.write(f"{start}\t{end}\t{name}\n")
                    
    @staticmethod
    def inDirSegments(files):
        raise NotImplementedError()

    @staticmethod
    def inDirSegmentsAudio(files):
        raise NotImplementedError()

    @staticmethod
    def inDirChaptersAudio(files):
        raise NotImplementedError()

    @staticmethod
    def moshafAudio(moshaf):
        raise NotImplementedError()

