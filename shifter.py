import RPi.GPIO as GPIO
import time

class shifter:
    def __init__(self,serial_pin,latch_pin,clock_pin):
        self.serial = serial_pin
        self.clock = clock_pin
        self.latch = latch_pin
        self.start()

    def start(self):  
        GPIO.setup(self.serial, GPIO.OUT)
        GPIO.setup(self.latch, GPIO.OUT, initial=0)  
        GPIO.setup(self.clock, GPIO.OUT, initial=0)

    def __ping(self,p):
        GPIO.output(p,1)
        time.sleep(0)
        GPIO.output(p,0)
      
    def shift_byte(self,b): 
        for i in range(8):
            GPIO.output(serial_pin, b & (1<<i))
            self.__ping(clock_pin) 
        self.__ping(latch_pin) 
