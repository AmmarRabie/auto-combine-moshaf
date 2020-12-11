'''
this file is responsible for indexing the quran ayat into indexer object
'''

from whoosh import index, query, fields, qparser, highlight
import xml.etree.ElementTree as ET
import os
import json

class QuranXmlReader():
    '''
    class that can return ayat connected to each other from any aya in any sura to another one
    '''
    def __init__(self, xmlPath="C:\Data\workspace\qur2an salah splitter\src\chapterfinder\quran-simple-clean.xml"):
        super().__init__()
        tree = ET.parse(xmlPath)
        self.root = tree.getroot()
    def getAyat(self, sura_from, sura_to, aya_from, aya_to):
        currentSura = self.root.find(f"./sura[@index='{sura_from}']")
        if(sura_from == sura_to): 
            return ' '.join(aya.attrib['text'] for aya in list(currentSura)[aya_from - 1:aya_to])
        res = ' '.join(aya.attrib['text'] for aya in list(currentSura)[aya_from - 1:])
        for currentSuraIndex in range(sura_from + 1, sura_to):
            currentSura = self.root.find(f"./sura[@index='{currentSuraIndex}']")
            res += ' ' + ' '.join(aya.attrib['text'] for aya in list(currentSura))

        currentSura = self.root.find(f"./sura[@index='{sura_to}']")
        res += ' ' + ' '.join(aya.attrib['text'] for aya in list(currentSura)[:aya_to])
        return res


class SearchEngine:
    '''
        Search engine for knowing where approximated text is located in which page in the madina moshaf.
    '''
    def __init__(self):
        super().__init__()
        self.groupOperator = qparser.OrGroup.factory(0.2)
        # self.groupOperator = qparser.OrGroup


    def buildIndexer(self, quranReader, indexDataDir="index_data", quranMetaDataPath="C:\Data\workspace\qur2an salah splitter\src\chapterfinder\quran-metadata.xml"):
        self.schema = fields.Schema(
                    ayat=fields.TEXT(stored=True),
                    pageNum=fields.NUMERIC(stored=True)
                )
        os.makedirs(indexDataDir, exist_ok=True)
        ix = index.create_in(indexDataDir, self.schema)
        writer = ix.writer()

        tree = ET.parse(quranMetaDataPath)
        root = tree.getroot()
        pages_root = root.find("pages")
        pagesElements = list(pages_root)

        for i in range(1, len(pagesElements)):
            sura_from, aya_from = pagesElements[i - 1].attrib['sura'], pagesElements[i - 1].attrib['aya']
            sura_to, aya_to = pagesElements[i].attrib['sura'], pagesElements[i].attrib['aya']
            sura_from, aya_from, sura_to, aya_to = [int(x) for x in (sura_from, aya_from, sura_to, aya_to)]
            if(aya_to != 1):
                aya_to -= 1
            else:
                sura_to -= 1
                aya_to = 300 # always take to the end aya in the sura, maximim is baqra of 286
            pageText = quranReader.getAyat(sura_from, sura_to, aya_from, aya_to)
            writer.add_document(ayat=pageText, pageNum=i)
        writer.commit()
        self.ix = ix
        self.parser = self._newParser()

    def loadIndexer(self, indexdir):
        self.ix = index.open_dir(indexdir)
        self.parser = self._newParser()

    def search(self, text, limit=None):
        '''
            search using last built or loaded index
            returns results, locations
            results is indicating the page number
            locations is the best match in the page itself
            locations is array of fragments, len(locations) = number of hits
            for each hit = results[i], the correspoding fragment = locations[i] is the list of ayat that matched in the page
            there may be no fragments at all in specific locations as there is no match and this should be in the very low score
        '''
        # TODO: optimize searching time and accuracy, with adding support to "filter" method, that is search in less documents and hence better accuracy
        q = self.parser.parse(text)
        with self.ix.searcher() as searcher:
            results = searcher.search(q, limit=limit)
            results.formatter = highlight.NullFormatter()
            results.order = highlight.SCORE
            locations = []
            for hit in results:
                pageNum = hit["pageNum"]
                # print(hit["pageNum"], str(hit.score))
                topHighlight = hit.highlights("ayat", top=1)
                # print(topHighlight)
                fragments = []
                with open(f"../quran_pages/{pageNum}.json") as f:
                    pageObj = json.loads(f.read())
                    ayat = pageObj['root']
                    for aya in ayat:
                        ayaText = aya['text']
                        fine = ayaText.find(str(topHighlight)) != -1 or str(topHighlight).find(ayaText) != -1
                        if(fine):
                            fragments.append(aya)
                locations.append(fragments)

            return results, locations

    def _newParser(self):
        return qparser.QueryParser("ayat", self.ix.schema, group=self.groupOperator)



if __name__ == "__main__":
    indexer = SearchEngine()
    indexer.loadIndexer("index_allstored")
    # indexer.buildIndexer(QuranXmlReader(), indexDataDir="index_allstored")
    tests = [
        u"انا ارسلنا في قريه ميت من نبي الا اخذنا اهلها ب البؤساء انا اخذنا اهلها بالباساء والضراء لعلهم يتضرعون ثم بدلنا مكان السيئه الحسنه حتى عفوا وقالون وقالوا قدم السا باء",
        u"ولو اننا نزلنا اليهم الملائكه وكلمهم الموتا وكلمهم الموتى وحشونا عليهم كل شيء قبل ما كانوا ما كانوا ليؤمنوا الا"
    ]
    results, locations = indexer.search(tests[1], limit=5)
    print(locations[0][0])