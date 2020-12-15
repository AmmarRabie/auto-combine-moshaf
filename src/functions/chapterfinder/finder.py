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
        # first aya in the segment
        approximatedText = "ولو أننا نزلنا إليهم الملائكة وكلمهم الموتى وحشرنا عليهم كل شيء قبلا ما كانوا ليؤمنوا إلا أن يشاء الله" #self.asr.recognizeGoogle(filePath, start, duration)
        results, locations = self.searchEngine.search(approximatedText, limit=1)
        bestAya1 = locations[0][0]

        # second aya in the segment
        approximatedText = "فريقا هدى وفريقا حق عليهم الضلالة إنهم اتخذوا الشياطين أولياء من دون الله ويحسبون أنهم مهتدون" #self.asr.recognizeGoogle(filePath, end - duration, duration)
        results, locations = self.searchEngine.search(approximatedText, limit=1)
        bestAya2 = locations[0][0]
        
        print(bestAya1)
        print(bestAya2)
        page1, page2 = bestAya1['page'], bestAya2['page']
        # find chapters
        chapters = self.chaptersInRange(page1, page2)
        for chapterIndex, chapterBegin in chapters:
            # try finding the location in the segment that chapter begin
            print(f"try finding the second where chapter #{chapterIndex} begin (page #{chapterBegin})")
            # expect
            totalPages = page2 - page1
            approxPageDuration = totalDuration / totalPages # 134 seconds per page
            expected = start + approxPageDuration * (chapterBegin - page1)
            expected = min(expected, end - self.EXAMINE_DURATION) # always be in segment 
            increasing = False
            while(expected < end and expected > start):
                approximatedText = self.asr.recognizeGoogle(filePath, expected, duration)
                results, locations = self.searchEngine.search(approximatedText, limit=1) # TODO: narrow down the search documents here
                actualPage = locations[0][0]['page']
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

    def findOnPage(self, filePath, duration, locations, expected, increasing, chapterIndex):
        '''
        adjuts @param:expected value in page to more close to the first aya in the @param:chapterIndex
        '''
        currentAya = locations[0][0]['index']
        currentSura = locations[0][0]['sura']
        while(not (currentSura == chapterIndex and currentAya >= 1 and currentAya <= 3)):
            approximatedText = self.asr.recognizeGoogle(filePath, expected, duration)
            results, locations = self.searchEngine.search(approximatedText, limit=1) # TODO: narrow down the search documents here
            if(len(results) == 0 or len(locations[0]) == 0):
                expected += 20 if increasing else -20
                continue
            currentAya = locations[0][0]['index']
            currentSura = locations[0][0]['sura']
            print(currentAya)
            if(currentSura < chapterIndex):
                expected += 20
                increasing = True
            elif(currentSura > chapterIndex):
                expected -= 20
                increasing = False
            else: # same sura but current aya is far away
                expected -= 20
                increasing = False
        return expected

    def findOnPage_faster(self, filePath, duration, results, locations, expected, increasing, chapterIndex):
        '''
        adjuts @param:expected value in page to more close to the first aya in the @param:chapterIndex
        '''
        # start with big shift and every time increasing changes, decrease the shift value
        currentAya = locations[0][0]['index']
        currentSura = locations[0][0]['sura']
        shift = 80
        while(not (currentSura == chapterIndex and currentAya >= 1 and currentAya <= chaptersMaxAya[chapterIndex - 1])):
            if(len(results) == 0 or len(locations[0]) == 0):
                expected += shift if increasing else -shift
                continue
            if(currentSura < chapterIndex): # previous sura
                expected += shift
                if(not increasing): # toggling event
                    shift //= 2
                increasing = True
            else: # next sura or same sura but current aya is far away
                expected -= shift
                if(increasing): # toggling event
                    shift //= 2
                increasing = False
            approximatedText = self.asr.recognizeGoogle(filePath, expected, duration)
            results, locations = self.searchEngine.search(approximatedText, limit=1) # TODO: narrow down the search documents here
            currentAya = locations[0][0]['index']
            currentSura = locations[0][0]['sura']
            print("sura, aya:", currentSura, currentAya)
        return expected


# this is because first 3 ayat of a chapter may be so long or so short. so we want a dynamic mapping that
# tell the first 3 sentences of each chapter ends in which aya index
chaptersMaxAya = [ # index is chapter index in zero based.. value is max aya index that gives 3 sentences
4, 3, 3, 1, 1, 1, 2, 1, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
]
if __name__ == "__main__":
    finder = Finder()
    chapters = finder.find("C:\\Data\\القران كامل\\4\\ZOOM0002.WAV", 64, 1541)
    print(chapters)