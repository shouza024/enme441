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
laser_pin = 26
altitude_position = 0.0
GPIO.setmode(GPIO.BCM)
GPIO.setup(laser_pin, GPIO.OUT)
GPIO.output(laser_pin, GPIO.LOW)

#------------------Global Objects--------------------------------
s = Shifter(data=16,latch=20,clock=21)   
lock = multiprocessing.Lock()

# Instantiate 2 Steppers:
m2 = Stepper(s, lock)   #will control azimuth
m1 = Stepper(s, lock)   #will control altitude

#------------------Server running with json file------------------------------

data ={
  "turrets": {
    "1": {
      "r": 182.8,
      "theta": 5.25344104850293
    },
    "2": {
      "r": 182.8,
      "theta": 3.5081117965086
    },
    "3": {
      "r": 182.8,
      "theta": 1.91986217719376
    },
    "4": {
      "r": 182.8,
      "theta": 4.45058959258554
    },
    "5": {
      "r": 182.8,
      "theta": 0.436332312998582
    },
    "6": {
      "r": 182.8,
      "theta": 2.47836753783195
    },
    "7": {
      "r": 182.8,
      "theta": 1.62315620435473
    },
    "8": {
      "r": 182.8,
      "theta": 5.70722665402146
    },
    "9": {
      "r": 182.8,
      "theta": 4.1538836197465
    },
    "10": {
      "r": 182.8,
      "theta": 3.35103216382911
    },
    "11": {
      "r": 182.8,
      "theta": 4.71238898038469
    },
    "12": {
      "r": 182.8,
      "theta": 2.23402144255274
    },
    "13": {
      "r": 182.8,
      "theta": 2.96705972839036
    },
    "14": {
      "r": 182.8,
      "theta": 0.802851455917392
    },
    "15": {
      "r": 182.8,
      "theta": 1.23918376891597
    },
    "16": {
      "r": 182.8,
      "theta": 0.20943951023932
    },
    "17": {
      "r": 182.8,
      "theta": 4.88692190558412
    },
    "18": {
      "r": 182.8,
      "theta": 3.17649923862968
    },
    "19": {
      "r": 182.8,
      "theta": 3.99680398706701
    },
    "20": {
      "r": 182.8,
      "theta": 6.2482787221397
    },
    "21": {
      "r": 182.8,
      "theta": 2.80998009571087
    },
    "22": {
      "r": 182.8,
      "theta": 3.7873644768277
    }
  },
  "globes": [
    {
      "r": 182.8,
      "theta": 3.14,
      "z": 162.6
    },
    {
      "r": 182.8,
      "theta": 1.047,
      "z": 195.6
    }
  ]
}

json_data = json.dumps(data)
def run_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.1.1", 4084))   ##10.115.189.68 Erick Ip   ## 127.0.1.1 Zach Ip address
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


def go_next(target_coordinates,turret_coordinates):
    """
    Fixed version with edge case handling.
    """
    r_t, theta_t, z_t = turret_coordinates
    r_p, theta_p, z_p = target_coordinates
    
    # Angular difference
    dtheta = angle_diff(theta_p, theta_t)
    
    # Special case: target very close to us
    if abs(dtheta) < 0.001:  # ~0.057°
        # Target is essentially at our position
        # We could aim slightly to the side or skip
        return [0, 0]
    
    # Special case: target almost opposite (Δθ ≈ π)
    if abs(abs(dtheta) - math.pi) < 0.001:
        # Target opposite us, aim 90° from inward
        azimuth = math.pi/2
        azimuth *= 1 if dtheta >= 0 else -1
    else:
        # General case: (π - |Δθ|)/2
        azimuth = (math.pi - abs(dtheta)) / 2
        azimuth *= 1 if dtheta >= 0 else -1
    
    # Altitude
    chord_length = 2 * r_t * math.sin(abs(dtheta) / 2)
    dz = z_p - z_t
    
    altitude = math.atan2(dz, chord_length)
    
    return [azimuth, altitude]
def aim_at_center(turret_coordinates):
    """
    Calculate angles to aim at center when zero already points to center.
    This should return [0, something] since we're already pointing at center!
    """
    r_t, theta_t, z_t = turret_coordinates
    
    # If azimuth=0 points to center, then to aim at center:
    azimuth = 0.0
    
    # Altitude depends on height difference
    # Assuming center is at z=0
    altitude = math.atan2(-z_t, r_t)  # Negative because center is lower if we're above it
    
    return [azimuth, altitude]
