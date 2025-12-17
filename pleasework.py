import multiprocessing
import time
import RPi.GPIO as GPIO
import requests
import json
import socket
from stepper_class import Stepper
import threading
from shifter import Shifter
import math

#-------------------Global Variables---------------------------
turret=[]             
globe=[]              
azimuth_input=0       
altitude_input=0      
run_signal=0          
stop_signal=0         
r_position=0          
theta_position =0     
laser_pin = 26
altitude_position = 0.0
GPIO.setmode(GPIO.BCM)
GPIO.setup(laser_pin, GPIO.OUT)
GPIO.output(laser_pin, GPIO.LOW)

#------------------Global Objects--------------------------------
s = Shifter(data=16,latch=20,clock=21)   
lock = multiprocessing.Lock()
m2 = Stepper(s, lock)   
m1 = Stepper(s, lock)   

#------------------Server running with json file------------------------------
data ={
  "turrets": {
    "1": {"r": 182.8, "theta": 5.25344104850293},
    "2": {"r": 182.8, "theta": 3.5081117965086},
    "3": {"r": 182.8, "theta": 1.91986217719376},
    "4": {"r": 182.8, "theta": 4.45058959258554},
    "5": {"r": 182.8, "theta": 0.436332312998582},
    "6": {"r": 182.8, "theta": 2.47836753783195},
    "7": {"r": 182.8, "theta": 1.62315620435473},
    "8": {"r": 182.8, "theta": 5.70722665402146},
    "9": {"r": 182.8, "theta": 4.1538836197465},
    "10": {"r": 182.8, "theta": 3.35103216382911},
    "11": {"r": 182.8, "theta": 4.71238898038469},
    "12": {"r": 182.8, "theta": 2.23402144255274},
    "13": {"r": 182.8, "theta": 2.96705972839036},
    "14": {"r": 182.8, "theta": 0.802851455917392},
    "15": {"r": 182.8, "theta": 1.23918376891597},
    "16": {"r": 182.8, "theta": 0.20943951023932},
    "17": {"r": 182.8, "theta": 4.88692190558412},
    "18": {"r": 182.8, "theta": 3.17649923862968},
    "19": {"r": 182.8, "theta": 3.99680398706701},
    "20": {"r": 182.8, "theta": 6.2482787221397},
    "21": {"r": 182.8, "theta": 2.80998009571087},
    "22": {"r": 182.8, "theta": 3.7873644768277}
  },
  "globes": [
    {"r": 182.8, "theta": 3.14, "z": 162.6},
    {"r": 182.8, "theta": 1.047, "z": 195.6}
  ]
}
json_data = json.dumps(data)

def run_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("10.115.189.68", 4084))
    server.listen(1)
    print("waiting for connection json server")
    conn, addr = server.accept()
    print("client connected from", addr)
    response = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}".format(len(json_data), json_data)  
    conn.sendall(response.encode("utf-8"))
    conn.close()
    server.close()

def angle_diff(target_rad, current_rad):
    diff = (target_rad - current_rad + math.pi) % (2 * math.pi) - math.pi
    return diff

def go_next(globe, turret):
    r_p, theta_p, z_p = globe
    r_t, theta_t, z_t = turret
    dtheta = angle_diff(theta_p, theta_t)
    delta_theta = abs(dtheta)
    dh = 2 * r_t * math.sin(delta_theta / 2)
    dz = z_p - z_t
    altitude = math.atan2(dz, dh)
    return dtheta, altitude

#-------------------Parsing Json-------------------------------
url = "http://10.115.189.68:4084"

def parse_json():
    global turret, globe, data
    response = requests.get(url)
    response.raise_for_status() 
    data = response.json()
    print("json filed parsed and copied")
    z_offset = 2
    turret = [[id['r'],id['theta'],z_offset] for id in data['turrets'].values()]
    globe  = [[i['r'],i['theta'],i['z']] for i in data['globes']]

#-----------------Control function Base on the data_dict read into Pi-----------------------------
def update(data_dict):
    global run_signal, stop_signal, azimuth_input, altitude_input
    if 'laser_on' in data_dict:
        print('Manual Laser ON')
        shoot_laser(3)
        return 
    if 'run_signal' in data_dict:
        run_signal = bool(data_dict['run_signal'])
        if run_signal==True:
            initiate()
    if 'stop_signal' in data_dict:
        stop_signal = bool(data_dict['stop_signal'])
        if run_signal==True:
            stopping()
    if 'azimuth' in data_dict:
        azimuth_input = float(data_dict['azimuth'])
        altitude_input= float(data_dict['altitude'])
        set_zero(azimuth_input,altitude_input)
 
