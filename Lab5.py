import time
import RPi.GPIO as GPIO #importing gpio library
import math

GPIO.setmode(GPIO.BCM)

pins = [21] #insert pin numbers once assigned.
base_frequency = 0.2 # frequency in hz
pwm_frequency = 500 #hz

for pin in pins:
    GPIO.setup(pin, GPIO.OUT)
    print(f'Pin{pin} setup for ouput')

pwm = GPIO.PWM(pins[0],pwm_frequency)
try:
    duty_cycle = ((sin(2*pi()*base_frequency*time.time()))**2)*100
    pwm.start(duty_cycle)
    while True:
        pass
except KeyboardInterrupt:
    print('\nExiting')

pwm.stop()
pwm.cleanup()
   



