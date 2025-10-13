import RPi.GPIO as GPIO
import time
import shifter
import random

class Bug:

   def  __init__(self,__shifter,timestep = 0.1,x = 3,isWrapon = False):
       self.__shifter = __shifter
       self.x = x
       self.timestep = timestep
       self.isWrapon = isWrapon
       self.pattern = (1 << self.x)
      
   def finder(self):
       for pos in range(8):
           if self.pattern & (1 << pos):
               return pos
           
   def update(self,new_pos):
       self.pattern =(1<<new_pos)

   def start(self):
       self.run = True
       while self.run == True:
           self.__shifter.shift_byte(self.pattern)
           pos = self.finder()
           if self.isWrapon == False:
               if pos == 7:
                   new_pos = 6
               elif pos == 0:
                   new_pos =1
           else:
               new_pos = pos + random.choice([-1,1])
               if new_pos == 8:
                   new_pos = 1
               elif new_pos ==0:
                   new_pos  = 7
           self.update(new_pos)
           time.sleep(self.timestep)

    def stop(self):
        self.run = False

GPIO.setmode(GPIO.BCM)

dataPin, latchPin, clockPin = 23, 24, 25
y = shifter.shifter(dataPin,latchPin,clockPin)
bug = Bug(y,0.05,1,True)

try:                             
  bug.start()
except KeyboardInterrupt:
  bug.stop()
  GPIO.cleanup()
