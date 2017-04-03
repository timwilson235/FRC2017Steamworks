# -*- coding: utf-8 -*-
"""
bucketvision

Many hands make light work!
A multi-threaded vision pipeline example for Bit Buckets Robotics that
looks like a bucket brigade

Thanks to Igor Maculan for an mjpg steaming solution!
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

# import the necessary packages

import cv2
import numpy as np
import time


from networktables import NetworkTables
import logging      # Needed if we want to see debug messages from NetworkTables

# import our classes

from bucketcapture import BucketCapture     # Camera capture threads... may rename this
from bucketprocessor import BucketProcessor   # Image processing threads... has same basic structure (may merge classes)
from bucketserver import BucketServer       # Run the HTTP service
from framerate import FrameRate
from bitrate import BitRate

import platform

if (platform.system() == 'Windows'):
    roboRioAddress = '127.0.0.1'
elif( platform.system() == 'Darwin'):
    roboRioAddress = '127.0.0.1'
else:
    roboRioAddress = '10.41.83.2' # On competition field


# Instances of GRIP created pipelines (they usually require some manual manipulation
# but basically we would pass one or more of these into one or more image processors (threads)
# to have their respective process(frame) functions called.

from nada import Nada
from gearlift import GearLift


# And so it begins
print("Starting BUCKET VISION!")

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
bvTable.putString("BucketVisionState","Starting")

# Auto updating listener should be good for avoiding the need to poll for value explicitly
# A ChooserControl is also another option

# Auto updating listeners from the network table
currentCam = bvTable.getAutoUpdateValue('CurrentCam','frontCam') # 'frontCam' or 'rearCam'
frontCamMode = bvTable.getAutoUpdateValue('FrontCamMode', 'gearLift') # 'gearLift' or 'Boiler'
alliance = bvTable.getAutoUpdateValue('allianceColor','red')   # default until chooser returns a value


# NOTE: NOTE: NOTE:
#
# YOUR MILEAGE WILL VARY
# The exposure values are cameras/driver dependent and have no well defined standard (i.e., non-portable)
# Our implementation is forced to use v4l2-ctl (Linux) to make the exposure control work because our OpenCV
# port does not seem to play well with the exposure settings (produces either no answer or causes errors depending
# on the cameras used)
FRONT_CAM_GEAR_EXPOSURE = 0
FRONT_CAM_NORMAL_EXPOSURE = -1   # Camera default

frontCam = BucketCapture(name="FrontCam", src=0, width=320, height=240, 
                         exposure=FRONT_CAM_GEAR_EXPOSURE).start()

while not frontCam.isRunning():
    time.sleep(0.001)

print("BucketCapture appears online!")

# NOTE: NOTE: NOTE
#
# Reminder that each image processors should process exactly one vision pipeline
# at a time (it can be selectable in the future) and that the same vision
# pipeline should NOT be sent to different image processors as this is simply
# confusing and can cause some comingling of data (depending on how the vision
# pipeline was defined... we can't control the use of object-specific internals
# being run from multiple threads... so don't do it!)


frontPipes = {'redBoiler'   : Nada('RedBoiler'),
              'blueBoiler'  : Nada('BlueBoiler'),
              'gearLift'    : GearLift('gearLift', bvTable)
            }

frontProcessor = BucketProcessor(frontCam, frontPipes['gearLift']).start()

processors = {'frontCam' : frontProcessor}

while not frontProcessor.isRunning():
    time.sleep(0.001)
print("BucketProcessors appear online!")



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

# Feeds the HTTP server the video stream from selected Processor
class DisplayStream:
    def __init__(self):
        self.fps = FrameRate()
        self.bitrate = BitRate()

    def get(self):
        
        theProcessor = processors[currentCam.value]                                   
        (img, _) = theProcessor.read()
            

        self.fps.start()

        # Write some useful info on the frame
        camFps, camUtil = theProcessor.camera.fps.get()
        procFps, procUtil = theProcessor.fps.get()
        srvFps, srvUtil = self.fps.get()
        srvBitrate = self.bitrate.get()

        cv2.putText(img, "{:.1f} : {:.0f}%".format(camFps, 100*camUtil), (0, 20), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 1)
        cv2.putText(img, "{:.1f} : {:.0f}%".format(procFps, 100*procUtil), (0, 40), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 1)
        cv2.putText(img, "{:.1f} : {:.0f}% : {:.1f}".format(srvFps, 100*srvUtil, srvBitrate), (0, 60), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 1)
        cv2.putText(img, currentCam.value, (0, 80), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 1)
        cv2.putText(img, theProcessor.pipeline.name, (0, 100), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 1)

        _, buf = cv2.imencode(".jpg", img)
        
        self.bitrate.update(len(buf))      
        self.fps.stop()

        return buf
    
    
server = BucketServer(DisplayStream()).start()
while not server.isRunning():
    time.sleep(0.001)
print("BucketServer appears online!")


bvTable.putString("BucketVisionState","ONLINE")

runTime = 0
bvTable.putNumber("BucketVisionTime",runTime)
nextTime = time.time() + 1

# Need a visible window for waitKey to work
cv2.imshow("Nothing", np.zeros((100,100)))

while True:

    if (time.time() > nextTime):
        nextTime = nextTime + 1
        runTime = runTime + 1
        bvTable.putNumber("BucketVisionTime",runTime)

    if (frontCamMode.value == 'gearLift'):
        frontProcessor.updatePipeline(frontPipes['gearLift'])
        frontCam.updateExposure(FRONT_CAM_GEAR_EXPOSURE)
    elif (frontCamMode.value == 'Boiler'):
        frontProcessor.updatePipeline(frontPipes[alliance.value + "Boiler"])
        frontCam.updateExposure(FRONT_CAM_NORMAL_EXPOSURE)

    key = cv2.waitKey(100)
    
    if key != -1:
        print key

    if (frontCam.processUserCommand(key) == True):
        break
        

# do a bit of cleanup
cv2.destroyAllWindows()

print("Goodbye!")

