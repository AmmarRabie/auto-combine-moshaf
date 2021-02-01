from moshaf_builder import MoshafBuilder

from PyInquirer import style_from_dict, Token, prompt, print_json, Separator
from pprint import pprint
from pygments.token import Token
import os
from pathlib import Path
# TODO: import and use 'from pyconfigstore import ConfigStore'
# TODO: import and use 'from pyfiglet import figlet_format'

myStyle = style_from_dict({
    Token.QuestionMark: '#fac731 bold',
    Token.Answer: '#4688f1 bold',
    Token.Instruction: '',  # default
    Token.Separator: '#cc5454',
    Token.Selected: '#0abf5b',  # default
    Token.Pointer: '#673ab7 bold',
    Token.Question: '',
})
menu = [
    # firs menu
    {
        'type': 'list',
        'name': 'high_action',
        'message': 'What do you want to do ?',
        'choices': ['show', 'add', 'update', 'clear', 'compile', 'build', 'export', 'load', 'save', 'exit']
    },
    # second menu scenarios
    {
        # 
        'type': 'list',
        'name': 'show_action',
        'message': 'show what ?',
        "choices":[
                "files",
                "file segments",
            {
                "name": 'all segments',
                "value": "segments"
            }, 
            {
                "name": 'all chapters',
                "value": "chapters"
            }, 
            {
            "name": 'segment chapters',
            "value": "seg chapters"
            }, 
            {
            "name": 'a segment',
            "value": "segment"
            }, 
            {
            "name": 'a chapter',
            "value": "chapter"
            }, 
        ],
        "when": lambda answers: answers['high_action'] == 'show'
    },
    {
        # 
        'type': 'list',
        'name': 'add_action',
        'message': 'add what ?',
        'choices': ['file', 'folder'],
        "when": lambda answers: answers['high_action'] == 'add'
    },
    {
        # 
        'type': 'list',
        'name': 'update_action',
        'message': 'update what ?',
        'choices': ['file segments', 'segment chapter'],
        "when": lambda answers: answers['high_action'] == 'update'
    },
    {
        # 
        'type': 'list',
        'name': 'clear_action',
        'message': 'clear what ?',
        'choices': [
            {
                "name": 'project (all files)',
                "value": "all"
            }, 
            {
                "name": 'all segments',
                "value": "segments"
            }, 
            {
                "name": 'all chapters',
                "value": "chapters"
            }, 
            {
            "name": 'segment chapters',
            "value": "seg chapters"
            }, 
            {
            "name": 'a segment',
            "value": "segment"
            }, 
            {
            "name": 'a chapter',
            "value": "chapter"
            }, 
        ],
        "when": lambda answers: answers['high_action'] == 'clear'
    },
    {
        # 
        'type': 'list',
        'name': 'compile_action',
        'message': 'compile what ?',
        'choices': [{"name": 'segments & chapters', "value": "all"}, 'segments', 'chapters'],
        "when": lambda answers: answers['high_action'] == 'compile'
    },
    # third menu scenario
    {
        # 
        'type': 'input',
        'name': 'add_action_startPath',
        'message': 'start path',
        "default": "./",
        "validate": lambda input: True, # TODO: implement
        "when": lambda answers: answers['high_action'] == 'add'
    },
    {
        # 
        'type': 'confirm',
        'name': 'add_action_inDirInfo',
        'message': 'in directory information (segments and chapters)',
        "default": True,
        "when": lambda answers: answers['high_action'] == 'add'
    },
]

