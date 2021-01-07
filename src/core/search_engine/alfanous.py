from .interface import EngineInterface
import requests

__all__ = ["AlfanousOnlineEngine"]

class AlfanousOnlineEngine(EngineInterface):
    '''
    Easy implementation of quran search engine, just uses the Alfanous json service (API)
    '''
    def __init__(self):
        self.jo2Root = "http://www.alfanous.org/jos2"
        self.defaultParams = {
            "action": "search",
            "unit": "aya",
            "sura_info": False,
            "word_info": False,
            "word_derivations": False,
            "word_vocalizations": False,
            "prev_aya": False,
            "next_aya": False,
            "vocalized": False,
            "highlight": "bold",
        }


    def buildIndexer(self, indexDataDir):
        pass

    def loadIndexer(self, indexdir):
        pass

    def loadOrBuild(self, indexDir):
        pass

    def search(self, text, limit=1):
        if(limit > 25): raise ValueError("limit have to be from 1 to 25")
        params = {** self.defaultParams, "query": text, "perpage": limit}
        req = requests.get(self.jo2Root, params=params)
        rootRes = req.json()
        result = []
        for i in range(1, limit + 1):
            txt = myget(rootRes, f"search/ayas/{i}/aya/text")
            txt = txt.replace("</b>", "")
            txt = txt.replace("<b>", "")
            current = {
                "query_text": text, # approximated searched text
                "page": myget(rootRes, f"search/ayas/{i}/position/page"),
                "text": txt, # original aya text
                "index": myget(rootRes, f"search/ayas/{i}/identifier/aya_id"), # aya index in the sura
                "sura": myget(rootRes, f"search/ayas/{i}/identifier/sura_id"), # sura index in the moshaf
            }
            result.append(current)
        return result

def myget(d, path):
    keys = path.split("/")
    value = d[keys[0]]
    for k in keys[1:]:
        value = value[k]
    return value

if __name__ == "__main__":
    from pprint import pprint
    tests = ["يا ايها الذين ئلنتي اعب ربكمو الذي خلقكم والذين من قبلكم لعلكم"]
    engine = AlfanousOnlineEngine()
    for i, t in enumerate(tests):
        print("-"*10, f"test #{i}", "-"*10)
        res = engine.search(t, limit=2)
        pprint(res)
        print() # separate tests
