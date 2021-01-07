'''
this file is responsible for indexing the quran ayat into indexer object
'''

from whoosh import index, query, fields, qparser, highlight, scoring
import xml.etree.ElementTree as ET
import os
import json
from difflib import SequenceMatcher

from .interface import EngineInterface

class QuranXmlReader():
    '''
    class that can return ayat connected to each other from any aya in any sura to another one
    '''
    def __init__(self, xmlPath="C:/Data/workspace/qur2an salah splitter/src/functions/chapterfinder/quran-simple-clean.xml"):
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


class TwoStagesSearchEngine(EngineInterface):
    '''
        Search engine for knowing where text is located in which page in the madina moshaf.
        Then search again in the given page.
        This is usefull for text that may correspond to multi connected ayat together
        As the whole page is considered the document in the first stage
        in the second stage, we use every aya in the page as a document
        This is incredibly usefull for motashabihat
    '''
    def __init__(self):
        super().__init__()
        self.groupOperator = qparser.OrGroup.factory(0.2)
        self.SEARCH_ENGINE_ALGO = False
        self.quranReader = QuranXmlReader()
        self.quranMetaDataPath = "C:/Data/workspace/qur2an salah splitter/src/functions/chapterfinder/quran-metadata.xml"
        # self.groupOperator = qparser.OrGroup


    def buildIndexer(self, indexDataDir="index_data"):
        self.schema = fields.Schema(
                    ayat=fields.TEXT(stored=True),
                    pageNum=fields.NUMERIC(stored=True)
                )
        os.makedirs(indexDataDir, exist_ok=True)
        ix = index.create_in(indexDataDir, self.schema)
        writer = ix.writer()

        tree = ET.parse(self.quranMetaDataPath)
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
            pageText = self.quranReader.getAyat(sura_from, sura_to, aya_from, aya_to)
            writer.add_document(ayat=pageText, pageNum=i)
        writer.commit()
        self.ix = ix
        self.parser = self._newParser()

    def loadIndexer(self, indexdir):
        self.ix = index.open_dir(indexdir)
        self.parser = self._newParser()

    def loadOrBuild(self, indexDir):
        if(index.exists_in(indexDir)): self.loadIndexer(indexDir)
        else: self.buildIndexer(QuranXmlReader(), indexDataDir=indexDir)

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
        with self.ix.searcher(weighting=scoring.BM25F()) as searcher:
            results = searcher.search(q, limit=limit, terms=True)
            results.formatter = highlight.NullFormatter()
            results.order = highlight.SCORE
            bestAyat = []
            hits = []
            for hit in results:
                pageNum = hit["pageNum"]
                # matchedTerms = list(map(lambda x: x[1].decode('utf-8'), hit.matched_terms()))
                # print(matchedTerms)
                # print(len(matchedTerms))
                # print(hit["pageNum"], str(hit.score))
                topHighlight = hit.highlights("ayat", top=1)
                
                # print(topHighlight)
                bestAya = self._getBestAyaMatch(pageNum, topHighlight)
                bestAya['page_score'] = hit.score
                bestAya['query_text'] = text
                bestAyat.append(bestAya)
                hits.append(hit)

            return hits, bestAyat

    def _getBestAyaMatch(self, *params):
        func = self._getBestAyaMatch_searchEngine if(self.SEARCH_ENGINE_ALGO) else self._getBestAyaMatch_seqMatcher
        return func(*params)

    def _getBestAyaMatch_seqMatcher(self, pageNum, topHighlight):
        with open(f"C:/Data/workspace/qur2an salah splitter/src/core/search_engine/quran_pages/{pageNum}.json") as f:
            pageObj = json.loads(f.read())
            ayat = pageObj['root']
        bestAya = None
        for pageIndex, aya in enumerate(ayat):
            ayaText = aya['text']
            fine = ayaText.find(str(topHighlight)) != -1 or str(topHighlight).find(ayaText) != -1
            if(fine):
                aya['pageIndex'] = pageIndex # offset from the page zero indexed
                aya['pageRatio'] = pageIndex / len(ayat) # location ratio
                aya['aya_score'] = 1
                bestAya = aya
                break
        if(bestAya != None): return bestAya
        mx = 0
        for pageIndex, aya in enumerate(ayat):
            ayaText = aya['text']
            score = SequenceMatcher(None, ayaText, topHighlight).quick_ratio()
            if(score > mx):
                aya['pageIndex'] = pageIndex # offset from the page zero indexed
                aya['pageRatio'] = pageIndex / len(ayat) # location ratio
                bestAya = aya
                mx = score
        bestAya['aya_score'] = mx
        return bestAya

    def _getBestAyaMatch_searchEngine(self, pageNum, topHighlight):
        '''
        find aya on specific page using search techniques
        '''
        print(pageNum, topHighlight)
        pageIndex = self._loadPageIndexer(pageNum)
        parser = self._newPageIndexParser(pageIndex)
        q = parser.parse(topHighlight)
        with pageIndex.searcher(weighting=scoring.BM25F()) as searcher:
            results = searcher.search(q, limit=1)
            hit = next(results)
            return {
                "sura": hit["sura"],
                "index": hit["ayaIndex"],
                "text": hit["ayaText"],
                "aya_score": hit.score,
                "page": hit["pageNum"]
            }

    def _newParser(self):
        return qparser.QueryParser("ayat", self.ix.schema, group=self.groupOperator)

    def _loadPageIndexer(self, pageNum):
        '''
        load specific page indexer
        '''
        indexDataDir = f"C:/Data/workspace/qur2an salah splitter/src/functions/chapterfinder/quran_pages_indexers/{pageNum}"
        return index.open_dir(indexDataDir)

    def _newPageIndexParser(self, pageIndexer):
        return qparser.QueryParser("ayaText", pageIndexer, group=self.groupOperator)


