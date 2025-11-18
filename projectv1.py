import multiprocessing
import time
import RPi.GPIO as GPIO
import requests
import json
import socket
import stepper_class
import threading

#-------------------Global Variables---------------------------
turret=[]   #list
globe=[]    #list
azimuth=0    #rad
altitude=0  #rad

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



#-------------------Parsing Json-------------------------------
url = "http://10.112.150.68:4084" #INSERT URL WHEN RELEASED

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




#-----------------HTML Setup-----------------------------------
##web page function-setups the page window for user to submit desired brightness level input
def web_page():
    html = """
    <!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Radar Turret Controller</title>

  <style>
    body {
      font-family: Arial, sans-serif;
      background-color: #0a0f24;
      color: #ffffff;
      text-align: center;
      margin: 0;
      padding: 0;
    }

    h1 {
      margin-top: 20px;
      font-size: 28px;
      text-shadow: 0 0 15px #00bfff;
    }

    .card {
      background-color: #11182f;
      padding: 25px;
      margin: 40px auto;
      width: 85%;
      max-width: 600px;
      border-radius: 20px;
      box-shadow: 0 0 35px rgba(0, 191, 255, 0.4);
    }

    label {
      display: block;
      margin-top: 15px;
      font-size: 18px;
    }

    input[type="number"] {
      width: 80%;
      padding: 10px;
      margin-top: 5px;
      border-radius: 10px;
      border: none;
      outline: none;
      font-size: 18px;
      text-align: center;
    }

    button {
      margin-top: 25px;
      padding: 15px 30px;
      background: linear-gradient(135deg, #1e90ff, #00bfff);
      color: white;
      font-weight: bold;
      font-size: 20px;
      border: none;
      border-radius: 15px;
      cursor: pointer;
      transition: 0.3s;
      box-shadow: 0 0 12px rgba(30, 144, 255, 0.6);
    }

    button:hover {
      transform: scale(1.1);
      box-shadow: 0 0 16px rgba(30, 144, 255, 0.9);
    }

    /* Emergency Stop Button */
    #stopBtn {
      background: linear-gradient(135deg, #ff0000, #ff4d4d);
      box-shadow: 0 0 18px rgba(255, 80, 80, 0.9);
    }

    #stopBtn:hover {
      box-shadow: 0 0 25px rgba(255, 80, 80, 1);
      transform: scale(1.12);
    }
  </style>
</head>

<body>

  <h1>RADAR TURRET CONTROLLER</h1>

  <div class="card">
    <form action="/set_zero.php" method="POST">
      <label for="turret">Turret Number:</label>
      <input type="number" id="turret" name="turret" min="1" max="10" required />

      <label for="zero_angle">Zero Angle (degrees):</label>
      <input type="number" id="zero_angle" name="zero_angle" required />

      <button id="submitBtn" type="submit">SET ZERO POSITION</button>
    </form>

    <!-- EMERGENCY STOP -->
    <button type="button" id="stopBtn" onclick="emergencyStop()">EMERGENCY STOP</button>

    <!-- FORM FOR RUN SIGNAL -->
    <form action="/start_run.php" method="POST">
      <input type="hidden" name="run_signal" id="run_signal" value="false">

      <button type="submit"
              id="runBtn"
              onclick="document.getElementById('run_signal').value = 'true';">
        INITIATE RUN
      </button>
    </form>

  </div>

  <script>
    function emergencyStop() {
      fetch("/emergency_stop.php", { method: "POST" });
      alert("EMERGENCY STOP ACTIVATED!");
    }
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
            print(data_dict)
            print("Not ready yet")
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
server_thread = threading.Thread(target=run_server)
server_thread.daemon = True
web_page_thread.start()
server_thread.start()
time.sleep(1)
parse_json()



try:
    while True:
        time.sleep(10)      #some wait

    
except KeyboardInterrupt:
    print("Could not fetch JSON FILE")
 
