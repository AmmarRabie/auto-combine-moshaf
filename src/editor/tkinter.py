'''
editor is the main application gui, you can also use it as a module without running the gui
works with the extension type of .qm ==> quran maker
process steps:
* choose folders and files for running splitter module on
* you have the ability then to refuse some labels, edit the boundaries, add new label
  simple editting can be done directly from the main gui
  advanced editing can be dome from audacity application, communication is done automatically
* run export over the project file than contains all the information about cuts positions and labels, name
'''
import os
import json
import subprocess
from time import sleep
from uuid import uuid4
from functools import reduce
from math import ceil

import tkinter as tk
from tkinter import filedialog, Button, Canvas, LabelFrame
from PIL import ImageTk, Image
from pydub import AudioSegment

from .base import Editor
from audacity.aud_scripter import AudacityScripter
from renderer.generate_wave_form import saveWaveform
from playback.soundplayer import SoundPlayer


# helper classes for TkinterEditor
class WaveformImage(Canvas):
    def __init__(self, master, imagePath, duration, cnf={}, **kw):
        '''
            duration: in seconds
        '''
        super().__init__(master=master, cnf=cnf, **kw)
        self._startPosition = None
        self._endPosition = None
        self._startId = None
        self._endId = None

        # persist init values
        self._duration = duration # in seconds
        self._imagePath = imagePath
        self._master = master

        # config
        self.lineWidth = 3
        self.fillColor = "green"

        img = Image.open(imagePath).resize((int(610*0.8), int(450*0.6)), Image.ANTIALIAS)
        img = ImageTk.PhotoImage(img)
        self.create_image(0, 0, anchor=tk.NW, image=img)
        self._wfi_h, self._wfi_w = img.height(), img.width() #* don't use self._h because it is reserved in pack and grid methods for window name
        self._pixelsPerSecond = self._wfi_w / self._duration # unit: pixels / second
        print(self._pixelsPerSecond)
        self.image = img


    def changeStartPosition(self, pos):
        if self._startId != None:
            self.delete(self._startId)
        self._startId = self._createNewPos(pos)
        self._startPosition = pos

    def changeEndPosition(self, pos):
        if self._endId != None:
            self.delete(self._endId)
        self._endId = self._createNewPos(pos)
        self._endPosition = pos
    
    def _createNewPos(self, pos):
        targetPixelStart = self.secondsToPixel(pos)
        posId = self.create_rectangle(targetPixelStart, 0, targetPixelStart + self.lineWidth, self._wfi_h, fill=self.fillColor)
        return posId

    def secondsToPixel(self, pos):
        return pos * self._pixelsPerSecond # seconds * (pixels / second) = pixels

    @property
    def startPosition(self):
        return self._startPosition
    @property
    def endPosition(self):
        return self._endPosition

    @classmethod
    def fromJson(cls, master, json):
        '''
            json: json produced from serialization as dict object
        '''
        wfi = cls(master, json['path'], json['duration'])
        scp, ecp = json.get("scp"), json.get('ecp')
        if (scp != None):
            wfi.changeStartPosition(scp)
        if(ecp != None):
            wfi.changeEndPosition(ecp)
        return wfi


    def __serialize__(self):
        return {
            "path": self._imagePath,
            "scp": self.startPosition,
            "ecp": self.endPosition,
            "duration": self._duration
        }

