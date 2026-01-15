import zmq
from contextlib import ExitStack

from core.Server import handle_tcp
from core.Registry import register_device, commands, devices

from Equipment import SDG6022X, Agilent33600A



device_configs = {
    'AG33600A_Gen1' : (Agilent33600A, 'TCPIP::169.254.11.23::INSTR'),
    'SDG_Gen1' : (SDG6022X, 'TCPIP::169.254.11.24::INSTR'),
}


with ExitStack() as stack:
    for instrument_class, name, addr in device_configs:
        dev = stack.enter_context(instrument_class(addr))
        register_device(name, dev)

    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")
    socket.RCVTIMEO = 1000

    print(commands)
    print(devices)

    run = True
    while run:
        try:
            message = socket.recv_json()
            handle_tcp(message)
            socket.send_string('Completed')
            
        except zmq.Again:
            print('Waiting for command')
            continue
        
        except KeyboardInterrupt:
            print('Closing connections')
            run = False
            
        except Exception as e:
            print(f'Error: {e}')
            socket.send_string('Failed')

print('Connections closed.')