def initiate():
    global turret, globe, r_position, theta_position, altitude_position, data
    print("Initiating turret run...")
    parse_json()
    MY_TURRET_ID = "20"
    my_turret = data['turrets'][MY_TURRET_ID]
    r_position = my_turret['r']
    theta_position = my_turret['theta']
    z_position = 3.0
    altitude_position = 0.0
    print(f"Turret 20 absolute θ = {theta_position:.3f} rad")
    p1 = m1.goAngle(0)
    p2 = m2.goAngle(0)
    p1.join()
    p2.join()
    print("Mechanical zero confirmed")
    theta_zero = theta_position
    print(f"Mechanical zero set at turret theta = {theta_zero:.3f} rad")
    globes_sorted = sorted(globe, key=lambda g: g[1])
    turrets_sorted = sorted(turret, key=lambda t: t[1])
    closest_globe_idx = min(range(len(globes_sorted)), key=lambda i: abs(angle_diff(globes_sorted[i][1], theta_zero)))
    direction = angle_diff(globes_sorted[closest_globe_idx][1], theta_zero)
    sweep_direction = 1 if direction > 0 else -1
    if sweep_direction == 1:
        globe_sequence = globes_sorted[closest_globe_idx:] + globes_sorted[:closest_globe_idx]
    else:
        rev = globes_sorted[::-1]
        idx = rev.index(globes_sorted[closest_globe_idx])
        globe_sequence = rev[idx:] + rev[:idx]
    last_globe_theta = globe_sequence[-1][1]
    if sweep_direction == 1:
        turret_order = turrets_sorted[::-1]
    else:
        turret_order = turrets_sorted
    start_idx = min(range(len(turret_order)), key=lambda i: abs(angle_diff(turret_order[i][1], last_globe_theta)))
    turret_sequence = turret_order[start_idx:] + turret_order[:start_idx]
    for i, g in enumerate(globe_sequence):
        azimuth, altitude = go_next([g[0], g[1], g[2]], [r_position, theta_position, z_position])
        print(f"\nAiming at globe #{i}")
        print(f"Current θ: {theta_position:.3f}")
        print(f"Target  θ: {g[1]:.3f}")
        print(f"Δθ: {azimuth:.3f}")
        p1 = m1.goAngle(math.degrees(azimuth))
        p2 = m2.goAngle(math.degrees(altitude))
        p1.join()
        p2.join()
        theta_position += azimuth
        altitude_position = altitude
        shoot_laser()
        time.sleep(5)
    for i, t in enumerate(turret_sequence):
        if abs(angle_diff(theta_position, t[1])) < 1e-3:
            continue
        azimuth_angle, altitude_angle = go_next([t[0], t[1], z_position], [r_position, theta_position, z_position])
        p1 = m1.goAngle(math.degrees(azimuth_angle))
        p2 = m2.goAngle(math.degrees(altitude_angle))
        p1.join()
        p2.join()
        theta_position += azimuth_angle
        altitude_position = altitude_angle
        print(f"Aiming for turret #{i} -> azimuth: {azimuth_angle:.3f} rad, altitude: {altitude_angle:.3f} rad")
        shoot_laser()
        time.sleep(5)

def stopping():
    print('stopping')

def set_zero(azimuth, altitude):
    print('moving to new desire zero')
    global m1, m2
    p2 = m2.goAngle(azimuth)
    p1 = m1.goAngle(altitude)
    p1.join()
    print(f'moving m1 to {altitude}')
    print(f"moving m2 to {azimuth}")
    p2.join()
    m1.zero()
    m2.zero()

def shoot_laser(duration = 3):
    print("LASER ON")
    GPIO.output(laser_pin, GPIO.HIGH)
    time.sleep(duration)
    GPIO.output(laser_pin, GPIO.LOW)
    print("LASER OFF")

def web_page():
    html = """<html><body><h2>Laser Turret Calibration</h2></body></html>"""
    return bytes(html,'utf-8')

def parsePOSTdata(data):
    data_dict = {}
    idx = data.find('\r\n\r\n')+4
    data = data[idx:]
    data_pairs = data.split('&')
    for pair in data_pairs:
        key_val = pair.split('=')
        if len(key_val) == 2:
            data_dict[key_val[0]] = key_val[1]
    return data_dict

def server_web_page():
    while True:
        time.sleep(0.5)
        print('waiting on connection html')
        conn,(client_ip,client_port) = d.accept()
        message = conn.recv(1024).decode('utf-8')              
        print(f'Message from {client_ip}')   
        data_dict = parsePOSTdata(message)
        if data_dict:
            update(data_dict)
            print('pi updating base on ur input')
        conn.send(b'HTTP/1.1 200 OK\r\nContent-type: text/html\r\nConnection: close\r\n\r\n') 
        try:
            conn.sendall(web_page())
        finally:
            conn.close()

d = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
d.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
d.bind(('',8084))
d.listen(3)

web_page_thread = threading.Thread(target=server_web_page)
web_page_thread.daemon = True

server_thread = threading.Thread(target=run_server)
server_thread.daemon = True
server_thread.start()
web_page_thread.start()
time.sleep(1)

try:
    while True:
        time.sleep(10)
except KeyboardInterrupt:
    d.close()
    GPIO.cleanup()
    print("Could not fetch JSON FILE")
