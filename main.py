from configparser import ConfigParser
from splitter.splitter import SalahSplitter
from pydub import AudioSegment
import os
from ticktock import tick, tock, logTime as currentTime
from json import dumps as jdumps, loads as jloads
# from incrementalload import SmartWavLoader

class SplitterMain(object):
    def __init__(self, outDir_root="C:\Data\splitter_out", algConfigPath="algo.ini", runsPath="input.txt"):
        '''
            outDir (string): root dir of output
        '''
        print("initializing SplitterMain")
        self.outDir_root = outDir_root
        self.algConfigPath = algConfigPath
        self.algOptions = self._loadSplitOptions(self.algConfigPath)
        self.checkpointRate = 3 # every 3 files we will make a checkpoint file
        self.checkpointDir = "checkpoints/"
        self.splitter = SalahSplitter(**self.algOptions)

        self.grouping = None
        self.countFrom = None
        self.outFormat = None

    def recover(self, checkpointFile):
        withdirJoined = os.path.join(self.checkpointDir, checkpointFile)
        if(os.path.exists(checkpointFile) and os.path.isfile(checkpointFile)):
            pass
        elif(os.path.exists(checkpointFile + ".json") and os.path.isfile(checkpointFile + ".json")):
            checkpointFile = checkpointFile + ".json"
        elif(os.path.exists(withdirJoined) and os.path.isfile(withdirJoined)):
            checkpointFile = withdirJoined
        else:
            raise FileNotFoundError(f"checkpoint file {checkpointFile} can't be found")
        runs, lastProcessedIndex = self._initFromCheckpointFile(checkpointFile)
        if (lastProcessedIndex >= len(runs) - 1):
            print("checkpoint file is fully executed before")
            return
        runs = runs[lastProcessedIndex + 1:]
        self.executeRuns(runs)

    def processRuns(self, runsPath="input.txt", extignorePath=".extignore", grouping="all", countFrom=1, checkpoint=True, outFormat="{ifname}_{gnum} {snum}.{expoext}"):
        '''
            outFormat can contains any combination of the following in addition to dirs format:
            - {ifname} ==> replaced with input file name with no extension
            - {ifdabsp} ==> replaced with input file directory absolute path (with not drive letter) # TODO not supported
            - {ifext} ==> replaced with input file extension # TODO not supported
            - {expoext} ==> replaced with export extension
            - {snum} ==> replaced with split number that the current file range corresponding to in its group
            - {gnum} ==> replaced with group number that the current file range corresponding to
            - {olength} ==> replaced with output file duration # TODO not supported
            - {ilength} ==> replaced with original input file duration # TODO not supported
            - {scp} ==> replaced with start cut position in seconds # TODO not supported
            - {ecp} ==> replaced with end cut position in seconds # TODO not supported
        '''
        self.grouping = grouping
        self.countFrom = countFrom
        self.outFormat = outFormat
        runs = self._readRuns(runsPath, extignorePath) # inflated runs
        self.executeRuns(runs)
    def executeRuns(self, runs):
        for runIndex, (filePath, exportFormat) in enumerate(runs):
            print(filePath, exportFormat)
            # audio = SmartWavLoader(filePath)
            audio = AudioSegment.from_file(filePath)
            audio = self.splitter.prepareAudio(audio)
            outGenerator = self.splitter.split(audio, countFrom=self.countFrom, grouping=self.grouping)
            list(map(lambda info: self.export(filePath, exportFormat, info), outGenerator))
            if(runIndex % self.checkpointRate == 0): self._checkpoint(runs, runIndex)

    def _readRuns(self, path, extignorePath):
        extIgnore = []
        with open(extignorePath, "r") as extIgnoreFile:
            extIgnore.extend([ext for ext in extIgnoreFile.read().split("\n")])
        runs = []
        with open(path, encoding="utf-8") as f:
            origInput = f.read().splitlines(False)
            # origInput = [r.split(" ") for r in runs]
            # print(origInput)
            for run in origInput:
                ipath, fformat = run.split(" ") # TODO: error when path itself have spaces
                if(os.path.isfile(ipath)):
                    ext = ipath.split(".")[-1]
                    if ext in extIgnore:
                        continue
                    runs.append([ipath, fformat])
                else:
                    runs.extend([[os.path.join(root, filename), fformat] for root, subdirs, files in os.walk(ipath) if len(subdirs) == 0 for filename in files if not (filename.split(".")[-1] in extIgnore)])
        return runs


    def export(self, ifpath, exportExt, info):
        '''
            write the file in the correct name
        '''
        audio = info["audio"]
        # del info["audio"]
        ifnamext = os.path.basename(ifpath)
        replacerMapper = {
            "ifnamext": ifnamext,
            "ifname":ifnamext[:ifnamext.rfind(".")],
            "ifext": ifnamext[ifnamext.rfind("."):],
            "expoext": exportExt,
            "ifdabsp": os.path.splitdrive(ifpath)[1],
            **info
        }
        outPath = self.outFormat
        for k, v in replacerMapper.items(): outPath = outPath.replace('{' + k + "}", str(v))
        print(f"exporting to {outPath}")
        audio.export(outPath, format=exportExt)
    def _loadSplitOptions(self, path):
        configParser = ConfigParser(allow_no_value=True)
        configParser.read(path)
        options = {}
        sections = ['initial', 'adjust']
        for section in sections:
            for key in configParser[section]:
                value = configParser[section][key]
                if value == None:
                    continue
                value = int(value)
                options[f"{section}_{key}"] = value
        return options

    def _checkpoint(self, runs, index):
        '''
            checkpoint make a file named in current timestamp
        '''
        importantValues = self.__dict__.copy()
        importantValues = dict(filter(lambda i: not callable(i[1]) and not isinstance(i[1], SalahSplitter), importantValues.items()))
        importantValues["current_runs"] = runs
        importantValues["last_processed_index"] = index + 1
        importantValues = jdumps(importantValues, sort_keys=True)
        loc = os.path.join(self.checkpointDir, currentTime() + ".json")
        with open(loc, "w") as checkpointFile:
            checkpointFile.write(importantValues)

    def _initFromCheckpointFile(self, checkpointFile):
        with open(checkpointFile) as file:
            perservedState = jloads(file.read())
        for k in perservedState.keys(): setattr(self, k, perservedState[k])
        return perservedState["current_runs"], perservedState["last_processed_index"]

