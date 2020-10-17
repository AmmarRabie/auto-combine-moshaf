'''
base editor functionalities with no gui, you can extend to use with different inputs methods (see TkinterEditor for gui inputs from the user)
'''
import os
import json
from random import randint

from pydub import AudioSegment

from onset_detection.splitter import SalahSplitter
from helpers.utils import circularIncIndex, circularDecIndex

class Editor():
    '''
        Base editor, can be used in any modules as functions, @see TkinterEditor for gui editing
    '''
    def __init__(self, projectFile=None, labelDefaults={}, outDir_root='C:\\Data\\splitter_out', algConfigPath='algo.ini'):
        self.outDir_root = outDir_root
        self.selectedLabelIndex = None
        self.selectedFileIndex = None
        self.projectFilePath = None
        self.tempProj = False
        
        self.extSupported = ["wav", "ogg", "mp3", "rm", "flac", "aac", "m4a"]
        self.files = [] # item is key value pairs contains labels key, eg: files = [ {path: *path*, labels:[{title:*title*, start: *start*}] }, [{},{}] ]

        self.labelDefaults = labelDefaults # at creating new label, this values will be populated first over the new label
        self.splitter = SalahSplitter()

        # file exist, load the project
        if projectFile != None and os.path.exists(projectFile): self.loadProject(projectFile)
        # file doesn't exist, create new project with this name
        # TODO: create the base dir of the path before creating the file so that no error raised
        elif projectFile != None: self.projectFilePath = projectFile
        # if no file provided create new temp project
        else: 
            self.projectFilePath = "tmp.qm"
            self.tempProj = True


    def setExportDir(self, path):
        self.outDir_root = path

    def setProject(self, projectFile):
        # TODO: write its implementation
        raise NotImplementedError
    
    def addFiles(self, files):
        currentLen = len(self.files)
        for f in files:
            if isinstance(f, dict):
                path = f['path'] # TODO: raise readable error here if path doesn't exist
                f = {"display": os.path.basename(path), "labels": [], **f}
                self.files.append(f)
            else:
                self.files.append({
                    "display": os.path.basename(f),
                    "path": f,
                    "suggested": False,
                    #"labels": [ {"display": str(x) + str(randint(0, 1000))} for x in range(randint(1, 10)) ],
                    "labels": [],
                })
        return self.files[currentLen:] # return added ones
        
    def changeLabel(self, fileIndex, labelIndex, label):
        original = self.files[fileIndex]["labels"][labelIndex]
        original = {**original, **label}
        return original

    def suggestCuts(self, grouping="all", countFrom=1):
        for fileIndex, currentFile in enumerate(self.files):
            print(f"processing {currentFile['display']} start...")
            if(self.files[fileIndex].get("suggested", False)):
                print("ignore, processed before")
                continue
            filePath = currentFile['path']
            audio = AudioSegment.from_file(filePath)
            audio = self.splitter.prepareAudio(audio)
            outGenerator = self.splitter.split(audio, countFrom=countFrom, grouping=grouping)
            for label in outGenerator:
                print(f"\tfound {label['snum']}: {label['scp']} ==> {label['ecp']}")
                del label['audio']
                self.files[fileIndex]['labels'].append({**self.labelDefaults, "display": label['snum'], **label})
            self.files[fileIndex]['suggested'] = True #* this should be false again if scp, ecp edited manually

    def selectFile(self, index):
        filesCount = len(self.files)
        if (filesCount == 0): return
        if (not (abs(index) < filesCount or (index < 0 and abs(index) <= filesCount))):
            return self.selectFile(self, filesCount - 1)
        self.selectedFileIndex = index

    def selectNext(self):
        fcount = len(self.files)
        if (self.selectedFileIndex == None): return self.selectFile(0)
        lcount = len(self.files[self.selectedFileIndex]['labels'])
        # if 'no labels' or 'no selected label' or 'last label selected' go to next file
        if (lcount == 0
            or self.selectedLabelIndex == None
            or self.selectedLabelIndex == lcount - 1):
            return self.selectFile(circularIncIndex(fcount, self.selectedFileIndex))
        # else go to next label
        return self.selectLabel(self.selectedLabelIndex + 1)

    def selectPrevious(self):
        fcount = len(self.files)
        if (self.selectedFileIndex == None): return self.selectFile(0)
        lcount = len(self.files[self.selectedFileIndex]['labels'])
        # if 'no labels' or 'no selected label' or 'first label selected' go to prev file
        if (lcount == 0
            or self.selectedLabelIndex == None
            or self.selectedLabelIndex == 0):
            return self.selectFile(circularDecIndex(fcount, self.selectedFileIndex))
        # else go to prev label
        return self.selectLabel(self.selectedLabelIndex - 1)
    def selectLabel(self, index):
        self.selectedLabelIndex = index
    

    def setProjectFile(self, path):
        self.projectFilePath = path

    def saveProject(self, path=None):
        path = path or self.projectFilePath
        jsonStr = json.dumps({"files": self.files}, default=dumper)
        with open(path, 'w') as projectFile:
            projectFile.write(jsonStr)
        print("project saved")
        self.setProjectFile(path)
        self.tempProj = False
        return True

    def loadProject(self, path=None):
        path = self.projectFilePath or path
        if (not path):
            return False
        with open(path, 'r') as projectFile:
            project = json.loads(projectFile.read())
            self.files = project['files']
            self.tempProj = False
            self.setProjectFile = path
            return True

    def toggleFileComplete(self, index=None, default=True):
        '''
        :param index: target index, if none will use selectedFileIndex
        :param default: if no complete state in the file, will use this value. default is true meaning that in the first time you toggle will set to true

        returns index of the file that changed, new value applied
        '''
        targetIndex = index or self.selectedFileIndex
        toggledValue = not self.files[targetIndex].get("complete", not default)
        self.files[targetIndex]['complete'] = toggledValue
        return targetIndex, toggledValue

    def toggleLabelComplete(self, fileIndex = None, index=None, default=True):
        '''
        :param fileIndex: target file index, if none will use the selectedFileIndex
        :param index: target index, if none will use selectedLabelIndex
        :param default: if no complete state in the label, will use this value. default is true meaning that in the first time you toggle will set to true
        returns index of the file that changed, new value applied
        '''
        targetIndex = index or self.selectedLabelIndex
        fileIndex = fileIndex or self.selectedFileIndex
        toggledValue = not self.files[fileIndex]['labels'][targetIndex].get("complete", not default)
        self.files[fileIndex]['labels'][targetIndex]['complete'] = toggledValue
        return targetIndex, toggledValue

    @property
    def selectedFile(self): return self.files[self.selectedFileIndex] if self.selectedFileIndex != None else None

    @property    
    def selectedLabel(self): return self.selectedFile['labels'][self.selectedLabelIndex] if self.selectedLabelIndex != None and self.selectedFileIndex != None else None

# helpers
def dumper(obj):
    if hasattr(obj, "__serialize__"):
        return obj.__serialize__()
    return obj.__dict__

if __name__ == "__main__":
    editor = Editor()
    editor.loadProject("tmp.qm")
    editor.suggestCuts()
    editor.saveProject("editor.base.test.qm")