class TkinterEditor(Editor):
    def __init__(self, projectFile=None, outDir_root='C:\\Data\\splitter_out', algConfigPath='algo.ini'):
        super().__init__(projectFile=projectFile, labelDefaults={
            "wfi": None,
            "edited_scp": None,
            "edited_ecp": None,
        }, outDir_root=outDir_root, algConfigPath=algConfigPath)
        self.editLabelMargin = 5000 # in ms
        self.player = SoundPlayer.getInstance()
        self.playing = False

    def addFiles(self):
        newFiles = filedialog.askopenfilenames()
        if len(newFiles) == 0: return
        newFiles = super().addFiles(newFiles)
        newFiles = list(map(lambda f: f["display"], newFiles))
        self.updateLboxFiles(newFiles)

    def addDirectory(self): #? openDirectory better name ?
        directory = filedialog.askdirectory()
        print(directory)
        files = [os.path.join(root, filename) for root, subdirs, files in os.walk(directory) if len(subdirs) == 0 for filename in files if (filename.split(".")[-1] in self.extSupported)]
        print(files)
        newFiles = super().addFiles(files)
        newFiles = list(map(lambda f: f["display"], newFiles))
        self.updateLboxFiles(newFiles)

    def changeLabel(self, fileIndex, labelIndex, label):
        label = super().changeLabel(fileIndex, labelIndex, label)
        if self.lbox_files.curselection()[0] == fileIndex:
            self.lbox_labels.delete(labelIndex)
            self.lbox_labels.insert(labelIndex, label["display"])
            if self.lbox_labels.curselection()[0] == labelIndex:
                # change the done state and so on of displayed states in the main frame
                pass
    def updateLboxFiles(self, files):
        '''
            append names in the files list box, append in the gui only
        '''
        fillListBox(self.lbox_files, files, start=len(self.files) - len(files))

    def selectFile(self, index):
        # if self.selectedFileIndex != None: self.lbox_files.itemconfig(self.selectedFileIndex, bg="white")
        super().selectFile(index)
        self.lbox_files.select_clear(0, tk.END)
        self.lbox_files.select_set(self.selectedFileIndex)
        self.lbox_files.activate(self.selectedFileIndex)
        # self.lbox_files.itemconfig(self.selectedFileIndex, bg="blue")
        self._refreshLabelsLBox()
        self.selectLabel(0)
        self.player.stop(ignoreError=True)

    def selectLabel(self, index):
        super().selectLabel(index)
        self.lbox_labels.select_clear(0, tk.END)
        self.lbox_labels.select_set(self.selectedLabelIndex)
        self.lbox_labels.activate(self.selectedLabelIndex)
        currentLabel = self.selectedLabel
        if (not self.selectedFile.get('suggested', False)): return
        if (currentLabel.get('wfi') == None):
            print(currentLabel)
            scp, ecp = currentLabel['scp'], currentLabel['ecp'] # in ms
            figName = currentLabel.get('figname')
            if (not figName):
                figName = uuid4().hex
                info = saveWaveform(self.selectedFile['path'], int(max(scp - self.editLabelMargin, 0)), int(ecp + self.editLabelMargin), f"data/{figName}.png")
            currentLabel['figName'] = figName

            duration = ecp + self.editLabelMargin - max(scp - self.editLabelMargin, 0) # ms
            duration /= 1000
            margin = self.editLabelMargin / 1000
            wfi = WaveformImage(master=self.frm_main, imagePath=f"data/{figName}.png", duration=duration)
            wfi.changeStartPosition(margin)
            wfi.changeEndPosition(duration - margin)
            currentLabel['wfi'] = wfi
        self._setMainFromWFI(currentLabel['wfi'])
        self.player.stop(ignoreError=True)

    def saveProject(self, path=None):
        if(self.tempProj):
            path = path or filedialog.asksaveasfilename()
        if(not path): return False
        return super().saveProject(path=path)

    def saveProjectAs(self):
        path = filedialog.asksaveasfilename()
        if(not path): return False
        isSaved = super().saveProject(path=path)
        
    def loadProject(self, path=None):
        path = path or filedialog.askopenfilename(title = "choose qm project", filetypes = (("qm files","*.qm"),))
        opened = super().loadProject(path=path)
        if (opened):
            self._updateFilesWFIs()
            self._refreshFilesLBox()
        return opened

    def togglePlay(self):
        if(self.playing): self.player.stop(); self._setPlay(False); return
        label = self.selectedLabel
        if (not label): print("no labels selected to toggle play"); return
        scp, ecp = label['scp'], label['ecp']
        path = self.selectedFile['path']
        self.player.start(path, int(scp / 1000), int(ecp / 1000), onFinish = lambda: self._setPlay(False))
        self._setPlay(True)

        

    def audacity(self, fileIndex = None):
        '''
            fileIndex: index in self.files to open or None for current selected file
        '''
        #TODO: enable such feature like below, track opened files so that if opened redirect to it
        # self.audacityOpenedFiles.append()
        fileIndex = fileIndex or self.selectedFileIndex
        # self._validateFileIndex(fileIndex) # TODO: implement
        targetFile = self.files[fileIndex]
        audacityPath = self._getAudacityLocation()
        openAudacity = subprocess.Popen([audacityPath])
        sleep(5)
        # openAudacity.wait()
        print("init scripter")
        self.scripter = AudacityScripter()
        self.scripter.openFile(targetFile['path'], labels=map(lambda l: {"title": str(l['snum']), "start": l['scp'] / 1000, "end": l['ecp'] / 1000}, targetFile['labels']))

    def toggleFileComplete(self, index=None, default=True):
        index, completed = super().toggleFileComplete(index, default)
        self.lbox_files.itemconfig(index, fg="green" if completed else "white", selectforeground="#ff0000" if completed else "white")

    def toggleLabelComplete(self, fileIndex = None, index=None, default=True):
        index, completed = super().toggleLabelComplete(fileIndex, index, default)
        print("indx, completed", index, completed)
        self.lbox_labels.itemconfig(index, fg="green" if completed else "white", selectforeground="#ff0000" if completed else "white")

    def gui(self):
        self.window = tk.Tk()
        # TODO: put window configuration in helper function
        self.window.geometry("1000x500")
        self.window.title("Quran Salah Editor")

        self.MULTIPLIER = 3

        self._quickActions()
        self._main()
        self._navigation()
        
        self._bindKeyShortcuts()

    def _setMainFromWFI(self, wfi):
        for c in self.frm_main.winfo_children(): c.grid_forget()
        wfi.grid(row=0, column=0, sticky="nsew")
    
    def _updateFilesWFIs(self):
        for f in self.files:
            labels = f.get('labels')
            if not labels: continue
            for l in labels:
                wfiJson = l.get('wfi')
                if not wfiJson: continue
                l['wfi'] = WaveformImage.fromJson(self.frm_main, wfiJson)

    def _bindKeyShortcuts(self):
        def _key_(event):
            char = event.char
            ctrl = (event.state & 0x4) != 0
            shift = (event.state & 0x1) != 0
            # print("pressed:", event.char, type(event.keysym), event, f"{ctrl=}, {shift=}")

            if(shift and not ctrl):
                # shift only is pressed
                char = event.keysym.lower()
                if (char == 'c'):
                    if(self.selectedFileIndex == None or self.selectedFileIndex == None): print("no file or label"); return
                    self.toggleLabelComplete()
                return

            if(ctrl and not shift):
                # ctrl only is pressed
                char = event.keysym.lower()
                if (char == 's'): # ctrl + s ==> save project
                    self.saveProject()
                if (char == 'l'): # ctrl + l ==> load project
                    self.loadProject()
                if (char == 'o'): # ctrl + o ==> open dir
                    print("add dir")
                    self.addDirectory()
                if (char == 'f'): # ctrl + f ==> add files
                    print("add files")
                    self.addFiles()
                if (char == 'c'): # ctrl + c ==> run splitter and get [c]uts
                    print("run splitter")
                    self.suggestCuts()
                    self.selectFile(0)
                    self.selectLabel(0)
                    # self._refreshLabelsLBox()
                if (char == 'd'): # ctrl + d ==> edit on audacity
                    self.audacity()

            if (shift and ctrl):
                pass
            
            if (char == ''): return
            char = char.lower()
            if (char == 'd'): # next file or label
                self.selectNext()
            if (char == 'a'): # previous file or label
                self.selectPrevious()
            if (char == 'c'):
                if(self.selectedFileIndex == None): return
                self.toggleFileComplete()
            if (char == 'p'):
                self.togglePlay()

            if (not ctrl): return
            char = event.keysym.lower()
            if(shift): # shift and ctrl shortcuts
                if (char == 'c'): # run splitter and get [c]uts over selected file
                    return
            
        self.window.bind("<Key>", _key_)

    def _getAudacityLocation(self):
        # TODO: implement search for installed paths instead of hardcode
        return "C:\\Program Files (x86)\\Audacity\\audacity.exe"

    def _quickActions(self):
        frm_quickActions = tk.Frame(master=self.window, width=50*self.MULTIPLIER, height=200, bg="red")
        frm_quickActions.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

    def _main(self):
        frm_main = tk.Frame(master=self.window, width=250*self.MULTIPLIER, bg="yellow")
        frm_main.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

        frm_main.rowconfigure(0, weight=1)
        frm_main.columnconfigure(0, weight=1)
        self.frm_main = frm_main

    def _navigation(self):
        frm_navigation = tk.Frame(master=self.window, width=250*self.MULTIPLIER, bg="blue")
        frm_navigation.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)
        frm_navigation.rowconfigure([0,1], weight=1)
        frm_navigation.columnconfigure(0, weight=1)
        lbox_files = staticListbox(frm_navigation, [])
        lbox_files.bind('<<ListboxSelect>>', self._onFileSelectionChange)
        lbox_files.grid(column=0, row=0, sticky="nsew")

        frm_navigation.rowconfigure([0,1], weight=1)
        frm_navigation.columnconfigure(0, weight=1)
        lbox_labels = staticListbox(frm_navigation, [])
        lbox_labels.bind('<<ListboxSelect>>', self._onLabelSelectionChange)
        lbox_labels.grid(column=0, row=1, sticky="nsew")

        self.frm_navigation, self.lbox_files, self.lbox_labels = frm_navigation, lbox_files, lbox_labels

    def _onFileSelectionChange(self, evt):
        index = int(evt.widget.curselection()[0])
        self.selectFile(index)

    def _onLabelSelectionChange(self, evt):
        index = int(evt.widget.curselection()[0])
        self.selectLabel(index)

    def _refreshFilesLBox(self):
        self.lbox_files.delete(0, tk.END)
        fillListBox(self.lbox_files, self._mapDisplay(self.files))
        self.selectFile(0)        
    def _refreshLabelsLBox(self):
        self.lbox_labels.delete(0, tk.END)
        fillListBox(self.lbox_labels, self._mapDisplay(self.files[self.selectedFileIndex]['labels']))
        self.selectLabel(0)

    def _mapDisplay(self, array):
        return [x['display'] for x in array]

    def _refreshFilesLBox(self):
        self.lbox_files.delete(0, tk.END)
        fillListBox(self.lbox_files, self._mapDisplay(self.files))
        self.selectFile(0)

    def _refreshLabelsLBox(self):
        self.lbox_labels.delete(0, tk.END)
        fillListBox(self.lbox_labels, self._mapDisplay(self.files[self.selectedFileIndex]['labels']))
        self.selectLabel(0)

    def _setPlay(self, state):
        self.playing = state

    def mainloop(self):
        if(not hasattr(self, 'window')): self.gui()
        self.window.mainloop()


