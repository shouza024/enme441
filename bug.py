import RPi.GPIO as GPIO
import time
import shifter
import random
import bug1 as Bug
          

GPIO.setmode(GPIO.BCM)

dataPin, latchPin, clockPin = 23, 24, 25
y = shifter.shifter(dataPin,latchPin,clockPin)
bug = Bug(y,0.05,1,True)

try:                             
  bug.start()
except KeyboardInterrupt:
  bug.stop()
  GPIO.cleanup()
