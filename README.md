# auto-combine-moshaf
automatic moshaf creation from file sounds
## installation
install required packages
`pip install -r requirements.txt` <br>
if you want to work with (import or export) formats not '.wav' ones,  you have to install ffmpeg and ffprobe
from [here](https://ffbinaries.com/downloads)
## run
to run the program, you have to edit input.txt. every single line in the input is a run. you specify the input path and the export format like <br>
`filedir/filepathwithextension exportformat` <br>
then run `python main.py`
# features
## available
- detect start and the end of connected sound
## currently in develoing
- detect 'allah akbar' at the end of the voice
## future features
- detect start and the end of quran chapters
