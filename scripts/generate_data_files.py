# Usage: python generate_data_files.py path_to_mb_project_file


import sys
import json
import subprocess


# converterLocation = "C:/Data/Others/progs/audiowaveform-1.4.2-win64/audiowaveform.exe"
converterLocation = "audiowaveform"
def main():
    args = sys.argv
    if(len(args) != 2):
        print("Usage: python generate_data_files.py path_to_mb_project_file")
        return
    mbPath = args[1]
    with open(mbPath) as mbFile:
        project = json.loads(mbFile.read())
        files = project["project"]["files"]
    # paths = map(lambda f: f['path'], files)
    for f in files:
        p = f['path']
        audioExt = p.split(".")[-1]
        dataPath = p.replace("." + audioExt, ".dat")
        cmd = f'"{converterLocation}" -i "{p}" -o "{dataPath}" -z 256 -b 16'
        # TODO: use --pixels-per-second, so that we be indpendent of samplerate and number of frames..
        # cmd = f'"{converterLocation}" -i "{p}" -o "{dataPath}" -b 16 --pixels-per-second 200'
        # cmd = f'ffmpeg -i "{p}" -f wav pipe:1 | {converterLocation} --input-foramt wav --output-format dat -b 16 > "{dataPath}"'
        print("issuing", cmd)
        process = subprocess.run(cmd)
        process.check_returncode()
        f['data_path'] = dataPath
    with open(mbPath, 'wt', encoding='utf-8') as resultFile:
        resultFile.write(json.dumps(project))

    

if __name__ == "__main__":
    main()