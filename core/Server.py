import zmq
import json
from core.Registry import commands, devices

def handle_tcp(message):
    cmd = message.pop('cmd')
    instr = message.pop('instr')
    commands[cmd](instr=instr,**message)



