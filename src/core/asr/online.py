import speech_recognition as sr
from os import path

from .interface import ASRInterface

class OnlineASR(ASRInterface):
    '''
    Online ASR implementation using google ASR version
    '''
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.lang = "ar-EG"
        self.server = "google" #? May add other servers
    def recognizeGoogle(self, filePath, start, duration=None):
        with sr.AudioFile(filePath) as source:
            audio = self.recognizer.record(source, offset=start, duration=duration)  # read the entire audio file
        try:
            return self.recognizer.recognize_google(audio, language=self.lang)
        except sr.UnknownValueError:
            return None

    def recognize(self, audioPath, start, duration):
        return self.recognizeGoogle(audioPath, start, duration)


#* إن لهجة بلاد الشام المتمثلة بسوريا والأردن وفلسطين الحديثة وليست القديمة قريبة جداً من اللغة الفصحى
#* the speech_recognition have nice ability recognize_google(preferred_phrases), use it at the phase of corrections (we will know what is the ayat we are in, this will be the prefered phrases)




# for determining whether or not the file is quran or not, we may add features to know:
    # number of chars, words said in one minute (speed of speaker)
    # score of SentenceMatcher
    # we will make it robust by averaging from many different durations in the file