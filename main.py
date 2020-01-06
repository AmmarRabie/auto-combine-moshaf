from configparser import ConfigParser
from splitter import SalahSplitter
from pydub import AudioSegment
from os import makedirs, path

outDir = "spliiter_out"
def main():
    options = readSplitOptions("algo.ini")
    runs = readRuns("input.txt")
    splitter = SalahSplitter(**options)
    for filePath, exportFormat in runs:
        print(filePath, exportFormat)
        audio = AudioSegment.from_file(filePath)
        splitter.splitWithExport(audio, path.join(outDir, path.basename(filePath)), exportFormat)

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

def readRuns(path):
    runs = []
    with open(path) as f:
        runs = f.read().splitlines(False)
        runs = [r.split(" ") for r in runs]
    return runs

if __name__ == "__main__":
    main()