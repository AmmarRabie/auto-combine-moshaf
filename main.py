from configparser import ConfigParser
from splitter.splitter import SalahSplitter
from pydub import AudioSegment
import os
import threading
from incrementalload import incload, SmartWavLoader

outDir = "splitter_out"
def main():
    options = readSplitOptions("algo.ini")
    runs = readRuns("input.txt")
    splitter = SalahSplitter(**options)
    for filePath, exportFormat in runs:
        print(filePath, exportFormat)
        p = getOutPath(outDir, filePath)
        audio = SmartWavLoader(filePath)
        # audio = AudioSegment.from_file(filePath)
        splitter.splitWithExport(audio, p , exportFormat)

def readSplitOptions(path):
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
            ipath, fformat = run.split(" ")
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
    return os.path.join(outDir, relativePath)

if __name__ == "__main__":
    main()