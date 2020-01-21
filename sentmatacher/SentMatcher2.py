import numpy as np
import editdistance
from bisect import bisect_left
from itertools import accumulate
from difflib import SequenceMatcher
import jellyfish
class SentMatcher():
    def __init__(self,corpus="quran-simple-clean.txt",minWordLenThresh=4):
        self.words = []
        self.sentsCummLen = []
        self.minWordLenThresh = minWordLenThresh
        with open(corpus,"r", encoding="utf-8") as corpusFile:
            self.sents = corpusFile.read().splitlines(False)

    def match(self, query):
        maxRatio = 0
        maxIndex = None
        for index, target in enumerate(self.sents):
            smaller = query
            larger = target
            if (len(smaller) > len(larger)):
                smaller, larger = larger, smaller
            smallerLength, largerLength = len(smaller), len(larger)

            words = larger.split(" ")
            offset = 0
            # matcher = SequenceMatcher(None, smaller)
            while offset <= largerLength - smallerLength:
                windowed = " ".join(words[offset:smallerLength])
                # matcher.set_seq2(windowed)
                # current = matcher.quick_ratio()
                current = SequenceMatcher(None, smaller, windowed).ratio()
                if (current > maxRatio):
                    maxRatio = current
                    maxIndex = index
                offset += 1
        return (maxIndex, maxIndex), maxRatio

    def match2(self, query):
        bestRatio = 0
        bestIndex = None
        print(len(self.sents))
        # dists = set()
        for index, target in enumerate(self.sents):
            smaller = query
            larger = target
            if (len(smaller) > len(larger)):
                smaller, larger = larger, smaller
            smallerLength, largerLength = len(smaller), len(larger)

            words = larger.split(" ")
            offset = 0
            # matcher = SequenceMatcher(None, smaller)
            while offset <= largerLength - smallerLength:
                windowed = " ".join(words[offset:smallerLength])
                # matcher.set_seq2(windowed)
                # current = matcher.quick_ratio()
                current = jellyfish.jaro_distance(windowed, smaller)
                # current = jellyfish.jaro_winkler(windowed, smaller)
                # dists.add(current)
                if (current > bestRatio):
                    bestRatio = current
                    bestIndex = index
                offset += 1
        # print(list(reversed(sorted(list(dists))))[0:20])
        return (bestIndex, bestIndex), bestRatio


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
            with open("../quran-simple-clean.txt","r", encoding="utf-8") as quranFile:
                quran = quranFile.readlines()
                for query in test:
                    matchRange,score = matcher.match2(query)
                    print(matchRange,score)
                    ayat=quran[matchRange[0]:matchRange[1]+1]
                    pred.write("".join(ayat)+"--------------\n")