import speech_recognition as sr
from os import path

def recognize_speech_from_file(recognizer, path, start, duration, recognize):
    """Transcribe speech from recorded from `microphone`.

    Returns a dictionary with three keys:
    "success": a boolean indicating whether or not the API request was
               successful
    "error":   `None` if no error occured, otherwise a string containing
               an error message if the API could not be reached or
               speech was unrecognizable
    "transcription": `None` if speech could not be transcribed,
               otherwise a string containing the transcribed text
    """
    # check that recognizer and microphone arguments are appropriate type
    if not isinstance(recognizer, sr.Recognizer):
        raise TypeError("`recognizer` must be `Recognizer` instance")

    # adjust the recognizer sensitivity to ambient noise and record audio
    # from the microphone
    with sr.AudioFile(path) as source:
        print("before adjust, the energy=", recognizer.energy_threshold)
        recognizer.adjust_for_ambient_noise(source)
        duration = duration if duration > 0 else None
        audio = recognizer.record(source, offset=start, duration=duration)
        print("after adjust, the energy=", recognizer.energy_threshold)


    # set up the response object
    response = {
        "success": True,
        "error": None,
        "transcription": None
    }

    try:
        response["transcription"] = recognize(audio)
    except sr.RequestError:
        # API was unreachable or unresponsive
        response["success"] = False
        response["error"] = "API unavailable"
    except sr.UnknownValueError:
        # speech was unintelligible
        response["error"] = "Unable to recognize speech"

    return response


if __name__ == "__main__":
    # create recognizer and mic instances
    recognizer = sr.Recognizer()
    while True:
        path = input("what is path: ")
        start = int(input("what is the start you want to read from: "))
        duration = int(input("how long do you want to read from start: "))
        guess = recognize_speech_from_file(recognizer, path, start, duration, lambda audio:
            recognizer.recognize_google(audio, language="ar-EG")
            # recognizer.recognize_sphinx(audio)
        )
        if guess["error"]:
            print("ERROR: {}".format(guess["error"]))
            continue
        print("file say: {}".format(guess["transcription"]))


#* notes:

# إن لهجة بلاد الشام المتمثلة بسوريا والأردن وفلسطين الحديثة وليست القديمة قريبة جداً من اللغة الفصحى
# the speech_recognition have nice ability recognize_google(preferred_phrases), use it at the phase of corrections (we will know what is the ayat we are in, this will be the prefered phrases)

# for determining whether or not the file is quran or not, we may add features to know:
    # number of chars, words said in one minute (speed of speaker)
    # score of SentenceMatcher
    # we will make it robust by averaging from many different durations in the file



# + Afrikaans af

# + Arabic (Egypt) ar-EG
# + Arabic (Qatar) ar-QA
# + Arabic (UAE) ar-AE
# +? Arabic (Jordan) ar-JO
# + Arabic (Kuwait) ar-KW
# +? Arabic (Lebanon) ar-LB
# .+ Arabic (Morocco) ar-MA
# .+ Arabic (Iraq) ar-IQ
# .+ Arabic (Algeria) ar-DZ
# .+ Arabic (Bahrain) ar-BH
# .+ Arabic (Lybia) ar-LY
# .+ Arabic (Oman) ar-OM
# .+ Arabic (Saudi Arabia) ar-SA
# .+ Arabic (Tunisia) ar-TN
# .+ Arabic (Yemen) ar-YE
# https://cloud.google.com/speech-to-text/docs/languages