from pylablib.core.devio import SCPI
import numpy as np


from core.Registry import register_command
import time

class SDG6022X(SCPI.SCPIDevice):
    def __init__(self, addr):
        super().__init__(addr, term_write="\n", term_read="\n")

        # Access the raw PyVISA resource to adjust timeouts
        raw_dev = self.instr.instr
        raw_dev.timeout = 20_000          # 20s timeout (uploading large ARBs takes time)
        raw_dev.chunk_size = 4 * 1024 * 1024  # 4MB chunk size
        
    # --------------------------------------------------
    # Set functions
    # --------------------------------------------------
        
    def set_frequency(self, freq, channel): 
        self.write(f"C{channel}:BSWV FRQ,{freq}")
        
    def set_amplitude(self, amp, channel): 
        self.write(f"C{channel}:BSWV AMP,{amp}")
        
    def set_offset(self, offset, channel): 
        self.write(f"C{channel}:BSWV OFST,{offset}")
        
    def set_duty_cycle(self, duty, channel):
        self.write(f"C{channel}:BSWV DUTY,{duty}")
        
    def set_phase(self, phase, channel): 
        self.write(f"C{channel}:BSWV PHSE,{phase}")
        
    def set_ramp_symmetry(self, sym, channel): 
        self.write(f"C{channel}:BSWV SYM,{sym}")
        
    def set_pulse_width(self, width, channel): 
        self.write(f"C{channel}:BSWV WIDTH,{width}")
        
    def set_load(self, load, channel): 
        # 0 to 1e5 Ohms, and then 1e6 or above sets it to HiZ. 1e5 to 1e6 just set it to 1e5.
        self.write(f"C{channel}:OUTP LOAD,{load}")
        
    def enable_output(self, enabled, channel): 
        self.write(f"C{channel}:OUTP {'ON' if enabled else 'OFF'}")

    def set_reference(self, reference):
        self.write(f"ROSC {"INT" if reference == 1 else "EXT"}")

    def set_reference(self, reference):
        self.write(f"ROSC {"INT" if reference == 1 else "EXT"}")
        


    def set_length(self, channel, length):
        self.write(f"C{channel}:BSWV LENGTH,{length}")

    def set_edge_time(self, channel, edge_time):
        self.write(f"C{channel}:BSWV EDGE,{edge_time:.15f}")


    def set_differential_mode(self, channel, differential_mode):
        self.write(f"C{channel}:BSWV DIFFSTATE,{"ON" if differential_mode else "OFF"}")
    

    def change_reference_out(self):
            self.write('VKEY VALUE,18,STATE,1')
            self.write('VKEY VALUE,23,STATE,1')
    # --------------------------------------------------
    # Get functions
    # --------------------------------------------------
    def get_frequency(self, channel): 
        return self.ask(f"C{channel}:BSWV?")
    
    def is_output_enabled(self, channel): 
        return 'OUTP ON' in self.ask(f"C{channel}:OUTP?")

    def get_reference_out(self):
        return self.ask(f"ROSC?")
    
    def upload_custom_waveform(self, name, waveform, channel=1):
        """
        Uploads a waveform to the Siglent AWG.
        Command: C1:WVDT WVNM,name,WAVEDATA,binary_block
        """
        # Ensure data is float32
        waveform = np.asarray(waveform, dtype=np.float32)
        payload = waveform.tobytes()
        
        # 1. Prepare Header
        byte_count = len(payload)
        len_str = str(byte_count)
        # IEEE 488.2 Header: # + digits_in_length + length
        header = f"#{len(len_str)}{len_str}".encode("ascii")
        
        # 2. Prepare Command String
        # Siglent uses C1, C2 etc.
        cmd_str = f"C{channel}:WVDT WVNM,{name},WAVEDATA,"
        cmd_bytes = cmd_str.encode("ascii")
        
        # 3. Send Binary Block
        # We write directly to the raw instrument to handle binary data safely
        self.instr.instr.write_raw(cmd_bytes + header + payload)
        self.write("*WAI")
        
        # 4. Select the uploaded wave
        self.write(f"C{channel}:ARWV NAME,{name}")

    def set_sample_rate(self, sample_rate, channel=1):
        """Sets sample rate in Sa/s"""
        self.write(f"C{channel}:BSWV SRATE,{sample_rate}")



@register_command
def SDGTestFunc (instr, arg1, arg2, arg3):
    instr.test_print(arg1, arg2)


@register_command
def SDG60RefClock(instr, ref_source, ref_out):
    #10MHz clock in and out
    #ref_source True gives internal reference, False external reference

    instr.set_reference(ref_source)
    time.sleep(3.0)

    reference_out_str = instr.get_reference_out()

    reference_out_device = '10MOUT,ON' in reference_out_str

    if reference_out_device != ref_out:
        instr.change_reference_out()

    print(instr.get_reference_out())


