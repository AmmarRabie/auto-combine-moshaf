'''
Interfaces of core ASR functions
'''


class ASRInterface():
    def __init__(self):
        pass


    def recognize(self, audioPath, start, duration):
        '''
            recognize text from audio file, from @start seconds to @start + @duration seconds
        '''
        raise NotImplementedError(f"{self.__class__.__name__} class should implement recognize method")