#-------------------Parsing Json-------------------------------
url = "http://127.0.1.1:4084" #INSERT URL WHEN RELEASED "http://10.112.150.68:4084"
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
    z_offset =2
    turret = [[id['r'],id['theta'],z_offset] for id in data['turrets'].values()]
    globe  = [[i['r'],i['theta'],i['z']] for i in data['globes']]
    

    #turret[id][r,theta] 
    #globe[id][r,theta,z] How to find any values from the json file
    #print(turret[1][1]) #Print turret radius of turret id 1.

#-----------------Control function Base on the data_dict read into Pi-----------------------------
def update(data_dict): # updates global variable base on what is found in the data_dict
    global run_signal, stop_signal,azimuth_input, altitude_input

    # Manual Laser 
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
    """FAST version - no return to center between targets"""
    print("FAST initiate run")
    
    # Fetch data
    response = requests.get(url)
    current_data = response.json()
    
    # Your position
    my_turret_id = "20"
    r_position = current_data['turrets'][my_turret_id]['r']
    theta_position = current_data['turrets'][my_turret_id]['theta']
    z_position = 0
    
    # Collect all targets
    all_targets = []
    
    # Globes
    for g in current_data['globes']:
        all_targets.append([g['r'], g['theta'], g['z']])
    
    # Other turrets
    for tid, tdata in current_data['turrets'].items():
        if tid != my_turret_id:
            all_targets.append([tdata['r'], tdata['theta'], z_position])
    
    # Create optimal sequence
    sequence = create_optimal_sequence(theta_position, all_targets)
    
    print(f"Found {len(sequence)} targets")
    
    # Start from current position (assume we're at center)
    current_azimuth = 0.0  # Currently aiming at center
    current_altitude = math.atan2(-z_position, r_position)  # Angle to center
    
    # Move to first target from center
    if sequence:
        print("\nMoving to first target...")
        target = sequence[0]
        azimuth, altitude = go_next(target, [r_position, theta_position, z_position])
        
        # Convert to absolute motor positions
        abs_azimuth = azimuth * 180 / math.pi
        abs_altitude = altitude * 180 / math.pi
        
        p1 = m1.goAngle(abs_azimuth)
        p2 = m2.goAngle(abs_altitude)
        p1.join()
        p2.join()
        
        current_azimuth = azimuth
        current_altitude = altitude
        
        shoot_laser(2)
        
        # Continue to remaining targets WITHOUT returning to center
        for i, target in enumerate(sequence[1:], 1):
            print(f"\nTarget {i+1}/{len(sequence)}")
            
            # Calculate angles to next target
            azimuth, altitude = go_next(target, [r_position, theta_position, z_position])
            
            # Calculate RELATIVE movement from current position
            delta_azimuth = azimuth - current_azimuth
            delta_altitude = altitude - current_altitude
            
            # Move relative to current position
            p1 = m1.rotate(delta_azimuth * 180 / math.pi)
            p2 = m2.rotate(delta_altitude * 180 / math.pi)
            p1.join()
            p2.join()
            
            # Update current position
            current_azimuth = azimuth
            current_altitude = altitude
            
            shoot_laser(2)
            time.sleep(0.5)  # Brief pause
    
    print("\nSequence complete!")
    

def stopping():         #Stops any motion, honestly not sure how do this yet? Is this required?
    print('stoping')

    

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

def shoot_laser(duration = 3):
  print("LASER ON")
  GPIO.output(laser_pin, GPIO.HIGH)
  time.sleep(duration)
  GPIO.output(laser_pin, GPIO.LOW)
  print("LASER OFF")



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
      margin-top: 12px;
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

    .laser-btn {
      background: linear-gradient(135deg, #ff3b3b, #ff9f00);
      box-shadow: 0 0 18px rgba(255, 80, 0, 0.9);
    }
  </style>
</head>

<body>

  <div class="calibration-card">
    <h2>LASER TURRET CALIBRATION</h2>

    <!-- CALIBRATION FORM -->
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

    <!-- RUN / STOP CONTROLS -->
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

    <!-- MANUAL LASER CONTROL -->
    <form action="/laser_control.php" method="POST">
      <input type="hidden" name="laser_on" value="true">

      <button type="submit"
        class="laser-btn"
        onclick="return confirm('WARNING: Turn laser ON manually?');">
        MANUAL LASER ON
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
d.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
d.bind(('',8084))
d.listen(3)

web_page_thread = threading.Thread(target=server_web_page)
web_page_thread.daemon = True


#_______________________DELETE WHEN DEVIO SERVER UP

server_thread = threading.Thread(target=run_server)
server_thread.daemon = True
server_thread.start()


web_page_thread.start()
time.sleep(1)



try:
    while True:
        time.sleep(10)      #some wait

    
except KeyboardInterrupt:
    d.close()
    GPIO.cleanup()
    print("Could not fetch JSON FILE")
 
