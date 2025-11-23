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
turret=[]             #list
globe=[]              #list
azimuth_input=0       #rad 
altitude_input=0      #rad
run_signal=0          #boolean      
stop_signal=0         #boolean   
r_position=0          #cm robot radius position   
theta_position =0     #def

#------------------Global Objects--------------------------------
s = Shifter(data=16,latch=20,clock=21)   
lock = multiprocessing.Lock()

# Instantiate 2 Steppers:
m2 = Stepper(s, lock)   #will control azimuth
m1 = Stepper(s, lock)   #will control altitude

#------------------Server running with json file------------------------------
data ={
 "turrets": {
 "1": {"r": 300.0, "theta": 2.580 },
 "2": {"r": 300.0, "theta": 0.661 },
 "3": {"r": 300.0, "theta": 5.152 }
 },
 "globes": [
 { "r": 300.0, "theta": 1.015, "z": 20.4 },
 { "r": 300.0, "theta": 4.512, "z": 32.0 },
 { "r": 300.0, "theta": 3.979, "z": 10.8 },
 { "r": 300.0, "theta": 7.918, "z": 14.5}
 ]
}

json_data = json.dumps(data)
def run_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("", 4084))   
    server.listen(1)

    print("waiting for connection json server")

    conn, addr = server.accept()
    print("client connected from", addr)

    # Send the JSON to the client
    response = "HTTP/1.1 200 OK\r\n" \
               "Content-Type: application/json\r\n" \
               "Content-Length: {}\r\n" \
               "Connection: close\r\n\r\n{}".format(len(json_data), json_data)  
    conn.sendall(response.encode("utf-8"))

    conn.close()
    server.close()

def angle_diff(target_rad, current_rad):
    diff = (target_rad - current_rad + math.pi) % (2 * math.pi) - math.pi
    return diff

def turret_altitude(target_coord,turret_coord):
    """
    turret, target: [r, theta, z] in radians and same radius
    Returns signed pitch rotation (rad) to aim at target
    """
    r_t, theta_t, z_t = turret_coord
    r_p, theta_p, z_p = target_coord
    
    # horizontal distance
    delta_theta = angle_diff(theta_p, theta_t)
    dh = 2 * r_t * math.sin(delta_theta / 2)
    
    # vertical difference
    dz = z_p - z_t
    
    # signed pitch angle
    altitude = math.atan2(dz, dh)
    return (altitude)

def go_next(self,target_coordinates,turret_coordinates):
        #target_coordinates - list contain [radians, theta, zeta]
        #turret_coordinates - list contains [radians, theta, zeta] zeta might be decide by our cad model, when we get around to that
        angle_delta =angle_diff(target_coordinates[1],turret_coordinates[1])
        turret_azimuth_angle =(angle_delta-math.pi)/2
        turret_altitude_angle=turret_altitude(target_coordinates,turret_coordinates)
        return [turret_azimuth_angle,turret_altitude_angle]

#-------------------Parsing Json-------------------------------
url = "http://onepi.local:4084" #INSERT URL WHEN RELEASED "http://10.112.150.68:4084"
    #"http://192.168.1.254:8000/positions.json"
def parse_json():
    
    response = requests.get(url)
    response.raise_for_status() 
    data = response.json()#utf8
    print("json filed parsed and copied")
    '''
    #This code parse the example.json file, only use while in testing
    with open("example.json", "r") as file:
        data = json.load(file)
    '''
    global turret, globe
    turret = [[id['r'],id['theta']] for id in data['turrets'].values()]
    globe  = [[i['r'],i['theta'],i['z']] for i in data['globes']]

    #turret[id][r,theta] 
    #globe[id][r,theta,z] How to find any values from the json file
    #print(turret[1][1]) #Print turret radius of turret id 1.

#-----------------Control function Base on the data_dict read into Pi-----------------------------
def update(data_dict): # updates global variable base on what is found in the data_dict
    global run_signal, stop_signal,azimuth_input, altitude_input
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
      
