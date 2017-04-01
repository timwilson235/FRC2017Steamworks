# -*- coding: utf-8 -*-
"""
bucketvision

Many hands make light work!
A multi-threaded vision pipeline example for Bit Buckets Robotics that
looks like a bucket brigade

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

import time

# import our classes

from framerate import FrameRate
from bucketcapture import BucketCapture  # Camera capture threads... may rename this
from bucketprocessor import BucketProcessor  # Image processing threads... has same basic structure (may merge classes)
from faces import Faces  # Useful for basic testing of driverCam/Processor pipeline


bucketCam = BucketCapture(name="bucketCam", src=0, width=320, height=240, exposure=100).start()

print("Waiting for BucketCapture to start...")
while (bucketCam.isStopped() == True):
    time.sleep(0.001)

print("BucketCapture appears online!")


bucketProcessor = BucketProcessor(bucketCam, Faces()).start()

print("Waiting for BucketProcessor to start...")
while (bucketProcessor.isStopped() == True):
    time.sleep(0.001)

print("BucketProcessor appear online!")

fps = FrameRate()  


while (True):
    # grab the frame from the image processor
    (frame, count) = bucketProcessor.read()

    (camFps, _) = bucketCam.fps.get()
    (procFps, procUtil) = bucketProcessor.fps.get()
    (thisFps, thisUtil) = fps.get()

    cv2.putText(frame, "{:.1f}".format(camFps), (0, 40), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
    cv2.putText(frame, "{:.1f}".format(procFps) + " : {:.0f}".format(100 * procUtil) + "%", (0, 80), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
    cv2.putText(frame, "{:.1f}".format(thisFps), (0, 120), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)

    fps.start()
    cv2.imshow("bucketCam", frame)
    fps.stop()

    key = cv2.waitKey(1) & 0xFF
     
    if (bucketCam.processUserCommand(key) == True):
        break
        
# NOTE: NOTE: NOTE:
# Sometimes the exit gets messed up, but for now we just don't care

# stop the image processors
bucketProcessor.stop()

print("Waiting for BucketProcessor to stop...")
while (bucketProcessor.isStopped() == False):
    time.sleep(0.001)

# stop the camera capture
bucketCam.stop()

print("Waiting for BucketCapture to stop...")
while (bucketCam.isStopped() == False):
    time.sleep(0.001)
 
# do a bit of cleanup
cv2.destroyAllWindows()

print("Goodbye!")

