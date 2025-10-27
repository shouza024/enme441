## This is lab 7 code

import socket
import RPi.GPIO as GPIO
import time
import threading

GPIO.setmode(GPIO.BCM)

## Pins labels for LED 1,2,3
leds = [17, 27, 22]
for led in leds: GPIO.setup(led,GPIO.OUT)

##Initiate LEDs at x brightness level
initial_brightness = 20  #User Input
pwm=[]                  #a list storing pwm object for the three leds
brightness = [0,0,0]         #a list storing brigthenss level
for i,led in enumerate(leds,start=0):      #loops assign initial values for both list above
    p = GPIO.PWM(led,100)
    p.start(initial_brightness)
    pwm.append(p)
    brightness[i] = initial_brightness


##web page function-setups the page window for user to submit desired brightness level input
def web_page(led_brightness):
    html = """
    <html>
    <body>
    <h2>Lab 7 Question 1</h2>
    <h3> Brightness Level:<h3>
    <form action="/cgi-bin/range.py" method="POST">
    <input type="range" name="brightness" min ="0" max="100"
    	value ="0"/><br>
    <p>Select LED:<br>
    <input type="radio" name="led" value="0"> LED 1 ("""+bin(brightness[0])+"""%)<br>
    <input type="radio" name="led" value="1"> LED 2 ("""+bin(brightness[1])+"""%)<br>
    <input type="radio" name="led" value="2"> LED 3 ("""+bin(brightness[2])+"""%) <br>
    <input type="submit" value="Change Brightness">
    </form> 
    </body>
    </html>
    """
    return bytes(html,'utf-8')
#d
def parsePOSTdata(data):        ##helper function from class
    data_dict = {}
    idx = data.find('\r\n\r\n')+4
    data = data[idx:]
    data_pairs = data.split('&')
    for pair in data_pairs:
        key_val = pair.split('=')
        if len(key_val) == 2:
            data_dict[key_val[0]] = key_val[1]
    return data_dict

def update_brightness(data_dict):
    c = int(data_dict['led'])
    g = int(data_dict['brightness'])      
    brightness[c] = g              ## Reads the data dictionary and updates brigthness list 
    pwm[c].ChangeDutyCycle(g)      ## Changes PWM level to new value from data_dict

def server_web_page():         ##         
    while True:
        time.sleep(0.1)
        print('waiting on connection')
        conn,(client_ip,client_port) = s.accept()
        message = conn.recv(1024).decode('utf-8')              
        print(f'Message from {client_ip}')   
        data_dict = parsePOSTdata(message)
        #Maybe needs the if statement not sure tbh

        conn.send(b'HTTP/1.1 200 OK\r\n')          
        conn.send(b'Content-type: text/html\r\n') 
        conn.send(b'Connection: close\r\n\r\n') 
        try:
            conn.sendall(web_page(brightness))
        finally:
            conn.close()

        update_brightness(data_dict)    
        
#Setup up socket
s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.bind(('',80))
s.listen(2)

web_page_thread = threading.Thread(target=server_web_page)
web_page_thread.daemon = True
web_page_thread.start()

try:
    while True:
        pass
except:
    print('joining webpage')
    web_page_thread.join()
    print('close socket')
    s.close


  
















pwm.stop()
GPIO.cleanup()