def initiate():         #This function will parse the json file initate calculating route, and then perform 
    print("initiate run") 
    #Code that finds path
    global turret, globe, parse_json,r_position,theta_position
    parse_json()
    print("Turret list")
    print(turret)
    print("Globe list")
    print(globe)
    n=1                         #assuming that n is our turret position
    r_position = turret[n][0]
    theta_position=turret[n][1] #assuming that n is id the turrent corresponding to our location, dont know yet how we are getting this value
    z_position = 3              #centimeters of the ground, not sure what this is until cad is fleshed out

    #-----------------Sort order of globe to aim--------------------------
    sort_globe = sorted(globe, key=lambda g: g[1])    #Sorted the globe list from highest to lowest globe
    sort_turret= sorted(turret, key=lambda t: t[1])
    globe_target_sequence=[]
    #need to find best direction to sweep, which globe is closer the one on its left or right?
    for i in sort_globe:
        if 360 > angle_diff(sort_globe[i][1],theta_position): 
            id_closet_globe = i
            g=abs(theta_position-sort_globe[i][1])
                                                   
    if g < 360-g:
        sweep_direction = 1 #CW
        globe_target_sequence = sort_globe[id_closet_globe:] + sort_globe[:id_closet_globe]
        sort_turret_inv = sort_turret[::-1]
        last_globe=globe_target_sequence[-1]      #variable holds position of the final globe in aim sequence 
        starting_id_turret=min(range(len(sort_turret_inv)),key=lambda i:abs(sort_turret_inv[i][1]-last_globe[1]))
        turret_target_sequence =sort_turret_inv[starting_id_turret:]+sort_turret_inv[:starting_id_turret]
    elif g> 360-g:
        sweep_direction=-1 #CCW    #might need to flip these direction, depends on stepper mottor class
        sort_globe_inv=sort_globe[::-1] #Inverse sort globe list to now be from high to low
        globe_target_sequence = sort_globe[id_closet_globe:] + sort_globe[:id_closet_globe]
        last_globe=globe_target_sequence[-1]
        starting_id_turret=min(range(len(sort_turret)),key=lambda i:abs(sort_turret[i][1]-last_globe[1]))
        turret_target_sequence =sort_turret_inv[starting_id_turret:]+sort_turret_inv[:starting_id_turret]
    #This block of code above is kinda confusing but all it does is output two important list:
    #turret_target_sequence - sequence to aim for turrets
    #globe_target_sequence - sequence for globe, both sequence will be completed by sweeping in one direction initially,
    #but then will sweep the other direction to hit the turrets along the way back.

    #------------------------Code that moves the turret along the two sequence above-----------------------------------
    #First we will follow the globe sequence, assuming that the turret is setup to aim at the zero, we will move in that sequence
    for i in globe_target_sequence:
        turret_azimuth_angle,turret_altitude_angle=go_next(globe_target_sequence[i],[r_position,theta_position,z_position])
        p1= m1.goAngle(turret_azimuth_angle)
        p2= m2.goAngle(turret_altitude_angle)
        p1.join()
        p2.join()

    for z in turret_target_sequence:
        if theta_position==turret_target_sequence[z][1]:  #Skips the turret position corresponding to our turret
          continue
        turret_azimuth_angle,turret_altitude_angle=go_next(turret_target_sequence[z],[r_position,theta_position,z_position])
        p1= m1.goAngle(turret_azimuth_angle)
        p2= m2.goAngle(turret_altitude_angle)
        p1.join()
        p2.join()
    

def stopping():         #Stops any motion, honestly not sure how do this yet? Is this required?
    print('stop')
    

def set_zero(azimuth,altitude):
    print('moving to new desire zero')
    global m1,m2
    p2 = m2.goAngle(azimuth)
    p1 = m1.goAngle(altitude)
    p1.join()
    print(f'moving m1 to {altitude}')
    print(f"moving m2 to {azimuth}")
    p2.join()
    m1.zero()
    m2.zero()



