from awg_scpi import AWG

  


resource =  'TCPIP::169.254.11.24::INSTR'
instr = AWG(resource)

## Upgrade Object to best match based on IDN string
instr = instr.getBestClass()

## Open this object and work with it
instr.open()

print('Using SCPI Device:     ' + instr.idn() + ' of series: ' + instr.series + '\n')

# set the channel (can pass channel to each method or just set it
# once and it becomes the default for all following calls)
instr.channel = 1

if instr.isOutputHiZ(instr.channel):
    print("Output High Impedance")
else:
    print("Output 50 ohm load")

instr.beeperOn()

# return to default parameters
instr.reset()               

instr.setWaveType('SINE')
instr.setFrequency(34.4590897823e3)
instr.setVoltageProtection(6.6)
instr.setAmplitude(3.2)
instr.setOffset(1.6)
instr.setPhase(0.45)

print("Voltage Protection is set to maximum: {}V Amplitude (assumes 0V offset)".format(instr.queryVoltageProtection()))

# turn on the channel
instr.outputOn()

# return to LOCAL mode
instr.setLocal()

instr.close()