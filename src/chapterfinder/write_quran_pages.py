import xml.etree.ElementTree as ET
import os
import json


class QuranWriter():
    '''
    class that can return ayat connected to each other from any aya in any sura to another one
    '''
    def __init__(self, xmlPath="C:\Data\workspace\qur2an salah splitter\src\chapterfinder\quran-simple-clean.xml"):
        super().__init__()
        tree = ET.parse(xmlPath)
        self.root = tree.getroot()
        self.data = []

    def writeAyat(self, pageNum, sura_from, sura_to, aya_from, aya_to):
        currentSura = self.root.find(f"./sura[@index='{sura_from}']")
        def updateList(sura, lst):
            for aya in lst:
                ayaIndex, ayaText = aya.attrib['index'], aya.attrib['text']
                self.data.append({"sura": sura, "index": int(ayaIndex), "text": ayaText, "page": pageNum})
        if(sura_from == sura_to):
            updateList(sura_from, list(currentSura)[aya_from - 1:aya_to])
            return self.commit(f"quran_pages/{pageNum}.json")

        updateList(sura_from, list(currentSura)[aya_from - 1:])
        for currentSuraIndex in range(sura_from + 1, sura_to):
            currentSura = self.root.find(f"./sura[@index='{currentSuraIndex}']")
            updateList(currentSuraIndex, list(currentSura))

        currentSura = self.root.find(f"./sura[@index='{sura_to}']")
        updateList(sura_to, list(currentSura)[:aya_to])
        self.commit(f"quran_pages/{pageNum}.json")

    def commit(self, file):
        '''
            commit changes to given file and clear data object again
        '''
        jsonStr = json.dumps({"root": self.data})
        with open(file, 'wt') as f:
            f.write(jsonStr)
        self.data = []


quranMetaDataPath = "C:\Data\workspace\qur2an salah splitter\src\chapterfinder\quran-metadata.xml"

tree = ET.parse(quranMetaDataPath)
root = tree.getroot()
pages_root = root.find("pages")
pagesElements = list(pages_root)
pagesElements.append(ET.Element("page", attrib={"sura":"115", "aya": "1"}))

os.makedirs("quran_pages", exist_ok=True)
writer = QuranWriter()
for i in range(1, len(pagesElements)):
    pageNum = i
    sura_from, aya_from = pagesElements[i - 1].attrib['sura'], pagesElements[i - 1].attrib['aya']
    sura_to, aya_to = pagesElements[i].attrib['sura'], pagesElements[i].attrib['aya']
    sura_from, aya_from, sura_to, aya_to = [int(x) for x in (sura_from, aya_from, sura_to, aya_to)]
    if(aya_to != 1):
        aya_to -= 1
    else:
        sura_to -= 1
        aya_to = 300 # always take to the end aya in the sura, maximim is baqra of 286
    writer.writeAyat(pageNum, sura_from, sura_to, aya_from, aya_to)

