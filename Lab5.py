import time
import RPi.GPIO as GPIO #importing gpio library
import math as m

GPIO.setmode(GPIO.BCM)

#Button Port
button = 11
GPIO.setup(button,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
direction = 1

def button_call(button):
    global direction 
    direction = direction*-1  #Swap wave direction

GPIO.add_event_detect(button,GPIO.RISING,callback=button_call,bouncetime=100)

#LED initation
pins = [21,20,16,12,7,5,6,13,19,26] #insert pin numbers once assigned.
base_frequency = 0.2 # frequency in hz
pwm_frequency = 500 #hz
pwm = []            #Creating a list of pwm objects

#LED- PWM Initation
for i,pin in enumerate(pins):
    GPIO.setup(pin, GPIO.OUT)
    print(f'Pin{pin} setup for ouput')
    p = GPIO.PWM(pin,pwm_frequency)
    p.start(((m.sin(-i*m.pi/11))**2)*100)
    pwm.append(p)

#LED- changing brightness
try:
    while 1:
        for j,p in enumerate(pwm[::direction]):
            t = time.time()
            duty_cycle = ((m.sin(2*m.pi*base_frequency*t - j*m.pi/11))**2)*100
            p.ChangeDutyCycle(duty_cycle)
        pass
except KeyboardInterrupt:
    print('\nExiting')

for p in pwm:
    p.stop()
GPIO.cleanup()
   












