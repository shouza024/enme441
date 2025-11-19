import multiprocessing
import time
import RPi.GPIO as GPIO
import requests
import json
import socket
from stepper_class import Stepper
import threading
from shifter import Shifter

#-------------------Global Variables---------------------------
turret=[]             #list
globe=[]              #list
azimuth_input=0       #rad 
altitude_input=0      #rad
run_signal=0          #boolean      
stop_signal=0         #boolean      

#------------------Global Objects--------------------------------
s = Shifter(data=16,latch=20,clock=21)   
lock = multiprocessing.Lock()

# Instantiate 2 Steppers:
m2 = Stepper(s, lock)   #will control azimuth
m1 = Stepper(s, lock)   #will control altitude

#------------------Server running with json file------------------------------
'''
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
    server.bind(("10.112.150.68", 4084))   
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
'''


#-------------------Parsing Json-------------------------------
url = "http://192.168.1.254:8000/positions.json" #INSERT URL WHEN RELEASED

def parse_json():
    
    response = requests.get(url)
    response.raise_for_status() 
    data = response.json()
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
    global turret, globe, parse_json
    parse_json()
    print(turret)
    print(globe)




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
        conn,(client_ip,client_port) = s.accept()
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


s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.bind(('',8084))
s.listen(3)

web_page_thread = threading.Thread(target=server_web_page)
web_page_thread.daemon = True
'''
server_thread = threading.Thread(target=run_server)
server_thread.daemon = True
server_thread.start()
'''
web_page_thread.start()

time.sleep(1)



try:
    while True:
        time.sleep(10)      #some wait

    
except KeyboardInterrupt:
    print("Could not fetch JSON FILE")
 
