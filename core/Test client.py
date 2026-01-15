import zmq
import json 

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")

    
# Create the dictionary
data = {"cmd": 'SDGtest_print', 'instr' : 'SDG_Gen1'}

while True:
    data['cmd']=input('cmd: ')
    data['arg1']=input('arg1: ')
    data['arg2']=input('arg2: ')
    data['arg3']=input('arg3: ')
    print(f"Sending: {data}")
    socket.send_json(data)

    # Receive response as a dict
    message = socket.recv_string()
    print(f"Received: {message}")