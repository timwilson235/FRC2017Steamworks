
from threading import Thread
from threading import Lock
from mailbox import Mailbox

from framerate import FrameRate

class Processor:
    def __init__(self, name, camera, pipeline):
        print("Creating Processor: camera=" + camera.name + " pipeline=" + pipeline.name)
        
        self.name = name
        self.camera = camera
        self.pipeline = pipeline
        self.lock = Lock()
        
        self.mailbox = Mailbox()
        self.fps = FrameRate()
        
        self.running = False

        
    def start(self):
        print("Processor " + self.name + " STARTING")
        t = Thread(target=self.run, args=())
        t.daemon = True
        t.start()
        return self

    def run(self):
        print("Processor " + self.name + " RUNNING")
        self.running = True
       
        while True:

            frame = self.camera.read(id(self))
            
            self.fps.start()

            self.lock.acquire()
            pipeline = self.pipeline
            self.lock.release()
            
            pipeline.process(frame)
            self.mailbox.put(frame)

            self.fps.stop()
                

    def setPipeline(self, pipeline):
        if pipeline == self.pipeline:
            return
        
        self.lock.acquire()
        self.pipeline = pipeline
        self.lock.release()
        print( "Processor " + self.name + " pipeline now=" + pipeline.name)

    def read(self):
        return self.mailbox.get()
          

    def isRunning(self):
        return self.running

