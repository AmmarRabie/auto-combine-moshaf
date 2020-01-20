def timeRepr(*millis, joint=", "):
    res = []
    for p in millis:
        seconds = p / 1000
        mins = seconds // 60
        remainSeconds = seconds - mins * 60
        res.append(f"{mins}:{remainSeconds}")
    if(len(millis) == 1):
        return res[0]
    # return res
    return joint.join(res)

from audio_metadata import load as fileInfo
def getFileLength(path):
    return fileInfo(path)["streaminfo"]["duration"]

from math import ceil
def approxToNearestSeconds(time):
    return ceil(time / 1000) * 1000

def isDiff(x, y, tolerance):
    return abs(x - y) > tolerance



class QuranPersistor:
    _quran = None
    _path = "../quran-simple-clean.txt"


    @staticmethod
    def quran():
        if (not QuranPersistor._quran):
            with open(QuranPersistor._path, 'r', encoding="utf-8") as quranFile:
                QuranPersistor._quran = quranFile.read().splitlines(False)
        return QuranPersistor._quran


if __name__ == "__main__":
    print(QuranPersistor.quran()[0:5])
