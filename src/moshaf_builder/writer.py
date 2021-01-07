from pydub import AudioSegment
import pathlib
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
    def moshafAudio(moshaf, rootPath):
        for chapterInfo in moshaf:
            chapter = chapterInfo['chapter']
            parts = chapterInfo['parts']
            print(f"exporting {chapter} with {len(parts)} parts")
            p = parts[0]
            path, start, end = p["sourceFile"], p["start"], p["end"]
            start, end = int(start * 1000), int(end * 1000)
            chapterAudio = AudioSegment.from_file(path)[start:end]
            if(len(parts) > 1):
                for p in parts[1:]:
                    path, start, end = p["sourceFile"], p["start"], p["end"]
                    start, end = int(start * 1000), int(end * 1000)
                    chapterAudio += AudioSegment.from_file(path)[start:end]
            exportPath = pathlib.Path(rootPath).joinpath(str(chapter) + ".mp3").resolve()
            chapterAudio.export(exportPath, format="mp3")
