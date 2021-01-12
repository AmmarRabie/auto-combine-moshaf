# Usage: python generate_data_files.py path_to_mb_project_file


import sys
import json
import subprocess


# converterLocation = "C:/Data/Others/progs/audiowaveform-1.4.2-win64/audiowaveform.exe"
converterLocation = "audiowaveform.exe"
def main():
    args = sys.argv
    if(len(args) != 2):
        print("Usage: python generate_data_files.py path_to_mb_project_file")
        return
    mbPath = args[1]
    with open(mbPath) as mbFile:
        files = json.loads(mbFile.read())["project"]["files"]
    paths = map(lambda f: f['path'], files)
    for p in paths:
        audioExt = p.split(".")[-1]
        dataPath = p.replace("." + audioExt, ".dat")
        cmd = f'"{converterLocation}" -i "{p}" -o "{dataPath}" -z 256 -b 8'
        print("issuing", cmd)
        process = subprocess.run(cmd)
        process.check_returncode()
        
    

if __name__ == "__main__":
    main()