import RPi.GPIO as GPIO
import time
import shifter
import random
import bugi as Bug
          

GPIO.setmode(GPIO.BCM)

dataPin, latchPin, clockPin = 23, 24, 25
s1,s2,s3 = 5, 6, 13

GPIO.setup(s1,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(s2,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(s3,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

y = shifter.shifter(dataPin,latchPin,clockPin)
bug = Bug.Bug(y)

def s2_call(s2):
    bug.isWrapon = not bug.isWrapon

def s3_call_rise(s3):
    bug.timestep = bug.timestep/3

def s3_call_fall(s3):
    bug.timestep = bug.timestep*3

GPIO.add_event_detect(s2,GPIO.RISING,callback=s2_call,bouncetime=1000)
GPIO.add_event_detect(s3,GPIO.RISING,callback=s3_call_rise,bouncetime=1000)
GPIO.add_event_detect(s3,GPIO.FALLING,callback=s3_call_fall,bouncetime=1000)

try:
    while s1 = True:
        bug.start()
    else:
        bug.stop()
except KeyboardInterrupt:
  bug.stop()
  GPIO.cleanup()
