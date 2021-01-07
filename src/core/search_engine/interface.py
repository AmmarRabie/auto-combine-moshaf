'''
Interfaces of core engine functions
'''


class EngineInterface():
    def __init__(self):
        pass


    def buildIndexer(self, indexDataDir):
        '''
            build indexer in the given @indexDataDir
        '''
        raise NotImplementedError(f"{self.__class__.__name__} class should implement buildIndexer method")


    def loadIndexer(self, indexdir):
        '''
            load indexer from the given @indexDataDir
        '''
        raise NotImplementedError(f"{self.__class__.__name__} class should implement loadIndexer method")


    def loadOrBuild(self, indexDir):
        '''
            load indexer from the given @indexDataDir if exists.
            if not exist, build it in the indexDir and load tne new one
        '''
        raise NotImplementedError(f"{self.__class__.__name__} class should implement loadOrBuild method")


    def search(self, text, limit=None):
        '''
            search using last built or loaded index
            returns array of best ayat
        '''
        raise NotImplementedError(f"{self.__class__.__name__} class should implement search method")
