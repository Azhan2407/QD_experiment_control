from pylablib.devices import AWG
import numpy as np
from core.Registry import register_command
import time

class Agilent33600A(AWG.GenericAWG):
    """
    Minimal driver wrapper for Keysight/Agilent 33600A series AWGs.

    Args:
        addr: VISA address of the instrument.
        channels_number: number of channels; default is 2.
    """

    def __init__(self, addr, channels_number=2):
        self._channels_number = channels_number
        super().__init__(addr)

        # Access the raw PyVISA instrument
        visa_instr = self.instr.instr
        visa_instr.timeout = 10_000          # ms
        visa_instr.chunk_size = 4 * 1024 * 1024  # 4 MB safe value



    def upload_custom_waveform(self, name, waveform, channel=1):
        """
        Upload a custom waveform to the specified channel.

        Args:
            name (str): Name to assign to the waveform in the AWG.
            waveform (array-like): Waveform data as float32 values in [-1, 1].
            channel (int, optional): Channel number. Default is 1.
        """
        waveform = np.asarray(waveform, dtype=np.float32)
        payload = waveform.tobytes()

        visa_instr = self.instr.instr

        # 1. Setup
        self.write("DISP:TEXT 'Uploading ARB'")
        self.write("FORM:BORD SWAP")
        self.clear_arbritrary(channel)

        # 2. Manual binary upload
        byte_count = len(payload)
        len_str = str(byte_count)
        header = f"#{len(len_str)}{len_str}".encode("ascii")

        cmd = f"SOUR{channel}:DATA:ARB {name},".encode("ascii")
        message = cmd + header + payload + b"\n"

        visa_instr.write_raw(message)
        self.write("*WAI")

        # 3. Configure waveform

        self.write("DISP:TEXT ''")

    def set_sample_rate(self, sample_rate, channel):
        """
        Set the sample rate for a specified channel.

        Args:
            sample_rate (float): Sample rate in Sa/s.
            channel (int, optional): Channel number. Default is 1.
        """
        self.write("*WAI")
        self.write(f"SOUR{channel}:FUNC:ARB:SRAT {sample_rate}")


    def arb_phase_sync(self):
        """
        Not too sure what function is - comes from A33ArbPhaseSync.vi
        """
        self.write(":FUNC:ARB:SYNC;")


    def clear_arbritrary(self, channel):
        self.write(f"SOUR{channel}:DATA:VOL:CLE")

    def configure_amplitude_modulation(self, channel, AM_source, modulation_waveform, modulation_frequency, enable_carrier_supression, enable_amplitude_modulation, modulation_depth):
        sources_str = ['INT','EXT','CH1','CH2',][int(AM_source)]
        waveforms_str = ['SIN','SQU','TRI','RAMP','NRAM','NOIS','PRBS','ARB'][int(modulation_waveform)]
        

        cmd = f"SOUR{channel}:AM:STAT {'ON' if enable_amplitude_modulation else 'OFF'};"
        cmd+= f":SOUR{channel}:AM:SOUR {sources_str};"

        if AM_source==0:
            cmd += f":SOUR{channel}:AM:INT:FUNC {waveforms_str};"
            cmd += f":SOUR{channel}:AM:INT:FREQ {modulation_frequency:#.12g};"

        cmd+= f":SOUR{channel}:AM:DEPT {modulation_depth:#.12g};"
        cmd+= f":SOUR{channel}:AM:DSSC {'ON' if enable_carrier_supression else 'OFF'};"

        self.write(cmd)
        
    def configure_ARB(self, channel, arb_number, amplitude, f_sr_p, phase, filter_key, dc_offset, advance_mode, freq_sample_rate_period):
        if arb_number>0:
            arb_string=arb_number
        else:
            arb_string=f'"INT:\\332XX_ARBS\\ARBF{abs(arb_number):.0f}.ARB"'

        cmd = f':SOUR{channel}:FUNC:ARB ARB{arb_number};:'
        cmd += f'SOUR{channel}:FUNC ARB;:'
        cmd += f'SOUR{channel}:FUNC ARB:FILT {["OFF", "STEP", "NORM"][filter_key]};:'
        cmd += f'SOUR{channel}:FUNC ARB:ADV {"TRIG" if advance_mode else "SRAT"};:'
        cmd += f'SOUR{channel}:VOLT {amplitude:#.12g};:'
        cmd += f'SOUR{channel}:VOLT:OFFS {dc_offset:#.12g};:'
        cmd += f'SOUR{channel}:FUNC ARB:{["FREQ", "SRAT", "PER"][f_sr_p]} {freq_sample_rate_period:#.12g};:'
        
        if (phase >= -360) and (phase <360):
            cmd += f'SOUR{channel}:PHASE:ARB {phase:#.12g};:'
 
        self.write(cmd)
    
    def configure_burst(self, channel, burst_mode, burst_phase, burst_count, gate_polarity, internal_period, enable_burst):
        if enable_burst:
            if burst_mode:
                cmd = f'SOUR{channel}:BURS:MODE GAT;:'
                cmd += f'SOUR{channel}:BURS:GATE:POL {'INV' if gate_polarity else 'NORM'};:'
                cmd += f'SOUR{channel}:BURS:INT:PER {internal_period:#.12g};:'
            else:            
                cmd = f'SOUR{channel}:BURS:MODE TRIG;:'
                cmd += f'SOUR{channel}:BURS:PHAS {burst_phase:#.12g};:'
                cmd += f'SOUR{channel}:BURS:NCYC {burst_count:.0f};:'
            
            cmd += f'SOUR{channel}:BURS:STAT ON'

        else:
            cmd = f'SOUR{channel}:BURS:STAT OFF'
        self.write(cmd)
        
    def configure_frequency_modulation(self, channel, enable_frequency_modulation, fm_source, modulation_waveform, modulation_deviation, modulation_frequency):
        modulation_waveform_str = ['SIN', 'SQU', 'TRI', 'RAMP', 'NRAM', 'NOIS', 'PRBS', 'ARB'][int(modulation_waveform)]
        fm_source_str = ['INT', 'EXT', 'CH1', 'CH2'][int(fm_source)]

        if enable_frequency_modulation:
            cmd = f'SOUR{channel}:FM:STAT ON;:'
            cmd += f'SOUR{channel}:AM:SOUR {fm_source_str};:'
            if fm_source_str=='INT':
                cmd += f'SOUR{channel}:FM:INT:FUNC {modulation_waveform_str};:'
                cmd += f'SOUR{channel}:FM:INT:FREQ {modulation_frequency:#.12g};:'
            cmd += f'SOUR{channel}:FM:DEV {modulation_deviation:#.12g};'
            
        else:
            cmd = f'SOUR{channel}:FM:STAT OFF;:'
        
        self.write(cmd)
        
    def configure_frequency_sweep(self, channel, enable_frequency_sweep, sweep_spacing, sweep_time, hold_time, return_time, start_frequency, stop_frequency):
        sweep_spacing_str = ['LIN', 'LOG'][int(sweep_spacing)]

        if enable_frequency_sweep:
            cmd = f':SWE{channel}:STAT ON;:'
            cmd += f'SWE{channel}:SPAC {sweep_spacing_str};:'
            cmd += f'SWE{channel}:TIME {sweep_time:#.7g};:'
            cmd += f'FREQ1:STAR {start_frequency:#.12g};:'
            cmd += f'FREQ1:STOP {stop_frequency:#.12g};:'
            cmd += f'SWE{channel}:HTIME {hold_time:#.7g};:'
            cmd += f'SWE{channel}:RTIME {return_time:#.7g};'            
            
        else:
            cmd = f':SWE{channel}:STAT OFF;'
        
        self.write(cmd.upper())

    def configure_pulse(self, channel, pulse_period, pulse_width, leading_edge, trailing_edge):
        cmd = f':SOUR{channel}:FUNC:PULS:PER {pulse_period:#.12g};:'
        cmd += f'SOUR{channel}:FUNC:PULS:WIDT {pulse_width:#.12g};:'
        cmd += f'SOUR{channel}:FUNC:PULS:TRAN:LEAD {leading_edge:#.12g};:'
        cmd += f'SOUR{channel}:FUNC:PULS:TRAN:TRA {trailing_edge:#.12g};'
        
        self.write(cmd)

    def configure_trigger(self, channel, trigger_source, trigger_slope, delay, int_period, trigger_level):
        trigger_source_str = ['IMM', 'TIM', 'EXT', 'BUS'][int(trigger_source)]
        trigger_slope_str = ['POS', 'NEG'][int(trigger_slope)]        

        cmd = f':TRIG{channel}: SOUR {trigger_source_str};:'
        cmd += f'TRIG{channel}:SLOP {trigger_slope_str};:'
        cmd += f'TRIG{channel}:DEL {delay:#.12g};:'
        cmd += f'TRIG{channel}:TIM {int_period:#.12g};:'
        cmd += f'TRIG{channel}:LEV {trigger_level:#.12g};'
        
        self.write(cmd)

    def configure_waveform(self, channel, waveform, amplitude, dc_offset, frequency_bw_bitrate, phase):
        waveform_str = ['SIN','SQU','PULS','RAMP','NOIS','DC','PRBS','TRI'][int(waveform)]
        
        cmd = f':SOUR{channel}:FUNC {waveform_str};:'

        if waveform_str!='DC':
            cmd += f'SOUR{channel}:VOLT {amplitude:#.12g};:'
        
        cmd += f'SOUR{channel}:VOLT:OFFS {dc_offset:#.12g};:'
        if waveform_str=='NOIS':
            cmd += f'SOUR{channel}:FUNC NOISE:BAND {frequency_bw_bitrate:#.12g};:'  
        if waveform_str=='PRBS':
            cmd += f'SOUR{channel}:FUNC:PRBS:BRAT {frequency_bw_bitrate:#.12g};:'
        else:
            cmd += f'SOUR{channel}:FREQ {frequency_bw_bitrate:#.12g};:'

        if waveform_str not in ['NOIS', 'DC']:        
            cmd += f'SOUR{channel}:PHASE {phase:#.12g};'
        
        self.write(cmd)
        
    def initialize(self, reset): 
        if reset:
            self.write('*RST')
            time.sleep(0.5)
               
        self.write('*CLS;*ESE 1;*SRE 32;')
        time.sleep(0.5)        
        self.write('*WAI')
        time.sleep(0.5)
        self.write(':ROSCillator:SOURce:AUTO  ON;')
        
    def output_on_off(self, channel, enable_output, output_mode, polarity, impedance):
        #  :OUTP1:LOAD 50.000000000000;:OUTP1:POL NORM;:OUTP1:MODE NORM;:OUTP1 ON;
        polarity_str = ['NORM', 'INV'][int(polarity)]
        enable_output_str = ['OFF', 'ON'][int(enable_output)]
        output_mode_str = ['NORM', 'GATED'][int(output_mode)]
        
        cmd = f':OUTP{channel}:LOAD {impedance:#.12g};:'
        cmd+= f'OUTP{channel}:POL {polarity_str};:'
        cmd+= f'OUTP{channel}:MODE {output_mode_str};:'
        cmd+= f'OUTP{channel} {enable_output_str};'
        self.write(cmd)
        
    def phase_sync(self):
        self.write(':SOUR1:PHASE:SYNC;')

    def read_error(self):
        return self.ask('SYST:ERR?')
    
    def trigger(self):
        self.write('*TRG;')
        
    def configure_prbs(self, channel, sequence_type, edge):
        # :SOUR1:FUNC:PRBS:DATA PN7;:SOUR1:FUNC:PRBS:TRAN 4.000000000000E-9
        cmd = f':SOUR{channel}:FUNC:PRBS:DATA PN{sequence_type:.0f};:'
        cmd+= f'SOUR{channel}:FUNC:PRBS:TRAN {edge:#.12g};' 
        self.write(cmd)
        


