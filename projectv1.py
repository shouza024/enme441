import multiprocessing
import time
#import RPi.GPIO as GPIO
#import requests
import json
import socket
import stepper_class

#-------------------Global Variables---------------------------
turret=[]   #list
globe=[]    #list
azmith=0    #deg
altitude=0  #deg

#-------------------Parsing Json-------------------------------
url = "" #INSERT URL WHEN RELEASED

def parse_json():
    ''' This code is for parsing the url, currently we dont have url so will be commented out until we get that
    response = requests.get(url)
    response.raise_for_status() 
    data = response.json()
    '''
    #This code parse the example.json file, only use while in testing
    with open("example.json", "r") as file:
        data = json.load(file)


    turret = [[id['r'],id['theta']] for id in data['turrets'].values()]
    globe  = [[i['r'],i['theta'],i['z']] for i in data['globes']]

    #turret[id][r,theta]
    #globe[id][r,theta,z] How to any values from the json file



#-----------------HTML Setup-----------------------------------
##web page function-setups the page window for user to submit desired brightness level input
def web_page(led_brightness):
    html = """
    Insert html here
    """
    return bytes(html,'utf-8')


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

def server_web_page():         ##         
    while True:
        time.sleep(0.1)
        print('waiting on connection')
        conn,(client_ip,client_port) = s.accept()
        message = conn.recv(1024).decode('utf-8')              
        print(f'Message from {client_ip}')   
        data_dict = parsePOSTdata(message)
        if 'word in html' in data_dict and 'a word from html' in data_dict: #Skips the first GET, and only runs the code updating golbal variables
            #updating code
            print("Not ready yet")
        conn.send(b'HTTP/1.1 200 OK\r\n')          
        conn.send(b'Content-type: text/html\r\n') 
        conn.send(b'Connection: close\r\n\r\n') 
        try:
            conn.sendall(web_page(brightness))
        finally:
            conn.close()


#------------------------Socket Setup----------------------------
s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.bind(('',80))
s.listen(2)

web_page_thread = threading.Thread(target=server_web_page)
web_page_thread.daemon = True
web_page_thread.start()
parse_json()

try:
    while True:
        print()
    
except KeyboardInterrupt:
    print("Could not fetch JSON FILE")