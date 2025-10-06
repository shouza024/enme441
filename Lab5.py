import time
import RPi.GPIO as GPIO #importing gpio library
import math

GPIO.setmode(GPIO.BCM)

pins = [17] #insert pin numbers once assigned.
base_frequency = 0.2 # frequency in hz
pwm_frequency = 500 #hz

for pin in pins:
    GPIO.setup(pin, GPIO.OUT)

pwm = GPIO.PWM(pins,f)
duty_cycle = ((sin(2*pi()*base_frequency*time.time()))**2)*100

