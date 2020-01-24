# from wavefile import read as sciread, write as sciwrite
import wave
import gc

def incload(chunkAvailableCond, path):
    print("incload start")
    waveread = wave.open(path, 'rb')
    n = 1000000 * 3 # approx 1 min
    for chunk in iter(lambda: waveread.readframes(n * 5), ''):
        with chunkAvailableCond:
            print("incload continue")
            wavewrite = wave.open("temp.wav", "wb")
            wavewrite.setparams(waveread.getparams())
            wavewrite.writeframes(chunk)
            del chunk
            gc.collect()
            wavewrite.close()
            chunkAvailableCond.notifyAll()
            print("incload notifyAll")