#-----------------HTML Setup-----------------------------------
##web page function-setups the page window for user to submit desired brightness level input
def web_page():
    html = """
    <!DOCTYPE html>
<html>
<head>
  <title>Laser Turret Calibration</title>

  <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');

    body {
      margin: 0;
      padding: 0;
      height: 100vh;
      display: flex;
      justify-content: center;
      align-items: center;
      background: #050510;
      font-family: 'Orbitron', sans-serif;
      color: #00eaff;
      background-image: 
        linear-gradient(rgba(0, 255, 255, 0.05) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 255, 255, 0.05) 1px, transparent 1px);
      background-size: 30px 30px;
    }

    .calibration-card {
      background: rgba(0, 30, 50, 0.35);
      border: 1px solid #00eaff;
      border-radius: 18px;
      padding: 35px 45px;
      box-shadow: 0 0 20px rgba(0, 255, 255, 0.4);
      width: 420px;
      backdrop-filter: blur(10px);
      animation: fadeIn 1s ease-out;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(30px); }
      to   { opacity: 1; transform: translateY(0); }
    }

    h2 {
      text-align: center;
      margin-bottom: 25px;
      font-size: 26px;
      letter-spacing: 3px;
      color: #7fedff;
      text-shadow: 0 0 8px #00eaff;
    }

    label {
      font-size: 16px;
      text-shadow: 0 0 5px #00eaff;
    }

    .input-row {
      margin-bottom: 22px;
      display: flex;
      flex-direction: column;
    }

    input[type="text"] {
      width: 100%;
      padding: 12px;
      margin-top: 8px;
      border-radius: 10px;
      border: 1px solid #00b3cc;
      background: rgba(0, 0, 20, 0.6);
      color: #a7faff;
      font-size: 18px;
      outline: none;
      transition: 0.3s;
      box-shadow: inset 0 0 10px rgba(0, 255, 255, 0.2);
    }

    input[type="text"]:focus {
      border-color: #00eaff;
      box-shadow: 0 0 12px rgba(0, 255, 255, 0.6);
    }

    .error {
      font-size: 13px;
      color: #ff6b6b;
      margin-top: 5px;
      min-height: 16px;
      text-shadow: 0 0 5px #ff3b3b;
    }

    button {
      width: 100%;
      padding: 15px;
      font-size: 18px;
      border: none;
      border-radius: 12px;
      cursor: pointer;
      margin-top: 10px;
      background: linear-gradient(135deg, #0047ff, #00eaff);
      color: white;
      font-weight: bold;
      letter-spacing: 2px;
      box-shadow: 0 0 15px rgba(0, 160, 255, 0.7);
      transition: 0.25s;
    }

    button:hover {
      transform: scale(1.06);
      box-shadow: 0 0 25px rgba(0, 220, 255, 1);
    }

    button:disabled {
      opacity: 0.4;
      cursor: not-allowed;
      box-shadow: none;
    }
  </style>

</head>

<body>

  <div class="calibration-card">
    <h2>LASER TURRET CALIBRATION</h2>

    <!-- MAIN CALIBRATION FORM -->
    <form id="calibrationForm" action="/set_zero.php" method="POST">
      
      <div class="input-row">
        <label for="altitude">Altitude Angle:</label>
        <input type="text" id="altitude" name="altitude" placeholder="Enter altitude offset">
        <div id="altitudeError" class="error"></div>
      </div>

      <div class="input-row">
        <label for="azimuth">Azimuth Angle:</label>
        <input type="text" id="azimuth" name="azimuth" placeholder="Enter azimuth offset">
        <div id="azimuthError" class="error"></div>
      </div>

      <button id="submitBtn" type="submit">SET ZERO POSITION</button>

    </form>

    <!-- NEW FORM FOR RUN + STOP -->
    <form action="/turret_control.php" method="POST">

      <input type="hidden" id="run_signal" name="run_signal" value="false">
      <input type="hidden" id="stop_signal" name="stop_signal" value="false">

      <button type="submit" onclick="
        document.getElementById('run_signal').value='true';
        document.getElementById('stop_signal').value='false';
      ">
        INITIATE RUN
      </button>

      <button type="submit" onclick="
        document.getElementById('stop_signal').value='true';
        document.getElementById('run_signal').value='false';
      ">
        EMERGENCY STOP
      </button>

    </form>
  </div>


  <script>
    const altitudeInput = document.getElementById("altitude");
    const azimuthInput = document.getElementById("azimuth");
    const altitudeError = document.getElementById("altitudeError");
    const azimuthError = document.getElementById("azimuthError");
    const submitBtn = document.getElementById("submitBtn");

    function validateAngle(value) {
      if (value === "") return "Field cannot be empty.";
      if (isNaN(value)) return "Angle must be a number.";
      const num = Number(value);
      if (num < -180 || num > 180) return "Angle must be between -180° and 180°.";
      return "";
    }

    function validateForm() {
      const altErr = validateAngle(altitudeInput.value);
      const aziErr = validateAngle(azimuthInput.value);

      altitudeError.textContent = altErr;
      azimuthError.textContent = aziErr;

      submitBtn.disabled = altErr || aziErr;
    }

    altitudeInput.addEventListener("input", validateForm);
    azimuthInput.addEventListener("input", validateForm);
  </script>

</body>
</html>

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
        time.sleep(0.5)
        print('waiting on connection html')
        conn,(client_ip,client_port) = d.accept()
        message = conn.recv(1024).decode('utf-8')              
        print(f'Message from {client_ip}')   
        data_dict = parsePOSTdata(message)
        if data_dict: #Skips the first GET, and only runs the code after pressing the set zero on the user end
            update(data_dict)
            print('pi updating base on ur input')
        conn.send(b'HTTP/1.1 200 OK\r\n')          
        conn.send(b'Content-type: text/html\r\n') 
        conn.send(b'Connection: close\r\n\r\n') 
        try:
            conn.sendall(web_page())
        finally:
            conn.close()


#------------------------Socket Setup----------------------------


d = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
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
        time.sleep(10)      #some wait

    
except KeyboardInterrupt:
    print("Could not fetch JSON FILE")
 
