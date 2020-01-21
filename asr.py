import speech_recognition as sr
# from pydub import AudioSegment
from os import path
from myutils import timeRepr
from sentmatacher.SentMatcher2 import SentMatcher

def main():
    from myutils import QuranPersistor
    FILE_PATH = "tests/clean.wav"
    qasr = QuranASR(corpusLocation="quran-simple-clean.txt")
    fi, ei, score = qasr.recognizeGoogle(FILE_PATH, start=0)
    if (not fi):
        print(":(")
        return None
    print("first aya in the file is:", QuranPersistor.quran()[fi])
    print("last aya in the file is:", QuranPersistor.quran()[ei])

class ASR:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.lang = "ar-EG"
    def recognizeGoogle(self, filePath, start, duration=None):
        with sr.AudioFile(filePath) as source:
            audio = self.recognizer.record(source, offset=start, duration=duration)  # read the entire audio file
        try:
            return self.recognizer.recognize_google(audio, language=self.lang)
        except sr.UnknownValueError:
            return None

class QuranASR(ASR):
    def __init__(self, corpusLocation = "../quran-simple-clean.txt"):
        super().__init__()
        self.sentMatcher = SentMatcher(corpusLocation)

    def recognizeGoogle(self, filePath, start, duration=None):
        text = super().recognizeGoogle(filePath, start, duration=duration)
        print("asr text:", text)
        if not text:
            print("can't recognize your audio")
            return None, None, None
        indexesRange, score = self.sentMatcher.match(text)
        if not indexesRange:
            print("can't find the text recognized in the quran")
            return None, None, None
        return indexesRange[0], indexesRange[1], score

if __name__ == "__main__":
    main()


#* إن لهجة بلاد الشام المتمثلة بسوريا والأردن وفلسطين الحديثة وليست القديمة قريبة جداً من اللغة الفصحى
#* the speech_recognition have nice ability recognize_google(preferred_phrases), use it at the phase of corrections (we will know what is the ayat we are in, this will be the prefered phrases)




# for determining whether or not the file is quran or not, we may add features to know:
    # number of chars, words said in one minute (speed of speaker)
    # score of SentenceMatcher
    # we will make it robust by averaging from many different durations in the file