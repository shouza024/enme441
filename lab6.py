import RPi.GPIO as GPIO
import time

class Shifter:
    def __init__(self,serial_pin,latch_pin,clock_pin):
        self.serial = serial_pin
        self.clock = clock_pin
        self.latch = latch_pin

    def start():  
        GPIO.setup(serial_pin, GPIO.OUT)
        GPIO.setup(latch_pin, GPIO.OUT, initial=0)  
        GPIO.setup(clock_pin, GPIO.OUT, initial=0)

    def __ping(p):
        GPIO.output(p,1)
        time.sleep(0)
        GPIO.output(p,0)
      
    def shift_byte(b): 
        for i in range(8):
            GPIO.output(dataPin, b & (1<<i))
            ping(clockPin) 
        ping(latchPin) 

GPIO.setmode(GPIO.BCM)

dataPin, latchPin, clockPin = 23, 24, 25
x = Shifter(dataPin,latchPin,clockPin)
x.start

pattern = 0b01100110        # 8-bit pattern to display on LED bar

try:
  x.shift_byte(pattern)
  while 1: pass
except:
  GPIO.cleanup()
