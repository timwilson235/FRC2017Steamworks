# -*- coding: utf-8 -*-
"""
bucketvision

Many hands make light work!
A multi-threaded vision pipeline example for Bit Buckets Robotics that
looks like a bucket brigade

Thanks to Igor Maculan for an mjpg streaming solution!
https://gist.github.com/n3wtron/4624820

Copyright (c) 2017 - RocketRedNeck.com RocketRedNeck.net 

RocketRedNeck and MIT Licenses 

RocketRedNeck hereby grants license for others to copy and modify this source code for 
whatever purpose other's deem worthy as long as RocketRedNeck is given credit where 
where credit is due and you leave RocketRedNeck out of it for all other nefarious purposes. 

Permission is hereby granted, free of charge, to any person obtaining a copy 
of this software and associated documentation files (the "Software"), to deal 
in the Software without restriction, including without limitation the rights 
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
copies of the Software, and to permit persons to whom the Software is 
furnished to do so, subject to the following conditions: 

The above copyright notice and this permission notice shall be included in all 
copies or substantial portions of the Software. 

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
SOFTWARE. 
**************************************************************************************************** 
"""

import cv2
import numpy as np
import time
import logging      # Needed if we want to see debug messages from NetworkTables
import platform


from networktables import NetworkTables

from camera import Camera         # Camera capture 
from processor import Processor   # Image processing 
from server import Server         # Web server
from framerate import FrameRate
from bitrate import BitRate


# Instances of GRIP created pipelines (they usually require some manual manipulation
# but basically we would pass one or more of these into one or more image processors (threads)
# to have their respective process(frame) functions called.
from nada import Nada
from gearlift import GearLift


if (platform.system() == 'Windows'):
    roboRioAddress = '127.0.0.1'
elif( platform.system() == 'Darwin'):
    roboRioAddress = '127.0.0.1'
else:
    roboRioAddress = '10.41.83.2' # On competition field


# And so it begins
print("Starting VISION!")

# To see messages from networktables, you must setup logging
logging.basicConfig(level=logging.DEBUG)

try:
    NetworkTables.setIPAddress(roboRioAddress)
    NetworkTables.setClientMode()
    NetworkTables.initialize()
    
except ValueError as e:
    print(e)
    print("\n\n[WARNING]: BucketVision NetworkTable Not Connected!\n\n")

bvTable = NetworkTables.getTable("BucketVision")
bvTable.putString("BucketVisionState", "Starting")

# Auto updating listeners from the network table
currentCam = bvTable.getAutoUpdateValue('CurrentCam', 'frontCam') # 'frontCam' or 'rearCam'
frontCamMode = bvTable.getAutoUpdateValue('FrontCamMode', 'gearLift') # 'gearLift' or 'Boiler'
alliance = bvTable.getAutoUpdateValue('AllianceColor', 'red')   # default until chooser returns a value



# NOTE: NOTE: NOTE:
#
# YOUR MILEAGE WILL VARY
# The exposure values are cameras/driver dependent and have no well defined standard (i.e., non-portable)
# Our implementation is forced to use v4l2-ctl (Linux) to make the exposure control work because our OpenCV
# port does not seem to play well with the exposure settings (produces either no answer or causes errors depending
# on the cameras used)
FRONT_CAM_GEAR_EXPOSURE = 0
FRONT_CAM_NORMAL_EXPOSURE = -1   # Camera default

frontCam = Camera(name="FrontCam", src=0, width=320, height=240, 
                  exposure=FRONT_CAM_GEAR_EXPOSURE).start()

while not frontCam.isRunning():
    time.sleep(0.001)

print("Cameras appear online!")


# Processing pipelines for Front Processor
frontPipes = {'redBoiler'   : Nada('RedBoiler'),
              'blueBoiler'  : Nada('BlueBoiler'),
              'gearLift'    : GearLift('GearLift', bvTable)
              }

frontProcessor = Processor("frontProcessor", frontCam, frontPipes['gearLift']).start()

frontProc2 = Processor( "frontProc2", frontCam, frontPipes['redBoiler']).start()

while not frontProcessor.isRunning():
    time.sleep(0.001)
while not frontProc2.isRunning():
    time.sleep(0.001)
    
print("Processors appear online!")



# Redirect port 80 to 8080
# keeping us legal on the field (i.e., requires 80)
# AND eliminating the need to start this script as root
#
#cmd = ['sudo iptables -t nat -D PREROUTING 1']
#call(cmd,shell=True)
#cmd = ['sudo iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 -j REDIRECT --to-port 8080']
#call(cmd,shell=True)
#cmd = ['sudo iptables -t nat -D PREROUTING 2']
#call(cmd,shell=True)
#cmd = ['sudo iptables -t nat -A PREROUTING -i wlan0 -p tcp --dport 80 -j REDIRECT --to-port 8080']
#call(cmd,shell=True)

# Maps network table "CurrentCam" value to Processor
processors = {'frontCam' : frontProcessor, 'front2' : frontProc2}

# Feeds the HTTP server the video stream from selected processor
class DisplayStream:
    def __init__(self):
        self.fps = FrameRate()
        self.bitrate = BitRate()

    def get(self):
        
        theProcessor = processors[currentCam.value]                                   
        img = theProcessor.read()
            
        self.fps.start()

        # Write some useful info on the frame
        camFps, camUtil = theProcessor.camera.fps.get()
        procFps, procUtil = theProcessor.fps.get()
        srvFps, srvUtil = self.fps.get()
        srvBitrate = self.bitrate.get()

        cv2.putText(img, "{:.1f} : {:.0f}%".format(camFps, 100*camUtil), (0, 20), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 1)
        cv2.putText(img, "{:.1f} : {:.0f}%".format(procFps, 100*procUtil), (0, 40), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 1)
        cv2.putText(img, "{:.1f} : {:.0f}% : {:.2f}".format(srvFps, 100*srvUtil, srvBitrate), (0, 60), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 1)
        cv2.putText(img, currentCam.value, (0, 80), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 1)
        cv2.putText(img, theProcessor.pipeline.name, (0, 100), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 1)

        _, jpg = cv2.imencode(".jpg", img, (cv2.IMWRITE_JPEG_QUALITY, 80))
        buf = bytearray(jpg)
        
        self.bitrate.update(len(buf))      
        self.fps.stop()

        return buf
    
    
server = Server(DisplayStream()).start()
while not server.isRunning():
    time.sleep(0.001)
print("Server appears online!")


bvTable.putString("BucketVisionState","ONLINE")

runTime = 0
bvTable.putNumber("BucketVisionTime", runTime)
nextTime = time.time() + 1.0

# Need a visible window for waitKey to work
cv2.imshow("Nothing", np.zeros((100,100)))

while True:

    if time.time() > nextTime :
        nextTime += 1.0
        runTime += 1.0
        bvTable.putNumber("BucketVisionTime", runTime)


    if frontCamMode.value == 'gearLift' :
        frontCam.setExposure(FRONT_CAM_GEAR_EXPOSURE)
    elif frontCamMode.value == 'blueBoiler' or frontCamMode.value == 'redBoiler':
        frontCam.setExposure(FRONT_CAM_NORMAL_EXPOSURE)

    frontProcessor.setPipeline( frontPipes[frontCamMode.value])
    
    
    key = cv2.waitKey(100)
    if key == ord('x') :
        break    
    frontCam.processUserCommand(key)
        

# do a bit of cleanup
cv2.destroyAllWindows()

print("Goodbye!")

