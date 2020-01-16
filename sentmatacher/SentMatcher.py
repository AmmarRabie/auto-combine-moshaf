import numpy as np
import editdistance
from bisect import bisect_left
from itertools import accumulate

class SentMatcher():
    def __init__(self,corpus="quran-simple-clean.txt",minWordLenThresh=4):
        self.words = []
        self.sentsCummLen = []
        self.minWordLenThresh = minWordLenThresh
        with open(corpus,"r", encoding="utf-8") as test:
            sents = [list(self._preprocess(sent.split())) for sent in test.readlines()]
            self.sentsCummLen =  list(accumulate(map(len,sents)))
            self.words = [word for sent in sents for word in sent]

    def match(self,query,terminationThresh = 100,acceptingThresh = .6,queryRejectThresh = 2,dataRejectThresh = 4):
        matches=[]
        query = self._preprocess(query.split())
        distance = lambda pred,ref: max(0, 1 - editdistance.eval(pred,ref) / len(pred))

        queryI = 0
        dataRejected = 0
        matchStart = None
        def reset():
            nonlocal queryI,dataRejected,matchStart
            queryI = 0
            dataRejected = 0
            matchStart = None

        i=0
        while i<len(self.words):
            if(queryI>=terminationThresh-1):
                return self._getSentsRange(matchStart,len(query))

            if(queryI >= len(query)):
                refStr = ' '.join(self.words[matchStart:matchStart+len(query)])
                queryStr = ' '.join(query)
                confideceScore = distance(queryStr,refStr)
                matches.append((matchStart,confideceScore))
                reset()

            canSkip = min(len(query)-queryI,queryRejectThresh+1)
            dists = [distance(query[queryI+disp],self.words[i]) for disp in range(canSkip)]
            bestDistI = np.argmax(dists + [acceptingThresh])
            
            if(bestDistI < canSkip and dists[bestDistI] >= acceptingThresh):
                dataRejected = 0
                queryI += bestDistI+1
                matchStart = i if matchStart == None else matchStart
            else:
                dataRejected+=1
                if(dataRejected > dataRejectThresh):
                    if(queryI):
                        i-= dataRejectThresh+1
                    reset()
            i+=1
        
        bestMatch = max(matches,key=lambda matchScorePair: matchScorePair[-1])
        return self._getSentsRange(bestMatch[0],len(query)),bestMatch[1]

    def _preprocess(self,sent):
        return sent
        # for i,word  in enumerate(sent):
        #     if(len(word)>=self.minWordLenThresh):
        #         continue
        #     if i+1<len(sent):
        #         sent[i+1] = sent[i]+sent[i+1] 
        #     else:
        #         sent[i-1] = sent[i-1]+sent[i] 
        
        # res = [word for word in sent if len(word)>=self.minWordLenThresh]
        # return res or sent

    def _getSentsRange(self,i,querySize):
        low = bisect_left(self.sentsCummLen,i+1)
        high = bisect_left(self.sentsCummLen,i+querySize)
        return low,high
        

if __name__ == "__main__":
    # matcher = SentMatcher("text.txt")
    matcher = SentMatcher("../quran-simple-clean.txt")

    with open("test.txt","r", encoding="utf-8") as test:
        with open("pred.txt","w",encoding="utf-8") as pred:
            for query in test:
                matchRange,score = matcher.match(query)
                print(matchRange,score)
                with open("../quran-simple-clean.txt","r", encoding="utf-8") as quran:
                    ayat=quran.readlines()[matchRange[0]:matchRange[1]+1]
                    pred.write("".join(ayat)+"--------------\n")



