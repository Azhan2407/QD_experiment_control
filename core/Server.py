import zmq
import json
from core.Registry import commands, devices

def handle_tcp(message):
    cmd = message.pop('cmd')
    instr = message.pop('instrument')
    commands[cmd](instr=devices[instr],**message)



