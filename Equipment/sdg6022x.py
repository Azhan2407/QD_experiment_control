from pylablib.core.devio import SCPI
import numpy as np
from core.Registry import register_command


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
    def set_function(self, wv, channel): 
        self.write(f"C{channel}:BSWV WVTP,{wv}")
        
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

    # --------------------------------------------------
    # Get functions
    # --------------------------------------------------
    def get_frequency(self, channel): 
        return self.ask(f"C{channel}:BSWV?")
    
    def is_output_enabled(self, channel): 
        return 'OUTP ON' in self.ask(f"C{channel}:OUTP?")
    
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

    def test_print(self, arg1, arg2, arg3):
        print(f'Test print: {arg1, arg2, arg3}')


@register_command
def SDGTestFunc (instr : SDG6022X, arg1, arg2, arg3):
    instr.test_print(arg1, arg2, arg3)


    
@register_command
def SDG_Set_Arb(instr, arg1, arg2):
    instr.set_function(arg1)
    


