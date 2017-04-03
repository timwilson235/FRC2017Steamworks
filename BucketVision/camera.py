# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 20:46:25 2017

@author: mtkes
"""
## NOTE: OpenCV interface to camera controls is sketchy
## use v4l2-ctl directly for explicit control
## example for dark picture: v4l2-ctl -c exposure_auto=1 -c exposure_absolute=10

# import the necessary packages

import cv2

from subprocess import call
from threading import Thread
from threading import Condition

import platform

# import our classes

from framerate import FrameRate

# This CANNOT be shared between multiple Processors!

class Camera:
    def __init__(self, name, src, width, height, exposure):

        print("Creating Camera for " + name)
        
        self.name = name
        self.src = src
        self.exposure = exposure
                
        self.stream = cv2.VideoCapture(src)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH,width)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT,height)
        
        self.condition = Condition()
        self.fps = FrameRate()
        
        self.setExposure()

        self.rate = self.stream.get(cv2.CAP_PROP_FPS)
        print("RATE = " + str(self.rate))
        self.brightness = self.stream.get(cv2.CAP_PROP_BRIGHTNESS)
        print("BRIGHT = " + str(self.brightness))
        self.contrast = self.stream.get(cv2.CAP_PROP_CONTRAST)
        print("CONTRAST = " + str(self.contrast))
        self.saturation = self.stream.get(cv2.CAP_PROP_SATURATION)
        print("SATURATION = " + str(self.saturation))
        print("EXPOSURE = " + str(self.exposure))
        

        self.frameAvail = False
        self.count = 0
        self.running = False


    def start(self):
        print("STARTING Camera for " + self.name)
        t = Thread(target=self.run, args=())
        t.daemon = True
        t.start()
        return self

    def run(self):
        print("Camera for " + self.name + " RUNNING")
        self.running = True
        
        lastExposure = self.exposure
        
        while True:

            if (lastExposure != self.exposure):
                self.setExposure()
                lastExposure = self.exposure

            # otherwise, read the next frame from the stream
            (grabbed, frame) = self.stream.read()
            
            self.fps.start()
            
            
            # grabbed will be false if camera has been disconnected.
            # How to deal with that??
            # Should probably try to reconnect somehow? Don't know how...
                
            if grabbed:
                self.count += 1
                
                self.condition.acquire()
                self.outCount = self.count
                self.outFrame = frame.copy()
                self.frameAvail = True
                self.condition.notify()
                self.condition.release()
            
            self.fps.stop()

                
    def read(self):       
        self.condition.acquire()
        while not self.frameAvail:
            self.condition.wait()
        outFrame = self.outFrame
        outCount = self.outCount
        self.frameAvail = False
        self.condition.release()
        return (outFrame, outCount)

    def processUserCommand(self, key):
        if key == ord('x'):
            return True
        elif key == ord('w'):
            self.brightness+=1
            self.stream.set(cv2.CAP_PROP_BRIGHTNESS,self.brightness)
            print("BRIGHT = " + str(self.brightness))
        elif key == ord('s'):
            self.brightness-=1
            self.stream.set(cv2.CAP_PROP_BRIGHTNESS,self.brightness)
            print("BRIGHT = " + str(self.brightness))
        elif key == ord('d'):
            self.contrast+=1
            self.stream.set(cv2.CAP_PROP_CONTRAST,self.contrast)
            print("CONTRAST = " + str(self.contrast))
        elif key == ord('a'):
            self.contrast-=1
            self.stream.set(cv2.CAP_PROP_CONTRAST,self.contrast)
            print("CONTRAST = " + str(self.contrast))
        elif key == ord('e'):
            self.saturation+=1
            self.stream.set(cv2.CAP_PROP_SATURATION,self.saturation)
            print("SATURATION = " + str(self.saturation))
        elif key == ord('q'):
            self.saturation-=1
            self.stream.set(cv2.CAP_PROP_SATURATION,self.saturation)
            print("SATURATION = " + str(self.saturation))
        elif key == ord('z'):
            self.exposure+=1
            self.setExposure(self.exposure)
            print("EXPOSURE = " + str(self.exposure))
        elif key == ord('c'):
            self.exposure-=1
            self.setExposure(self.exposure)
            print("EXPOSURE = " + str(self.exposure))
            
##        elif key == ord('p'):
##            self.iso +=1
##            self.stream.set(cv2.CAP_PROP_ISO_SPEED, self.iso)
##        elif key == ord('i'):
##            self.iso -=1
##            self.stream.set(cv2.CAP_PROP_ISO_SPEED, self.iso)

        return False

    def updateExposure(self, exposure):
        self.exposure = exposure
        return
    
    def setExposure(self):
        # cv2 exposure control DOES NOT WORK ON PI - or Mac (Darwin)
        if (platform.system() == 'Windows' or platform.system() == 'Darwin'):
            self.stream.set(cv2.CAP_PROP_EXPOSURE,self.exposure)
        else:
            cmd = ['v4l2-ctl --device=' + str(self.src) + ' -c exposure_auto=1 -c exposure_absolute=' + str(self.exposure)]
            call(cmd,shell=True)
        
    
    def isRunning(self):
        return self.running

