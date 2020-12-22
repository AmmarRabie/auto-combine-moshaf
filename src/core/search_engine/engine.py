'''
this file is responsible for indexing the quran ayat into indexer object
'''

from whoosh import index, query, fields, qparser, highlight, scoring
import xml.etree.ElementTree as ET
import os
import json
from difflib import SequenceMatcher

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


class SearchEngine:
    '''
        Search engine for knowing where approximated text is located in which page in the madina moshaf.
    '''
    def __init__(self):
        super().__init__()
        self.groupOperator = qparser.OrGroup.factory(0.2)
        # self.groupOperator = qparser.OrGroup


    def buildIndexer(self, quranReader, indexDataDir="index_data", quranMetaDataPath="C:/Data/workspace/qur2an salah splitter/src/functions/chapterfinder/quran-metadata.xml"):
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
                with open(f"C:/Data/workspace/qur2an salah splitter/src/core/search_engine/quran_pages/{pageNum}.json") as f:
                    pageObj = json.loads(f.read())
                    ayat = pageObj['root']
                bestAya = self._getBestAyaMatch(ayat, topHighlight)
                bestAya['page_score'] = hit.score
                bestAyat.append(bestAya)
                hits.append(hit)

            return hits, bestAyat

    def _getBestAyaMatch(self, ayat, topHighlight):
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
        bestAya['aya_score'] = mx
        return bestAya

    def _newParser(self):
        return qparser.QueryParser("ayat", self.ix.schema, group=self.groupOperator)



if __name__ == "__main__":
    indexer = SearchEngine()
    indexer.loadIndexer("C:\Data\workspace\qur2an salah splitter\src\core\search_engine\index_allstored")
    # indexer.buildIndexer(QuranXmlReader(), indexDataDir="index_allstored")
    tests = [
        u"انا ارسلنا في قريه ميت من نبي الا اخذنا اهلها ب البؤساء انا اخذنا اهلها بالباساء والضراء لعلهم يتضرعون ثم بدلنا مكان السيئه الحسنه حتى عفوا وقالون وقالوا قدم السا باء",
        u"ولو اننا نزلنا اليهم الملائكه وكلمهم الموتا وكلمهم الموتى وحشونا عليهم كل شيء قبل ما كانوا ما كانوا ليؤمنوا الا",
        u"له جنه تجري من تحتها الانهار كلما اعود قمنا من ثمره رزقا قالوا قالوا هذا الذي رزقنا من قبل وقوته به متشابها ولهم فيها ازواج مطهره وهم فيها خالدون",

        u"أعد الله سبحانه الجنة للأبرار الذين يحققون طاعة الله ورسوله هذه الطاعة متوقفة على أمرين هما الإيمان الحق وطاعة الله ورسوله في الأمر والنهي ومن جهل شيئاً عليه بسؤال أهل العلم",
        u"الله خالق السماوات والأرض فإذا ازداد الإيمان قوي عبد الله على طاعة الله ورسوله وبذلك يصبح من البررة الأبرار",
        u"يا عشاق دار السلام دار الأبرار هل تسمحون لي أن أعرض أمامكم شاشتين تشاهدون أنفسكم فمن وجد نفسه ظهر على الشاشة البيضاء النورانية القرآنية حمد الله وبكى ومن لم يجد نفسه في تلك الشاشة الأولى ولا الثانية فليعلم أنه ما هو بالمؤمن فليطلب الإيمان",

        u"إن الذين كفروا سواء عليهم أأنذرتهم أم لم تنذرهم لا يؤمنون ختم الله على قلوبهم وعلى سمعهم وعلى أبصارهم غشاوة ولهم عذاب عظيم ومن الناس من يقول آمنا بالله وباليوم الآخر وما هم بمؤمنين يخادعون الله والذين آمنوا وما يخدعون إلا أنفسهم وما يشعرون في قلوبهم مرض فزادهم الله مرضا ولهم عذاب أليم بما كانوا يكذبون وإذا قيل لهم لا تفسدوا في الأرض قالوا إنما نحن مصلحون ألا إنهم هم المفسدون ولكن لا يشعرون وإذا قيل لهم آمنوا كما آمن الناس قالوا أنؤمن كما آمن السفهاء ألا إنهم هم السفهاء ولكن لا يعلمون وإذا لقوا الذين آمنوا قالوا آمنا وإذا خلوا إلى شياطينهم قالوا إنا معكم إنما نحن مستهزئون الله يستهزئ بهم ويمدهم في طغيانهم يعمهون أولئك الذين اشتروا الضلالة بالهدى فما ربحت تجارتهم وما كانوا مهتدين",


        u"اللهم إني أسألك يا الله بأنك الواحد الأحد الصمد الذي لم يلد ولم يولد ولم يكن له كفواً أحد أن تغفر لي ذنوبي إنك أنت الغفور الرحيم",
        u"اللهم إني أعوذ بك من يوم السوء ومن ليلة السوء ومن ساعة السوء ومن صاحب السوء ومن جار السوء في دار المقامة"
    ]

    results, locations = indexer.search(tests[-2], limit=1)
    print(list(map(lambda h: h.score, results)), locations)
    # for t in tests:
    #     results, locations = indexer.search(t, limit=1)
    #     print(results[0].score)