def require_Agilent33600A(func):    
    def wrapper(instr, *args, **kwargs):
        if not isinstance(instr, Agilent33600A):
            raise TypeError("instr must be an instance of SDG")
        return func(instr, *args, **kwargs)
    return wrapper




@register_command
@require_Agilent33600A
def A33ArbPhaseSync(instr : Agilent33600A):
   instr.arb_phase_sync()


@register_command
@require_Agilent33600A
def A33ClearArbitrary(instr : Agilent33600A):
   instr.clear_arbritrary()


@register_command
@require_Agilent33600A
def A33ConfigureAM(instr : Agilent33600A, channel, am_source, modulation_waveform, modulation_frequency, enable_carrier_supression, enable_amplitude_modulation, modulation_depth):
    instr.configure_amplitude_modulation(channel, am_source, modulation_waveform, modulation_frequency, enable_carrier_supression, enable_amplitude_modulation, modulation_depth)


@register_command
@require_Agilent33600A
def A33ConfigureARB(instr : Agilent33600A, channel, arb_number, amplitude, f_sr_p, phase, filter_key, dc_offset, advance_mode, freq_sample_rate_period):
    instr.configure_ARB(channel, arb_number, amplitude, f_sr_p, phase, filter_key, dc_offset, advance_mode, freq_sample_rate_period)


