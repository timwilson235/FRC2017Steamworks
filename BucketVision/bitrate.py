'''
Created on Apr 2, 2017

@author: twilson
'''
from stopwatch import StopWatch

class BitRate:
    def __init__(self):
        self._stopwatch = StopWatch()
        self._totBytes = 0
        self._numFrames = 0
        self._bitrate = 0.0
        
        self._stopwatch.start()
    
    def update(self, bytecnt):
        self._numFrames += 1
        self._totBytes += bytecnt
    
    # Returns bitrate in kBit/sec
    def get(self):
        if self._numFrames > 10 :
            totTime = self._stopwatch.stop()
            self._bitrate = (8*self._totBytes/totTime)/1000.0
            self._numFrames = 0
            self._totBytes = 0
        
        return self._bitrate
            
        