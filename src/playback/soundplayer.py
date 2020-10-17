'''
 play a long file
'''
import queue
import threading
import sounddevice as sd
import soundfile as sf
import numpy as np

class SoundPlayer():
    '''
        class for playing single file at a time asynchronously without large memory allocation.
    '''
    player = None
    def __init__(self):
        super().__init__()
        self.blocksize = 2048
        self.buffersize = 20
        self.device = None
        self.state = 'idle' # states of playing: [idle, pausing, stopping, playing]
        self.q = None # current queue
        self.th = None # current consuming thread
        self.stream = None # current stream of played file
        self.info = None # current info of the played file

    @staticmethod
    def getInstance() -> "SoundPlayer":
        if (SoundPlayer.player == None):
            SoundPlayer.player = SoundPlayer()
        return SoundPlayer.player


    def start(self, filePath, from_s, to_s, play=True, onFinish=None):
        if(self.stream): self.stop()
        q = queue.Queue(maxsize=self.buffersize)
        self.q = q
        event = threading.Event()
        self.info = sf.info(filePath)
        samplerate = self.info.samplerate

        startFrame, stopFrame = from_s * samplerate, to_s * samplerate
        blocks = sf.blocks(filePath, start=startFrame, stop=stopFrame, blocksize=self.blocksize)

        for _ in range(self.buffersize):
            data = next(blocks, None)
            if not isinstance(data, np.ndarray):
                break
            q.put_nowait(data)  # Pre-fill queue

        def consumer(outdata, frames, time, status):
            # print("consumer")
            if self.state == 'pausing': outdata.fill(0)
            if (self.state == 'stopping'): raise sd.CallbackStop
            assert frames == self.blocksize
            if status.output_underflow:
                print('Output underflow: increase blocksize?')
                raise sd.CallbackAbort
            assert not status
            try:
                data = q.get_nowait()
            except queue.Empty as e:
                if(self.state == "pausing"):
                    print("I will block now.....")
                    data = q.get()
                    print("hello after block")
                else:
                    print('Buffer is empty: increase buffersize?')
                    raise sd.CallbackAbort from e
            if len(data) < len(outdata):
                outdata[:len(data)] = data
                outdata[len(data):] = b'\x00' * (len(outdata) - len(data))
                raise sd.CallbackStop
            else:
                outdata[:] = data
        def producer(status, timeout=None):
            count = 3
            while True: #data != None:
                state = self.state
                if(state == 'stopping'): break
                try:
                    data = next(blocks, None)
                    if (not isinstance(data, np.ndarray)): break
                    q.put(data, timeout=timeout)
                    count = 3
                except queue.Full:
                    # A timeout occurred, i.e. there was an error in the callback
                    if state == "pausing":
                        # block on the data
                        print("producer: block on putting data")
                        q.put(data)
                        count = 3
                    else:
                        print(f"timeout occurred, the callback doesn't consume the data correctly.. the queue is full {count}")
                        if (count == 0):
                            break
                        count -= 1
                        continue

        self.stream = sd.OutputStream(
            samplerate=samplerate, blocksize=self.blocksize,
            channels=self.info.channels, dtype='float32', callback=consumer, finished_callback=onFinish)
        self.th = threading.Thread(target=producer, args=(lambda: self.state, self.blocksize * self.buffersize / samplerate,) )
        self._setState("pausing")
        self.stream.start()
        self.th.start()
        if(play): self.play()

    def pause(self, ignoreError=False):
        if(not self.stream):
            if(ignoreError): return
            raise Exception("There is no sound started to pause it")
        self._setState("pausing")

    def play(self, ignoreError=False):
        if (not self.stream):
            if(ignoreError): return
            raise Exception("There is no sound started to play it")
        self._setState("playing")

    def stop(self, ignoreError=False):
        if (self.stream == None):
            if(ignoreError): return
            raise Exception("There is no sound started to stop it")
        self._setState("stopping")
        self.stream.close()
        self.th = None
        self.stream = None

    def wait(self):
        if(self.th and self.stream):
            self.th.join()

    def _setState(self, state):
        if(not state in ['idle', 'pausing', 'stopping', 'playing']): raise Exception("state should be one of [idle, pausing, stopping, playing]")
        self.state = state

if __name__ == "__main__":
    import time
    player = SoundPlayer.getInstance()
    player.start("audio_tests/ex1.wav", 0, 25)
    print("playing")
    time.sleep(5)
    player.pause()
    print("pausing")
    time.sleep(5)
    player.play()
    print("playing")
    time.sleep(8)
    print("stopping")
    player.stop()
    player.wait()

    input("force wait")