class Console:
    def __init__(self, projectPath = None):
        super().__init__()
        self.app = MoshafBuilder(projectPath)

    def getCommand(self):
        return prompt(menu, style=myStyle)

    def execCommand(self, command):
        highAction = command['high_action']
        if(highAction == 'exit'):
            if(self.app.isTempState()):
                # warn  the user
                ans = prompt([{
                    'type': 'confirm',
                    'name': 'noSave',
                    'message': 'exit without saving',
                    'default': False
                }])
            return not ans["noSave"]
        if(highAction == 'build'):
            self.app.build()
        elif(highAction == 'compile'):
            if(command['compile_action'] == 'all'):
                self.app.compile()
            elif(command['compile_action'] == 'segments'):
                self.app.compile(chapters=False)
            elif(command['compile_action'] == 'chapters'):
                self.app.compile(segments=False)
        elif(highAction == 'export'):
            path = self.chooseFolderNavigator()
            self.app.exportMoshaf(path.resolve())
        elif(highAction == 'clear'):
            if(command['clear_action'] == 'all'):
                self.app.clear()
            elif(command['clear_action'] == 'segments'):
                count = len(self.app.getFiles())
                for i in range(count): self.app.clearFileSegments(i)
            elif(command['clear_action'] == 'chapters'):
                for fileIndex, f in enumerate(self.app.getFiles()):
                    for segIndex in enumerate(f.segments):
                        self.app.clearSegmentChapters(fileIndex, segIndex)
            elif(command['clear_action'] == 'seg chapters'):
                self.app.compile(segments=False)
            elif(command['clear_action'] == 'segment'):
                self.app.compile(segments=False)
            elif(command['clear_action'] == 'chapter'):
                self.app.compile(segments=False)

        elif(highAction == 'show'):
            if(command['show_action'] == 'files'):
                paths = [f.path for f in self.app.getFiles()]
                pprint(paths)
            elif(command['show_action'] == 'segments'):
                pprint(self.app.getSegments())
            elif(command['show_action'] == 'chapters'):
                pprint(self.app.getChapters())
            elif(command['show_action'] == 'file segments'):
                fileIndex = self.askFile()
                pprint(self.app.getFiles()[fileIndex].segments)
            elif(command['show_action'] == 'seg chapters'):
                fileIndex, segIndex = self.askSegment()
                seg = self.app.getFiles()[fileIndex].segments[segIndex]
                pprint(seg.chapters)
            elif(command['show_action'] == 'segment'):
                fileIndex, segIndex = self.askSegment()
                seg = self.app.getFiles()[fileIndex].segments[segIndex]
                pprint(seg)
            elif(command['show_action'] == 'chapter'):
                fileIndex, segIndex, chapterIndex = self.askChapter()
                chapter = self.app.getFiles()[fileIndex].segments[segIndex].chapterLocations[chapterIndex]
                pprint(chapter)
    
        elif(highAction == 'add'):
            target = self.chooseFileNavigator if command['add_action'] == 'file' else self.chooseFolderNavigator
            ans = target(startPath=command['add_action_startPath'])
            target = self.app.addFolder if ans.is_dir() else self.app.addFile
            target(str(ans.resolve()), inDirInfo=command['add_action_inDirInfo'])

        elif(highAction == 'update'):
            pass
        
        elif(highAction == 'save'):
            savePath = None
            if(self.app.isTempState()):
                savePath = self.chooseFolderNavigator(dirMark=f"save a new file here")
                if(os.path.isdir(savePath)):
                    saveName = input("filename:")
                    savePath = os.path.join(savePath, saveName)
            self.app.save(savePath)
            print("saved")
        
        elif(highAction == 'load'):
            loadPath = self.chooseFileNavigator()
            self.app.load(loadPath)
        return True

    def askFile(self, message="choose the file"):
        files = self.app.getFiles()
        choices = map(lambda index, audioFile: {
            "name": repr(audioFile), # audioFile.path,
            "value": index
        }, range(len(files)), files)
        q = {
            "type": 'list',
            "name": 'file',
            "message": message,
            "choices": list(choices)
        }
        return prompt(q, style=myStyle)['file']
    
    def askSegment(self, fileIndex=None, message="choose the segment"):
        if(not fileIndex):
            fileIndex = self.askFile()
        segments = self.app.getFiles()[fileIndex].segments
        choices = map(lambda index, seg: {
            "name": repr(seg),
            "value": index
        }, range(len(segments)), segments)
        q = {
            "type": 'list',
            "name": 'segment',
            "message": message,
            "choices": list(choices)
        }
        return fileIndex, prompt(q, style=myStyle)['segment']

    def askChapter(self, fileIndex=None, segIndex=None, message="choose the chapter"):
        if(not segIndex):
            fileIndex, segIndex = self.askSegment()
        chapters = self.app.getFiles()[fileIndex].segments[segIndex].chapterLocations
        choices = map(lambda index, chapter: {
            "name": repr(chapter),
            "value": index
        }, range(len(chapters)), chapters)
        q = {
            "type": 'list',
            "name": 'chapter',
            "message": message,
            "choices": list(choices)
        }
        return fileIndex, segIndex, prompt(q, style=myStyle)['chapter']

    def chooseFileNavigator(self, startPath='./'):
        startPath = Path(startPath).resolve()
        current = self._showPath(startPath)
        while(current.is_dir()):
            current = self._showPath(current)
        return current

    def chooseFolderNavigator(self, startPath='./', dirMark="(select it to add the whole folder)"):
        startPath = Path(startPath).resolve()
        prevCurrent = startPath
        current = self._showPath(startPath, showCurrentDir=True, currentDirMark=dirMark)
        if(isinstance(current, str) and current == "."):
            return prevCurrent
        while(current.is_dir() and current != "."):
            prevCurrent = current
            current = self._showPath(current, showCurrentDir=True, currentDirMark=dirMark)
            if(isinstance(current, str) and current == "."):
                current = prevCurrent
                break
        return current

    def _showPath(self, root, showCurrentDir=False, dirMark=" >", fileMark="", currentDirMark=""):
        rootPath = Path(root)
        dirs = []
        files = []
        for path in rootPath.iterdir():
            if(path.is_dir()): dirs.append(path)
            else: files.append(path)
        choiceMapper = lambda post: lambda x: {"name": x.name + post, "value": x}
        choices = [{"name": ". " + currentDirMark, "value": "."},] if showCurrentDir else []
        choices += [{"name": "..", "value": rootPath.parent},] + \
            list(map(choiceMapper(dirMark), dirs)) + list(map(choiceMapper(fileMark), files))
        q = {
            "type": "list",
            "message": "navigate",
            "name": "ans",
            "choices": choices
        }
        return prompt(q, style=myStyle)['ans']
    
    def loop(self):
        stop = False
        while(not stop):
            cmd = self.getCommand()
            stop = not self.execCommand(cmd)



if __name__ == "__main__":
    from sys import argv
    projectPath = argv[1] if(len(argv) >= 2) else None
    app = Console(projectPath)
    app.loop()
    # chosen = app.chooseFolderNavigator()
    # print(chosen)
