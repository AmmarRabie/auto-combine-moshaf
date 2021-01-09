'''
Write quran pages for in each aya. creates folder quran_pages, this folder conatains 604 file equals the number of 
quran pages. each file corresponds ayat in this page.
also find all beginning of each sura and ending.
'''

import xml.etree.ElementTree as ET
import os
import json
from whoosh import index, fields

class QuranWriter():
    '''
    class that can return ayat connected to each other from any aya in any sura to another one
    '''
    def __init__(self, xmlPath="../assets/quran-simple-clean.xml"):
        super().__init__()
        tree = ET.parse(xmlPath)
        self.root = tree.getroot()
        self.data = []
        self.extraData = []

    def writeAyat(self, pageNum, sura_from, sura_to, aya_from, aya_to):
        currentSura = self.root.find(f"./sura[@index='{sura_from}']")
        def updateList(sura, lst, suraObj):
            for aya in lst:
                ayaIndex, ayaText = aya.attrib['index'], aya.attrib['text']
                self.data.append({"sura": sura, "index": int(ayaIndex), "text": ayaText, "page": pageNum})
                ayas = len(suraObj)
                if(ayaIndex == '1'):
                    print("start")
                    self.extraData.append({"sura": sura, "page_start": pageNum})
                if(ayaIndex == str(ayas)):
                    print("end")
                    self.extraData[sura - 1]['page_end'] = pageNum
                    self.extraData[sura - 1]['ayas'] = ayas

        if(sura_from == sura_to):
            updateList(sura_from, list(currentSura)[aya_from - 1:aya_to], currentSura)
            return self.commit(pageNum)

        updateList(sura_from, list(currentSura)[aya_from - 1:], currentSura)
        for currentSuraIndex in range(sura_from + 1, sura_to):
            currentSura = self.root.find(f"./sura[@index='{currentSuraIndex}']")
            updateList(currentSuraIndex, list(currentSura), currentSura)

        currentSura = self.root.find(f"./sura[@index='{sura_to}']")
        updateList(sura_to, list(currentSura)[:aya_to], currentSura)
        self.commit(pageNum)

    def commit(self, pageNum):
        '''
            commit changes to given file and clear data object again
        '''
        file = f"../assets/quran_pages/{pageNum}.json"
        jsonStr = json.dumps({"root": self.data})
        with open(file, 'wt') as f:
            f.write(jsonStr)
        self.data = []

    def writeExtraData(self, path):
        with open(path, 'wt') as f:
            for info in self.extraData:
                s, e = info['page_start'], info['page_end']
                f.write(f"{s}\t{e}\n")






class QuranPageIndexer(QuranWriter):
    '''
    class that build the indexing for every page in the quran
    '''
    def __init__(self, xmlPath="../assets/quran-simple-clean.xml"):
        super().__init__(xmlPath=xmlPath)

    def commit(self, pageNum):
        '''
            commit changes to given file and clear data object again
        '''
        self.schema = fields.Schema(
                    ayaText=fields.TEXT(stored=True),
                    ayaIndex=fields.NUMERIC(stored=True),
                    suraIndex=fields.NUMERIC(stored=True),
                    pageNum=fields.NUMERIC(stored=True)
                )
        indexDataDir = f"../assets/quran_pages_indexers/{pageNum}"
        os.makedirs(indexDataDir, exist_ok=True)
        ix = index.create_in(indexDataDir, self.schema)
        writer = ix.writer()
        for aya in self.data:
            writer.add_document(ayaText=aya["text"], ayaIndex=aya["index"], suraIndex=aya["sura"], pageNum=aya["page"])
        writer.commit()

        self.data = []

    def writeExtraData(self, path):
        with open(path, 'wt') as f:
            for info in self.extraData:
                s, e = info['page_start'], info['page_end']
                f.write(f"{s}\t{e}\n")


quranMetaDataPath = "../assets/quran-metadata.xml"

tree = ET.parse(quranMetaDataPath)
root = tree.getroot()
pages_root = root.find("pages")
pagesElements = list(pages_root)
pagesElements.append(ET.Element("page", attrib={"sura":"115", "aya": "1"}))

os.makedirs("../assets/quran_pages", exist_ok=True)
# writer = QuranWriter()
writer = QuranPageIndexer()
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

# writer.writeExtraData("../assets/chapters_page_begin_end.txt")










def chaptersInRange(self, startPage, endPage):
    res = []
    for chapterIndex, chapterInfo in enumerate(self.chaptersBeginnings):
        # chapterIndex is zero based
        chapterBegin, chapterEnd, ayas = list(map(int, chapterInfo.split("\t")))
        if(chapterBegin >= startPage and chapterBegin <= endPage):
            res.append([chapterIndex + 1, chapterBegin])
        if(chapterBegin > endPage): break
    return res