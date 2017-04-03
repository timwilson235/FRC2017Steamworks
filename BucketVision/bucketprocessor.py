
from threading import Thread
from threading import Condition

from framerate import FrameRate

class BucketProcessor:
    def __init__(self, camera, pipeline):
        print("Creating BucketProcessor for " + camera.name)
        self.name = camera.name
        self.pipeline = pipeline
        
        self.fps = FrameRate()
        self.camera = camera
        self._condition = Condition()
        self.frameAvailable = False
        
        self._running = False

        print("BucketProcessor created for " + self.name)
        
    def start(self):
        print("STARTING BucketProcessor for " + self.name)
        t = Thread(target=self.run, args=())
        t.daemon = True
        t.start()
        return self

    def run(self):
        print("BucketProcessor for " + self.name + " RUNNING")
        # keep looping infinitely until the thread is stopped
        self._running = True

        
        while True:

            (frame, count) = self.camera.read()
            
            self.fps.start()

            self._condition.acquire()
            pipeline = self.pipeline
            self._condition.release()
            
            pipeline.process(frame)

                
            # Now that image processing is complete, place results
            # into an outgoing buffer to be grabbed at the convenience
            # of the reader
            self._condition.acquire()
            self.outFrame = frame
            self.outCount = count
            self.frameAvailable = True
            self._condition.notify()
            self._condition.release()

            self.fps.stop()
                
        print("BucketProcessor for " + self.name + " STOPPING")

    def updatePipeline(self, pipeline):
        self._condition.acquire()
        self.pipeline = pipeline
        self._condition.release()

    def read(self):
        
        self._condition.acquire()
        while not self.frameAvailable:
            self._condition.wait()           
        outFrame = self.outFrame
        outCount = self.outCount
        self.frameAvailable = False
        self._condition.release()
        return (outFrame, outCount)
          

    def isRunning(self):
        return self._running