@register_command
@require_Agilent33600A
def A33ConfigureBurst(instr : Agilent33600A, channel, burst_mode, burst_phase, burst_count, gate_polarity, internal_period, enable_burst):
    instr.configure_burst(channel, burst_mode, burst_phase, burst_count, gate_polarity, internal_period, enable_burst)
    
@register_command
@require_Agilent33600A
def A33ConfigureFM(instr : Agilent33600A, channel, enable_frequency_modulation, fm_source, modulation_waveform, modulation_deviation, modulation_frequency):
    instr.configure_frequency_modulation(channel, enable_frequency_modulation, fm_source, modulation_waveform, modulation_deviation, modulation_frequency)
    
@register_command
@require_Agilent33600A
def A33ConfigureFSweep(instr : Agilent33600A, channel, enable_frequency_sweep, sweep_spacing, sweep_time, hold_time, return_time, start_frequency, stop_frequency):
    instr.configure_frequency_sweep(channel, enable_frequency_sweep, sweep_spacing, sweep_time, hold_time, return_time, start_frequency, stop_frequency)
    
@register_command
@require_Agilent33600A
def A33ConfigureFSweep(instr : Agilent33600A, channel, enable_frequency_sweep, sweep_spacing, sweep_time, hold_time, return_time, start_frequency, stop_frequency):
    instr.configure_frequency_sweep(channel, enable_frequency_sweep, sweep_spacing, sweep_time, hold_time, return_time, start_frequency, stop_frequency)
    