def main():
    print("main splitter")
    options = _loadSplitOptions("algo.ini")
    runs = readRuns("input.txt")
    splitter = SalahSplitter(**options)
    def isProccessedBefore(dir_, fname, exportFormat):
        dir_ = os.path.dirname(dir_) if os.path.dirname(dir_) else dir_
        return os.path.exists(f"{dir_}/{fname}_S1.{exportFormat}")
    for filePath, exportFormat in runs:
        print(filePath, exportFormat)
        outdir, filename = getOutPath(outDir, filePath)
        # audio = SmartWavLoader(filePath)
        if (isProccessedBefore(outdir, filename, exportFormat)):
            print("file already processed before ==> ignoring it...")
            continue
        audio = AudioSegment.from_file(filePath)
        splitter.splitWithExport(audio, outdir , filename, exportFormat)


def _loadSplitOptions(path):
    configParser = ConfigParser(allow_no_value=True)
    configParser.read(path)
    options = {}
    sections = ['initial', 'adjust']
    for section in sections:
        for key in configParser[section]:
            value = configParser[section][key]
            if value == None:
                continue
            value = int(value)
            options[f"{section}_{key}"] = value
    return options

def readRuns(inputPath):
    extIgnore = []
    with open(".extignore", "r") as extIgnoreFile:
        extIgnore.extend([ext for ext in extIgnoreFile.read().split("\n")])
    runs = []
    with open(inputPath, encoding="utf-8") as f:
        origInput = f.read().splitlines(False)
        # origInput = [r.split(" ") for r in runs]
        # print(origInput)
        for run in origInput:
            ipath, fformat = run.split(" ") # TODO: error when path itself have spaces
            if(os.path.isfile(ipath)):
                ext = ipath.split(".")[-1]
                if ext in extIgnore:
                    continue
                runs.append([ipath, fformat])
            else:
                runs.extend([[os.path.join(root, filename), fformat] for root, subdirs, files in os.walk(ipath) if len(subdirs) == 0 for filename in files if not (filename.split(".")[-1] in extIgnore)])
    return runs



def getOutPath(baseOutDir, inputPath):
    nameNoExtension = os.path.basename(inputPath)[::-1].split(".", 1)[-1][::-1]
    dirPath = os.path.dirname(os.path.abspath(inputPath))[3:]
    relativePath = os.path.join(dirPath, nameNoExtension)
    return os.path.join(outDir, relativePath), nameNoExtension


def _isProccessedBefore(dir_, fname, exportFormat):
    dir_ = os.path.dirname(dir_) if os.path.dirname(dir_) else dir_
    return os.path.exists(f"{dir_}/{fname}_S1.{exportFormat}")

if __name__ == "__main__":
    tick("timing the whole run")
    # main()
    splitter = SplitterMain()
    # splitter.processRuns(outFormat="2020/{ifname}_{gnum} {snum}.{expoext}")
    splitter.recover("2020-04-27 22-22-35.json")
    tock("the whole run")