from pylablib.devices import AWG

class SDG6022X(AWG.GenericAWG):
    def __init__(self, addr):
        super().__init__(addr)


if __name__ == "__main__":
    ip = "TCPIP0::169.254.11.24::INSTR"
    awg = SDG6022X(ip)

    awg.set_amplitude(1.234, channel=1)
    awg.close()