@register_command
@require_Agilent33600A
def A33ConfigurePulse(instr : Agilent33600A, channel, pulse_period, pulse_width, leading_edge, trailing_edge):
    instr.configure_pulse(channel, pulse_period, pulse_width, leading_edge, trailing_edge)

@register_command
@require_Agilent33600A
def A33ConfigureTrigger(instr : Agilent33600A, channel, trigger_source, trigger_slope, delay, int_period, trigger_level):  
    instr.configure_trigger(channel, trigger_source, trigger_slope, delay, int_period, trigger_level)


@register_command
@require_Agilent33600A
def A33ConfigureWFM(instr : Agilent33600A, channel, waveform, amplitude, dc_offset, frequency_bw_bitrate, phase):  
    instr.configure_waveform(channel, waveform, amplitude, dc_offset, frequency_bw_bitrate, phase)

@register_command
@require_Agilent33600A
def A33Initialize(instr : Agilent33600A, reset):  
    instr.initialize(reset)

@register_command
@require_Agilent33600A
def A33LoadArbitraryVolat(instr : Agilent33600A, channel, arb_number, waveform_path, waveform_column_number, waveform_source, waveform_array, waveform_length):  
    instr.load_arbitrary_volatile(channel, arb_number, waveform_path,)

@register_command
@require_Agilent33600A
def A33OutputOnOff(instr : Agilent33600A, channel, enable_output, output_mode, polarity, impedance):  
    instr.output_on_off(channel, enable_output, output_mode, polarity, impedance)

@register_command
@require_Agilent33600A
def A33PhaseSync(instr : Agilent33600A):  
    instr.phase_sync()
    
@register_command
@require_Agilent33600A
def A33ReadError(instr : Agilent33600A):  
    error = print(instr.read_error())    
    return error

@register_command
@require_Agilent33600A
def A33Trg(instr : Agilent33600A):  
    instr.trigger()
    
@register_command
@require_Agilent33600A
def A33Trg(instr : Agilent33600A):  
    instr.trigger()
    
@register_command
@require_Agilent33600A
def A33ConfigurePRBS(instr : Agilent33600A, channel, sequence_type, edge):  
    instr.configure_prbs(channel, sequence_type, edge)


if __name__=="__main__":
    # ip = 'TCPIP::169.254.11.23::INSTR'
    #  TCPIP::169.254.49.101::5026::SOCKET
    ip = 'TCPIP::127.0.0.1::5025::SOCKET'
    num_points = 4e4
    sample_rate = 1e6
    t = np.linspace(0, 1, int(num_points))
    
    sig = np.sin(2 * np.pi * 50 * t) 
    sig /= np.max(np.abs(sig))

    # awg = Agilent33600A(ip)

        # SOUR1:FUNC:PULS:PER 1.000000000000;:SOUR1:FUNC:PULS:WIDT 0.100000000000;:SOUR1:FUNC:PULS:TRAN:LEAD 4.000000000000E-9;:SOUR1:FUNC:PULS:TRAN:TRA 4.000000000000E-9;
    with Agilent33600A(ip) as awg:
    # awg.upload_custom_waveform('test', sig)
    # awg.set_function('arb')
    # awg.set_sample_rate(sample_rate)
        # A33ConfigureARB(awg, channel=2, arb_number=1, amplitude=2.23, f_sr_p=0, phase=250, filter_key=2, dc_offset=0.456, advance_mode=1, freq_sample_rate_period=1e3)
        # A33ConfigureBurst(awg, channel=2, burst_mode=1, burst_phase=180.0, burst_count=99999, gate_polarity=0, internal_period=123, enable_burst=1)
        # A33ConfigureFSweep(instr=awg, channel=1, enable_frequency_sweep=1, sweep_spacing=0, sweep_time=1.23, hold_time=3.4, return_time=5.6, start_frequency=123e-6, stop_frequency=123e3)
        # A33ConfigureTrigger(instr=awg, channel=2, trigger_source=2, trigger_slope=1, delay=1.23, int_period=4.56, trigger_level=1.2) 
        # A33Initialize(instr=awg, reset=1)
        # A33OutputOnOff(instr=awg, channel=1, enable_output=0, output_mode=0, polarity=1, impedance=1234)
        # A33PhaseSync(instr=awg)
        A33ConfigurePRBS(awg, 2, 4, 5e-6)