@register_command
def SDG60ConfPRBS(instr, channel, bit_rate_period, bit_rate, period, amp, offset, differential_mode, length, edge_time):
    """
    Configures all PRBS settings in a single SCPI command string.
    Format: C1:BSWV WVTP,PRBS,BITRATE,10,AMP,2.0,...
    """
    cmd_parts = [f"C{channel}:BSWV WVTP,PRBS"]

    # 2. Bitrate OR Period
    if bit_rate_period:
        # #.12g formats the float to 12 significant digits (high precision)
        cmd_parts.append(f"BITRATE,{bit_rate:#.12g}")
    else:
        cmd_parts.append(f"PERI,{period:#.12g}")

    cmd_parts.append(f"AMP,{amp:#.12g}")

    cmd_parts.append(f"OFST,{offset:#.12g}")

    cmd_parts.append(f"LENGTH,{length}")

    diff_state = "ON" if differential_mode else "OFF"
    cmd_parts.append(f"DIFFSTATE,{diff_state}")

    cmd_parts.append(f"EDGE,{edge_time:#.12g}")

    full_command = ",".join(cmd_parts)
    
    print(f"[SENT] {full_command}")
    
    instr.write(full_command)

@register_command
def SDG60ConfSTDWFM(instr, **kwargs):

    channel = kwargs.get('channel', 1)
    wv_type = kwargs.get('waveform_type', 'SINE') 
    
    cmd_parts = [f"C{channel}:BSWV WVTP,{wv_type}"]

    is_freq_mode = kwargs.get('is_freq_mode', True)
    
    if is_freq_mode:
        if 'freq' in kwargs:
            cmd_parts.append(f"FRQ,{kwargs['freq']:#.12g}")
    else:
        if 'period' in kwargs:
            cmd_parts.append(f"PERI,{kwargs['period']:#.12g}")

    # 3. Dynamic Parameter Mapping
    param_map = {
        'amp': 'AMP',
        'offset': 'OFST',
        'phase': 'PHSE',
        'duty_cycle': 'DUTY',
        'ramp_symmetry': 'SYM',
        'pulse_width': 'WIDTH',
        # Add 'edge_time' here if standard waveforms (like Pulse) need it later
        'edge_time': 'EDGE' 
    }

    for json_key, scpi_key in param_map.items():
        if json_key in kwargs:
            value = kwargs[json_key]
            # Append formatted string
            cmd_parts.append(f"{scpi_key},{value:#.12g}")

    # 5. Join and Send
    full_command = ",".join(cmd_parts)
    print(f"[SENT] {full_command}")
    instr.write(full_command)

@register_command

def SDG60ConfPulse1(instr,kwargs):

    channel = kwargs.get('channel', 1)

    cmd_parts = [f"C{channel}:BSWV WVTP,PULSE"]

    if 'period' in kwargs:
        cmd_parts.append(f"PERI,{kwargs['period']:#.12g}")
    else:
        cmd_parts.append(f"FRQ,{kwargs['freq']:#.12g}")

    if 'amp' in kwargs:
        cmd_parts.append(f"AMP,{kwargs['amp']:#.12g}")
    else:
        cmd_parts.append(f"HLEV,{kwargs['amp']:#.12g}")

    if 'offset' in kwargs:
        cmd_parts.append(f"OFST,{kwargs['offset']:#.12g}")
    else:
        cmd_parts.append(f"LLEV,{kwargs['offset']:#.12g}")

    if 'pulse_width' in kwargs:
        cmd_parts.append(f"WIDTH,{kwargs['pulse_width']:#.12g}")
    else:
        cmd_parts.append(f"DUTY,{kwargs['duty_cycle']:#.12g}")

    if 'rise_time' in kwargs:
        cmd_parts.append(f"RIS,{kwargs['rise_time']:#.12g}")
    
    if 'fall_edge' in kwargs:
        cmd_parts.append(f"FALL,{kwargs['fall_edge']:#.12g}")

    if 'delay_time' in kwargs:
        cmd_parts.append(f"EDGE,{kwargs['delay_time']:#.12g}")

    full_command = ",".join(cmd_parts)
    print(f"[SENT] {full_command}")
    instr.write(full_command)





if __name__ == "__main__":
    # awg = SDG6022X('TCPIP::127.0.0.1::5025::SOCKET')

    # 'TCPIP::169.254.11.24::INSTR'

    # TCPIP::127.0.0.1::5026::SOCKET

    with SDG6022X('TCPIP::127.0.0.1::18882::SOCKET') as awg:
        # SDG60RefClock(awg, True, False)
        #awg.set_sample_rate(1e9, channel=1)
        #SDG60ConfPRBS(awg, channel=1, bit_rate_period=True, bit_rate=1000, period=0.2e-2, amp=1.0, offset=0.0,length=3, differential_mode=False, edge_time=1e-8)
        # pass
        # awg.write('Test test')
        #awg.set_sample_rate(123, channel=1)
        #SDG60ConfSTDWFM(awg, channel=1, waveform_type="SQUARE", is_freq_mode=True, freq=2.0, period=0.2e-2, amp=0.1, offset=0.0, ramp_symmetry=50.0, phase=0.0,)
        SDG60ConfPulse1(awg, dict(channel=1, freq=1e3, amp=2.0, offset=0.0, pulse_width=1e-3, rise_time=1e-6))