if __name__ == "__main__":
    indexer = TwoStagesSearchEngine()
    indexer.loadIndexer("C:\Data\workspace\qur2an salah splitter\src\core\search_engine\index_allstored")
    # indexer.buildIndexer(QuranXmlReader(), indexDataDir="index_allstored")
    tests = [
        # quran approximated
        u"انا ارسلنا في قريه ميت من نبي الا اخذنا اهلها ب البؤساء انا اخذنا اهلها بالباساء والضراء لعلهم يتضرعون ثم بدلنا مكان السيئه الحسنه حتى عفوا وقالون وقالوا قدم السا باء",
        u"ولو اننا نزلنا اليهم الملائكه وكلمهم الموتا وكلمهم الموتى وحشونا عليهم كل شيء قبل ما كانوا ما كانوا ليؤمنوا الا",
        u"له جنه تجري من تحتها الانهار كلما اعود قمنا من ثمره رزقا قالوا قالوا هذا الذي رزقنا من قبل وقوته به متشابها ولهم فيها ازواج مطهره وهم فيها خالدون",

        # quran approximated motshabihat
        u"بني اسرائيل اذكروا نعمتي التي انعمت عليكم واني فضلتكم على العالمين واتقوا يوما لا تجزى نفس عن نفس شيئا ولا يقبل منها عدل ولا تنفعها شفاعة ولا تنفعوا شفاعة ولا هم ينصرون",
        u"فانك لا تسمع الموتى ولا تسمع الصم الدعاء ولا تسمع الصم الدعاء الى ونلوم ده منين وما انت بهادي العمى عن ضلالتهم انفسنا ومن لا يؤمن باياتنا فهم مسلمون الله الذي خلقكم من ضعف ثم جعل من بعد ضعف قزة",        
        u"فانك لا تسمع الموتى ولا تسمع الصم الدعاء ولا تسمع الصم الدعاء الى ونلوم ده منين وما انت بهادي العمى عن ضلالتهم انفسنا ومن لا يؤمن باياتنا فهم مسلمون",

        # dros
        u"أعد الله سبحانه الجنة للأبرار الذين يحققون طاعة الله ورسوله هذه الطاعة متوقفة على أمرين هما الإيمان الحق وطاعة الله ورسوله في الأمر والنهي ومن جهل شيئاً عليه بسؤال أهل العلم",
        u"الله خالق السماوات والأرض فإذا ازداد الإيمان قوي عبد الله على طاعة الله ورسوله وبذلك يصبح من البررة الأبرار",
        u"يا عشاق دار السلام دار الأبرار هل تسمحون لي أن أعرض أمامكم شاشتين تشاهدون أنفسكم فمن وجد نفسه ظهر على الشاشة البيضاء النورانية القرانية حمد الله وبكى ومن لم يجد نفسه في تلك الشاشة الأولى ولا الثانية فليعلم أنه ما هو بالمؤمن فليطلب الإيمان",


        # do3a2
        u"اللهم إني أسألك يا الله بأنك الواحد الأحد الصمد الذي لم يلد ولم يولد ولم يكن له كفواً أحد أن تغفر لي ذنوبي إنك أنت الغفور الرحيم",
        u"اللهم إني أعوذ بك من يوم السوء ومن ليلة السوء ومن ساعة السوء ومن صاحب السوء ومن جار السوء في دار المقامة"
    ]

    results, locations = indexer.search(tests[4], limit=2)
    print(list(map(lambda h: h.score, results)), locations)
    # for t in tests:
    #     results, locations = indexer.search(t, limit=1)
    #     print(results[0].score)
