
import RPi.GPIO as GPIO
import time
import math

GPIO.setmode(GPIO.BCM)
pins = [2,3,4,17,27,22,14,15,18,23]

f = .2
phi = math.pi/11
B = [0] *10
duty  = [0] *10
led = []
direction = 1 #forward -1 for reverse 
button_pin= 24 

GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def button_pressed_callback(pin):
    global direction
    direction *= -1  # flip the direction
    print(f"Direction changed! Now direction = {direction}")

for p in pins:
    GPIO.setup(p,GPIO.OUT)
    pwm = GPIO.PWM(p,500)
    pwm.start(0) #makes the pwm start at 0
    led.append(pwm)


GPIO.add_event_detect(button_pin, GPIO.RISING,  callback=button_pressed_callback, bouncetime=200)

try:
    while True:
        t = time.time()
        for i in range (10): 
           B[i]  = (math.sin((2*(math.pi)*f*t - direction* phi*i)))**2
           duty [i] = 100 * B[i]
           led[i].ChangeDutyCycle(duty[i])
except KeyboardInterrupt:
    for l in led:
       l.stop()
GPIO.cleanup()
