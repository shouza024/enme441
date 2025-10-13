import RPi.GPIO as GPIO
import time
import shifter
import random

GPIO.setmode(GPIO.BCM)

dataPin, latchPin, clockPin = 23, 24, 25
y = shifter.shifter(dataPin,latchPin,clockPin)

pattern = 0b01111110        # 8-bit pattern to display on LED bar

start_pos=random.randint(0,7)#Choose a random starting positiong
pattern = 0b00000000               #Initiate empty pattern

pattern = (1 << start_pos)

def x(pattern):
   for pos in range(8):
       if pattern & (1 << pos)
           return pos
           
def update(new_pos):
    global pattern 
    pattern = 0b00000000
    pattern =(1<<new_pos) 
    
try:                             
  while 1:
      y.shift_byte(pattern)
      pos = x(pattern)
      if pos == 7:
          new_pos = 6
      elif pos == 0:
          new_pos =1
      else:
          new_pos = pos + random.choice([-1,1])
                                  
  update(new_pos)
  time.sleep(0.05)
       
except KeyboardInterrupt:
  GPIO.cleanup()
