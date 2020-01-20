from configparser import ConfigParser
from splitter.splitter import SalahSplitter
from pydub import AudioSegment
import os

outDir = "splitter_out"
def main():
    options = readSplitOptions("algo.ini")
    runs = readRuns("input.txt")
    splitter = SalahSplitter(**options)
    for filePath, exportFormat in runs:
        print(filePath, exportFormat)
        audio = AudioSegment.from_file(filePath)
        p = os.path.join(os.path.join(outDir, os.path.dirname(filePath)[3:], os.path.basename(filePath)))
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
    runs = []
    with open(inputPath, encoding="utf-8") as f:
        origInput = f.read().splitlines(False)
        # origInput = [r.split(" ") for r in runs]
        print(origInput)
        for run in origInput:
            ipath, fformat = run.split(" ")
            print(ipath, fformat)
            if(os.path.isfile(ipath)):
                runs.append([ipath, fformat])
            else:
                runs.extend([ [os.path.join(root, filename), fformat] for root, subdirs, files in os.walk(ipath) if len(subdirs) == 0 for filename in files])
    return runs

if __name__ == "__main__":
    main()