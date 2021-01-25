class ISplitter(object):
    def __init__(self):
        raise NotImplementedError("Can't construct ISplitter interface")
        
    def prepareAudio(self, audio):
        'called for each audio before calling split'
        raise NotImplementedError(f"{self.__class__.__name__} class should implement recognize method") 

    def split(self):
        raise NotImplementedError(f"{self.__class__.__name__} class should implement recognize method")
