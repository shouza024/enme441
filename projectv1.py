import multiprocessing
import time
#import RPi.GPIO as GPIO
#import requests
import json
import socket

#-------------------Global Variables---------------------------
turret=[]
globe=[]

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






try:
    parse_json()

except KeyboardInterrupt:
    print("Could not fetch JSON FILE")