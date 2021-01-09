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
        self.SAME_TIME_THRESHOLD = 7 # seconds. if abs(t - start) < SAME_TIME_THRESHOLD, we will consider t as start
        self.asr = ASR()
        self.searchEngine = SearchEngine()
        self.searchEngine.loadOrBuild(indexDir="./core/search_engine/index_allstored")
        self.chaptersBeginnings = self.readChaptersBeginnings()
        self.chaptersInfo = self.readChaptersInfos()
    
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
        bestAyaStart, succ = continuousFind(start, duration)
        if(not succ):
            return None

        # last aya in the segment
        bestAyaEnd, succ = continuousFind(end - duration, -duration)
        if(not succ):
            return None
        
        print(bestAyaStart)
        print(bestAyaEnd)
        page1, page2 = bestAyaStart['page'], bestAyaEnd['page']
        sura1, sura2 = bestAyaStart['sura'], bestAyaEnd['sura']
        totalPages = page2 - page1 + 1
        approxPageDuration = totalDuration / totalPages # 134 seconds per page
        if(page2 < page1 or sura2 < sura1):
            print("pageEnd < pageStart. segment expected wrongly")
            return None
        # find chapters
        chapters = self.chaptersInRange(page1, page2)
        chaptersResult = [{} for _ in range(len(chapters))]
        chapterOnBeginning = False # flag to check pre-part of first chapter in the segment
        for cri, chapterInfo in enumerate(chapters):
            chapterIndex, chapterPageBegin = chapterInfo
            if not (chapterIndex >= sura1 and chapterIndex <= sura2): # to ignore case of begin of chapter is not in the begin of page. and reciter has not start in the new chapter
                continue
            # try finding the location in the segment that chapter begin
            print(f"try finding the page where chapter #{chapterIndex} begin (page #{chapterPageBegin})")
            # expect
            expected = start + approxPageDuration * (chapterPageBegin - page1)
            expected = min(expected, end - self.EXAMINE_DURATION) # always be in segment 
            bestAya, newExpected, succ = self.findPageSecond(filePath, expected, duration, start, end, chapterPageBegin)
            increasing = newExpected > expected
            expected = newExpected
            print(f"chapter {chapterIndex} is around {expected} seconds")
            if(succ):
                # try finding first aya location on the page if we succeeded in finding wanted page
                bestAya, expected = self.findOnPage(filePath, duration, bestAya, expected, increasing, chapterIndex)
                print(f"chapter {chapterIndex} is most probably at {expected} seconds")
            if(abs(start - expected) < self.SAME_TIME_THRESHOLD):
                print(f"adjust {expected} to the beginning of the segment({start}) as it is more reasonable")
                expected = start
                chapterOnBeginning = True
                bestAya = bestAyaStart
            chaptersResult[cri]["expected_start"] = expected
            chaptersResult[cri]["is_accurate"] = succ
            chaptersResult[cri]["is_first_part"] = True
            chaptersResult[cri]["is_last_part"] = False
            chaptersResult[cri]["best_aya"] = bestAya
            if(cri > 0):
                chaptersResult[cri - 1]["expected_end"] = expected
                chaptersResult[cri]["is_last_part"] = True
        while {} in chaptersResult:
            chaptersResult.remove({})
        if(len(chaptersResult) > 0):
            if(not chapterOnBeginning):
                expectedEnd = chaptersResult[0]['expected_start']
                acc = chaptersResult[0]['is_accurate']
                chaptersResult.insert(0, {
                    "expected_start": start,
                    "expected_end": expectedEnd,
                    "is_accurate": acc,
                    "is_first_part": False,
                    "is_last_part": True, # because we know that after it there is a chapter
                    "best_aya": bestAyaStart
                })
            chaptersResult[-1]["expected_end"] = end
        else:
            chaptersResult.append({
                "expected_start": start,
                "expected_end": end,
                "is_accurate": True,
                "is_first_part": False,
                "is_last_part": False, # maybe the last part
                "best_aya": bestAyaStart
            })
        return chaptersResult
        

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
        with open("../assets/chapters_begin_page.txt") as f:
            return f.read().splitlines(False)

    def readChaptersInfos(self):
        with open("../assets/chapters_page_info.txt") as f:
            return f.read().splitlines(False)


    def findPageSecond(self, filePath, expected, duration, mn, mx, targetPage):
        expected = expected or mn
        increasing = None # this value will be overridden in the first iteration
        maxTests = 15
        actualPage = targetPage - 1 # work around for None in first iteration issue
        while(expected <= mx and expected >= mn): # get the wanted page
            maxTests -= 1
            approximatedText = self.asr.recognizeGoogle(filePath, expected, duration)
            if(approximatedText):
                results, locations = self.searchEngine.search(approximatedText, limit=1) # TODO: narrow down the search documents here
                actualPage = locations[0]['page'] # TODO: if in first iteration text is None, this will cause error in the check "actualPage == targetPage" 
            else:
                print("ASR returns None @find at", expected)
            print(f"actual page, wanted page = {actualPage}, {targetPage}")
            if(actualPage == targetPage):
                return locations[0], expected, True
            elif(actualPage > targetPage):
                expected -= self.EXAMINE_DURATION
                increasing = False
            elif(actualPage < targetPage):
                expected += self.EXAMINE_DURATION
                increasing = True
            if(maxTests == 0):
                print("max tests of 15 exceeded, we will break in current expected value")
                break
        return locations[0], expected, False
    def findOnPage(self, filePath, duration, bestAya, expected, increasing, chapterIndex):
        '''
        adjuts @param:expected value in page to more close to the first aya in the @param:chapterIndex
        '''
        # start with big shift and every time increasing changes, decrease the shift value
        currentAya = bestAya['index']
        currentSura = bestAya['sura']
        shift = self.EXAMINE_DURATION
        maxTests = 15
        print("sura, aya:", currentSura, currentAya, "and shift=", shift, "we are in", expected)
        while(not (currentSura == chapterIndex and currentAya >= 1 and currentAya <= chaptersMaxAya[chapterIndex - 1])):
            maxTests -= 1
            if(maxTests < 0):
                print("max tests of 15 exceeded, we will break in current expected value")
                break
            if(currentSura < chapterIndex): # previous sura
                expected += shift
                if(not increasing): # toggling event
                    shift /= 1.5
                    shift = max(shift, 1)
                increasing = True
            else: # next sura or same sura but current aya is far away
                expected -= shift
                if(increasing): # toggling event
                    shift /= 1.5
                    shift = max(shift, 1)
                increasing = False
            approximatedText = self.asr.recognizeGoogle(filePath, expected, duration)
            if(not approximatedText):
                print("ASR returns None @findOnPage")
                break
            results, locations = self.searchEngine.search(approximatedText, limit=1) # TODO: narrow down the search documents here
            if(len(results) == 0 or len(locations) == 0):
                expected += shift if increasing else -shift
                continue
            bestAya = locations[0]
            currentAya = bestAya['index']
            currentSura = bestAya['sura']
            print("sura, aya:", currentSura, currentAya, "and shift=", shift, "we are in", expected)
        return bestAya, expected


# this is because first 3 ayat of a chapter may be so long or so short. so we want a dynamic mapping that
# tell the first 3 sentences of each chapter ends in which aya index
chaptersMaxAya = [ # index is chapter index in zero based.. value is max aya index that gives 3 sentences
4, 3, 3, 1, 1, 1, 2, 1, 2, 2, 3, 3, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
]
if __name__ == "__main__":
    finder = Finder()
    chapters = finder.find("C:\\Data\\القران كامل\\4\\ZOOM0002.WAV", 64, 1541)
    print(chapters)