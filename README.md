# auto-combine-moshaf
semi automatic moshaf creation from file sounds
## installation
install required packages
`pip install -r requirements.txt` <br>
if you want to work with (import or export) formats not '.wav' ones, you have to install ffmpeg and ffprobe
from [here](https://ffbinaries.com/downloads)
## modules
We have core, functions and apps layers
* **core**: core basic methods that functions uses one or more of them to achieve one concrete function
* **functions**: concrete function that applications can use them with manipulation other aspects to achieve one concrete app
### core module
core module currently contains these sub-modules
* **onset detection**: detect audio changes, yields position and whether the sound was increasing or decreasing
* **ASR**: Speech recognition that recognizes text from sound file
* **search engine**: search engine built for quran, given an approximated text (text that doesn't perfectly match any aya) return the most like aya of that text.
### functions
* **splitter**: split audio file into segments. segment is what program think that is a recitation of quran.
* **chapterfinder**: label segments and find chapter beginning
### apps
* **moshaf-builder**: This application manipulates .mb files. This project file contains information about where segments begin and end. in each segment what is chapters inside it. store steps to create the moshaf from all audio files

## important files
* **src/console.py**: This file runs a command line interface(CLI) for moshaf-builder application.