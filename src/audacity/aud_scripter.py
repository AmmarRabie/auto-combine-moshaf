import time
from . import pipeclient
from helpers.errors import AudacityNotOpened

class Label:
    instances = 0
    def __init__(self, title, start, end):
        self.id = 0
        self.title = title
        self.start = start
        self.end = end
        Label.instances += 1
    
    def getParamsStr(self):
        return f"Label={self.id} Start={self.start} End={self.end} Text=\"{self.title}\""


class AudacityScripter:
    def __init__(self):
        try:
            self.client = pipeclient.PipeClient()
        except FileNotFoundError as error:
            raise AudacityNotOpened
        self.TIMEOUT = 10
    
    def openFile(self, audioPath, labels):
        '''
            to get the intended result, it is better to call close() first. 
        '''
        self.client.write(f"OpenProject2: Filename=\"{audioPath}\"")
        self._createLabels(labels)
    
    def openProject(self, projectPath):
        raise NotImplementedError
        pass
    
    def close(self, name = None, save=True):
        if save and name==None: raise Exception("if save, you have to pass name parameter")
        if save: self.save(name)
        self.client.write("Close"); self._wait()

    def save(self, name):
        self.client.write(f"SaveProject2: Filename=\"{name}\""); self._wait()

    def _createLabels(self, labels):
        print("create lables")
        res = []
        for label in labels:
            res.append(self._createLabel(label["title"], label["start"], label["end"]))
        return res
    def _createLabel(self, title, start, end):
        self.client.write("AddLabel")
        reply = self._wait()
        if not reply:
            raise Exception("time out in the reply of adding label")
        label = Label(title, start, end)
        self.client.write(f"SetLabel: {label.getParamsStr()}")
        return label

    def _wait(self):
        start = time.time()
        reply = ''
        while reply == '':
            time.sleep(0.1)  # allow time for reply
            if time.time() - start > self.TIMEOUT:
                reply = False
            else:
                reply = self.client.read()
        return reply

if __name__ == "__main__":
    scripter = AudacityScripter()
    labels = [
        {"title": "ammar alsayed", "start": 0, "end": 10},
        {"title": "ammar2alsayed", "start": 11, "end": 20},
    ]
    scripter.openFile("C:\\Data\\workspace\\qur2an salah splitter\\tmp.wav", labels)

    input("enter any key")
    scripter.close("C:\\Data\\workspace\\qur2an salah splitter\\ammmmmmmar")
