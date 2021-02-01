"Scripts in form that can be called from other functions"
import logging
import subprocess

def generateDatFile(inPath, outPath, converterLocation="audiowaveform"):
    cmd = f'"{converterLocation}" -i "{inPath}" -o "{outPath}" -z 256 -b 16'
    logging.info(f"issuing: {cmd}")
    process = subprocess.run(cmd, stderr=subprocess.PIPE)
    if(process.returncode != 0):
        # error
        logging.error(process.stderr.decode("utf-8"))
    process.check_returncode()





def runTestCases():
    logging.basicConfig(level=logging.DEBUG)
    generateDatFile("../audio_tests/ex1.wav", "../audio_tests/ex1.dat")

if __name__ == "__main__":
    runTestCases()