# helperes
def staticListbox(master, values, selectmode=tk.SINGLE, exportselection=False):
    listbox = tk.Listbox(master=master, selectmode=selectmode, exportselection=exportselection)
    for i, v in enumerate(values):
        listbox.insert(i, v)
    return listbox
def fillListBox(listbox, values, start=0):
    for i, v in enumerate(values):
        listbox.insert(start + i, v)
    return listbox

def drawFreqBars(data, canvas, styles={}):
    print(data[:5])
    length = len(data)
    defaults = {
        "fillStyle": 'rgb(250, 250, 250)',
        "strokeStyle": 'rgb(251, 89, 17)',
        "lineWidth": 1,
        "fftSize": 16384, # delization of bars from 1024 to 32768
        "spaceBetweenBars": 1,
        "heightPadding": 0,
        "barWidth": 2,

    }
    styles = { **defaults, **styles }

    canvas.update()
    width, height = canvas.winfo_reqwidth(), canvas.winfo_reqheight()

    canvas.create_rectangle(0, 0, width, height)
    oneBarResoultion = 0.20 # 50 % of the width
    barWidth = styles["barWidth"] or width * (oneBarResoultion / 100) # TODO: fix issue of space between bars greater than 1
    barHeight = None

    # array_chunks = (array, chunk_size) => Array(Math.ceil(array.length / chunk_size)).fill().map((_, index) => index * chunk_size).map(begin => array.slice(begin, begin + chunk_size))
    # average = (array) => array.reduce((a, b) => a + Math.abs(b)) / array.length
    array_chunks = lambda array, chunk_size: map(lambda begin: array[int(begin):int(begin + chunk_size)],[index * chunk_size for index in range(ceil(len(array) / chunk_size))])
    average = lambda array: reduce(lambda a, b: a + abs(b), array) / len(array)
    data = map(average, array_chunks(data, width / (barWidth + styles["spaceBetweenBars"])) )
    data = list(data)
    # minValue = Math.min(data)
    print(len(data))
    maxValueRef = styles.get("maxValue", None) or max(data)
    xOffset = 0
    for i in range(len(data)):
        barHeight = (data[i] / maxValueRef) * (height - styles["heightPadding"])
        # barHeight *= 800
        # print(f"{barHeight=}")

        canvas.create_rectangle(xOffset, int(height - barHeight), xOffset + barWidth, int(height), fill="green")
        xOffset += barWidth + styles["spaceBetweenBars"]
    print(barWidth, barHeight, maxValueRef, len(data))


if __name__ == "__main__":
    editor = TkinterEditor()
    editor.gui() # build the gui
    # editor.addFiles()
    editor.mainloop()

