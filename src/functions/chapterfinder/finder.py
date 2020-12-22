from core.search_engine import SearchEngine
from core.asr import ASR

class Finder:
    '''
        Take a segment and find if a chapter beginning is in it
        try to get the location of the beginning
    '''
    def __init__(self):
        super().__init__()
        self.EXAMINE_DURATION = 30 # seconds
        self.asr = ASR()
        self.searchEngine = SearchEngine()
        self.searchEngine.loadOrBuild(indexDir="search_engine/index_allstored")
        self.chaptersBeginnings = self.readChaptersBeginnings()
    
    def find(self, filePath, start, end):
        '''
        filepath: original file that have the pray including the recitation
        start: start of the recitation rak3a
        end: end of the recitation rak3a
        segment = audio(filepath)[start:end]
        this function examines first 30 seconds of the segment, and last 30 seconds of the segment
        '''
        totalDuration = end - start
        duration = min(totalDuration, self.EXAMINE_DURATION)

        def continuousFind(xstart, shift): # validate the result till find applicable one
            maxTests = 15
            while(True):
                approximatedText = self.asr.recognizeGoogle(filePath, xstart, duration)
                print("approximatedText:", approximatedText)
                if(len(approximatedText) < 45):
                    xstart += shift
                    print(f"approximated text is very short.. we will try next block. try next block @ {xstart}")
                    continue
                results, locations = self.searchEngine.search(approximatedText, limit=1)
                bestAya = locations[0]
                if(bestAya['page_score'] > 20): return bestAya, True
                xstart += shift
                print(bestAya)
                print(f"very low page score={bestAya['page_score']} < 20. try next block @ {xstart}")
                maxTests -= 1
                if(maxTests == 0):
                    print("max tests of 15 reached. break now")
                    return None, False
        # first aya in the segment
        bestAya1, succ = continuousFind(start, self.EXAMINE_DURATION)
        if(not succ):
            return

        # last aya in the segment
        bestAya2, succ = continuousFind(end, -self.EXAMINE_DURATION)
        if(not succ):
            return
        
        print(bestAya1)
        print(bestAya2)
        page1, page2 = bestAya1['page'], bestAya2['page']
        sura1, sura2 = bestAya1['sura'], bestAya2['sura']
        totalPages = page2 - page1 + 1
        approxPageDuration = totalDuration / totalPages # 134 seconds per page
        # find chapters
        chapters = self.chaptersInRange(page1, page2)
        for chapterIndex, chapterBegin in chapters:
            if not (chapterIndex >= sura1 and chapterIndex <= sura2): continue # to ignore case of begin of chapter is not in the begin of page. and reciter has not start in the new chapter
            # try finding the location in the segment that chapter begin
            print(f"try finding the second where chapter #{chapterIndex} begin (page #{chapterBegin})")
            # expect
            expected = start + approxPageDuration * (chapterBegin - page1)
            expected = min(expected, end - self.EXAMINE_DURATION) # always be in segment 
            increasing = False
            maxTests = 15
            while(expected < end and expected > start):
                maxTests -= 1
                approximatedText = self.asr.recognizeGoogle(filePath, expected, duration)
                if(approximatedText):
                    results, locations = self.searchEngine.search(approximatedText, limit=1) # TODO: narrow down the search documents here
                    actualPage = locations[0]['page']
                else:
                    print("ASR returns None @find")
                print(f"actual page, wanted page = {actualPage}, {chapterBegin}")
                if(actualPage == chapterBegin):
                    print(f"chapter {chapterIndex} is around {expected} seconds")
                    # try finding first aya location
                    expected = self.findOnPage_faster(filePath, duration, results, locations, expected, increasing, chapterIndex)
                    print(f"chapter {chapterIndex} is most probably at {expected} seconds")
                    break
                elif(actualPage > chapterBegin):
                    expected -= self.EXAMINE_DURATION
                    increasing = False
                elif(actualPage < chapterBegin):
                    expected += self.EXAMINE_DURATION
                    increasing = True
                if(maxTests == 0):
                    print("max tests of 15 exceeded, we will break in current expected value")
                    break
            yield chapterIndex, expected
        


    def chaptersInRange(self, startPage, endPage):
        res = []
        for chapterIndex, chapterBegin in enumerate(self.chaptersBeginnings):
            # chapterIndex is zero based
            chapterBegin = int(chapterBegin)
            if(chapterBegin >= startPage and chapterBegin <= endPage):
                res.append([chapterIndex + 1, chapterBegin])
            if(chapterBegin > endPage): break
        return res

    def readChaptersBeginnings(self):
        with open("C:/Data/workspace/qur2an salah splitter/src/functions/chapterfinder/chapters_begin_page.txt") as f:
            return f.read().splitlines(False)

    def readChaptersInfos(self):
        with open("C:/Data/workspace/qur2an salah splitter/src/functions/chapterfinder/chapters_page_info.txt") as f:
            return f.read().splitlines(False)

    def findOnPage(self, filePath, duration, results, locations, expected, increasing, chapterIndex):
        '''
        adjuts @param:expected value in page to more close to the first aya in the @param:chapterIndex
        '''
        # start with big shift and every time increasing changes, decrease the shift value
        currentAya = locations[0]['index']
        currentSura = locations[0]['sura']
        shift = 80
        maxTests = 15
        while(not (currentSura == chapterIndex and currentAya >= 1 and currentAya <= chaptersMaxAya[chapterIndex - 1])):
            if(len(results) == 0 or len(locations[0]) == 0):
                expected += shift if increasing else -shift
                continue
            if(currentSura < chapterIndex): # previous sura
                expected += shift
                if(not increasing): # toggling event
                    shift /= 1.5
                increasing = True
            else: # next sura or same sura but current aya is far away
                expected -= shift
                if(increasing): # toggling event
                    shift /= 1.5
                increasing = False
            approximatedText = self.asr.recognizeGoogle(filePath, expected, duration)
            if(not approximatedText):
                print("ASR returns None @findOnPage_faster")
                break
            results, locations = self.searchEngine.search(approximatedText, limit=1) # TODO: narrow down the search documents here
            currentAya = locations[0]['index']
            currentSura = locations[0]['sura']
            print("sura, aya:", currentSura, currentAya, "and shift=", shift, "we are in", expected)
            maxTests -= 1
            if(maxTests == 0):
                print("max tests of 15 exceeded, we will break in current expected value")
                break
        return expected


# this is because first 3 ayat of a chapter may be so long or so short. so we want a dynamic mapping that
# tell the first 3 sentences of each chapter ends in which aya index
chaptersMaxAya = [ # index is chapter index in zero based.. value is max aya index that gives 3 sentences
4, 3, 3, 1, 1, 1, 2, 1, 2, 2, 3, 3, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
]
if __name__ == "__main__":
    finder = Finder()
    chapters = finder.find("C:\\Data\\القران كامل\\4\\ZOOM0002.WAV", 64, 1541)
    print(chapters)