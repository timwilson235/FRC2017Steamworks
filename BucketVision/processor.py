
from threading import Thread
from threading import Condition

from framerate import FrameRate

class Processor:
    def __init__(self, camera, pipeline):
        print("Creating Processor for " + camera.name)
        
        self.name = camera.name
        self.camera = camera
        self.pipeline = pipeline
        
        self.fps = FrameRate()
        self.condition = Condition()
        self.frameAvailable = False
        
        self.running = False

        print("Processor created for " + self.name)
        
    def start(self):
        print("STARTING Processor for " + self.name)
        t = Thread(target=self.run, args=())
        t.daemon = True
        t.start()
        return self

    def run(self):
        print("Processor for " + self.name + " RUNNING")
        # keep looping infinitely until the thread is stopped
        self.running = True

        
        while True:

            (frame, count) = self.camera.read()
            
            self.fps.start()

            self.condition.acquire()
            pipeline = self.pipeline
            self.condition.release()
            
            pipeline.process(frame)

                
            # Now that image processing is complete, place results
            # into an outgoing buffer to be grabbed at the convenience
            # of the reader
            self.condition.acquire()
            self.outFrame = frame
            self.outCount = count
            self.frameAvailable = True
            self.condition.notify()
            self.condition.release()

            self.fps.stop()
                
        print("Processor for " + self.name + " STOPPING")

    def setPipeline(self, pipeline):
        self.condition.acquire()
        self.pipeline = pipeline
        self.condition.release()

    def read(self):
        
        self.condition.acquire()
        while not self.frameAvailable:
            self.condition.wait()           
        outFrame = self.outFrame
        outCount = self.outCount
        self.frameAvailable = False
        self.condition.release()
        return (outFrame, outCount)
          

    def isRunning(self):
        return self.running

