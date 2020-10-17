import os
import gc

import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf

from helpers.ticktock import tick, tock

def readPydub():
    from pydub import AudioSegment
    segment = AudioSegment.from_wav("tmp.wav")
    # segment.set_channels(1)
    return segment.raw_data, segment.frame_rate
def readSoundfile(path, start, end):
    data = sf.read(path, start=start, end=end)
    # print(sf.info("tmp.wav", True))
    return data[0][:,0], 48000
def readStandard():
    import wave
    spf = wave.open("tmp.wav", "r")
    # Extract Raw Audio from Wav File
    signal = spf.readframes(-1)
    signal = np.fromstring(signal, "Int16")
    fs = spf.getframerate()
    # If Stereo
    if spf.getnchannels() == 2:
        # print("Just mono files")
        # sys.exit(0)
        pass
    return signal, fs


def sfread(fpath, start_ms, stop_ms, sample_rate=48000):
    startFrameIndex = np.round( (start_ms / 1000) * sample_rate )
    nframes = ( (stop_ms - start_ms) / 1000) * sample_rate # (stop_ms / 1000 * sampleRate) - startFrameIndex
    stopFrameIndex = np.round(startFrameIndex + nframes)
    # stopFrameIndex = ceil(startFrameIndex + nframes) #? should we use this instead
    try:
        return sf.read(fpath, start=int(startFrameIndex), stop=int(stopFrameIndex))
    except RuntimeError as error:
        print("Warning:", error, "startFrameIndex", startFrameIndex, "stopFrameIndex", stopFrameIndex)
        print(f"sfread({fpath=}, {start_ms=}, {stop_ms=})") #! python 3.8 only
        res = sf.read(fpath)[0][int(startFrameIndex):int(stopFrameIndex)], sample_rate
        print("succeeded reading the whole file and access the required data only")
        return res

def saveWaveform(inPath, start, end, outPath, audioInfo=None):
    '''
        start, end: in ms
    '''
    def wrap(audioInfo):
        audioInfo = audioInfo or sf.info(inPath)
        signal, fs = sfread(inPath, start, end, sample_rate=audioInfo.samplerate)
        signal = signal[:,0]
        Time = np.linspace(0, len(signal) / fs, num=len(signal))

        # configure plot (1)
        # fig = plt.figure(1, frameon=False)
        # fig.plot(Time, signal)

        # configure plot (2)
        plt.box(False)
        plt.margins(0,0)
        plt.gca().xaxis.set_major_locator(plt.NullLocator())
        plt.gca().yaxis.set_major_locator(plt.NullLocator())
        fig, ax = plt.subplots(1)
        fig.subplots_adjust(left=0,right=1,bottom=0,top=1, wspace=0, hspace=0)
        ax.axis('off')
        ax.margins(0,0)
        fig.tight_layout()
        plt.plot(Time, signal)

        # create dir if not exist
        outDir = os.path.dirname(outPath)
        if (outDir):
            os.makedirs(outDir, exist_ok=True)

        # save (1)
        plt.savefig(outPath, bbox_inches='tight', pad_inches=0)

        # save (2)
        # with open(outPath, 'w') as outfile:
        #     fig.canvas.print_png(outfile)
        plt.close('all')
        plt.clf()
        return audioInfo
    out = wrap(audioInfo)
    # input("see the mem")
    tick()
    gc.collect()
    tock()
    # input("see the mem")
    return out


def test():
    saveWaveform("audio_tests/ex1.wav", 55000.0, 358500.0, "zex1.png")
    input("see the mem")
    import gc
    gc.collect()
    input("see the mem")



def main():
    signal, fs = readStandard()
    print("Standard:", len(signal), signal[0])
    signal, fs = readPydub()
    print("Pydub:", len(signal), signal[0])
    signal, fs = readSoundfile()
    print("soundfile:", len(signal), signal[0])

    Time = np.linspace(0, len(signal) / fs, num=len(signal))
    input("wait")
    plt.figure(1)
    plt.title("Signal Wave...")
    plt.plot(Time, signal)
    plt.savefig("orange.png")

if __name__ == "__main__":
    test()