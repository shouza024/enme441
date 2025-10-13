import RPi.GPIO as GPIO
import time
import shifter
import random

GPIO.setmode(GPIO.BCM)

dataPin, latchPin, clockPin = 23, 24, 25
y = shifter(dataPin,latchPin,clockPin)

pattern = 0b01111110        # 8-bit pattern to display on LED bar

start_pos=random.randint(0,7)#Choose a random starting positiong
pattern =[0]*8               #Initiate empty pattern

pattern[start_pos] = 1

def x(pattern):
   for pos,val in enumerate(pattern):
       if val == 1:
           return pos
           
def update(new_pos):
    pattern = [0]*8
    pattern[new_pos] = 1
    
try:  
  y.shift_byte(pattern)
  x(pattern)
  if x == 7:
      new_pos = 6
  elif x == 0:
      new_pos =1
  else:
      new_pos = x + random.choice([-1,1])
                                  
  update(new_pos)
  time.sleep(0.05)
                                  
  while 1: pass
except KeyboardInterrupt:
  GPIO.cleanup()
