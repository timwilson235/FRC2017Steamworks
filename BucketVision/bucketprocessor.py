
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
        
        # initialize the variable used to indicate if the thread should
        # be stopped
        self._stop = False
        self.stopped = True

        print("BucketProcessor created for " + self.name)
        
    def start(self):
        print("STARTING BucketProcessor for " + self.name)
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        print("BucketProcessor for " + self.name + " RUNNING")
        # keep looping infinitely until the thread is stopped
        self.stopped = False

        
        while True:
            # if the thread indicator variable is set, stop the thread
            if (self._stop == True):
                self._stop = False
                self.stopped = True
                return

            # otherwise, read the next frame from the stream
            # grab the frame from the threaded video stream
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
          
    def stop(self):
        # indicate that the thread should be stopped
        self._stop = True
        
        self._condition.acquire()
        self.frameAvailable = True
        self._condition.notify()
        self._condition.release()

    def isStopped(self):
        return self.stopped
		
