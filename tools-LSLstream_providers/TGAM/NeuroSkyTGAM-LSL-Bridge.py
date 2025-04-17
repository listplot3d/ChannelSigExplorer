# Version Control:
# 2024.12.29 init version, tested with MNE-LSL viewer, by Shawn Li
# 2025.02.06 added poor signal display, by Shawn Li
# 2025.03.06 added debugging for forwarding speed, by Shawn Li
# 2025.04.17 set COM as user input, by Shawn Li

import time
from NeuroPy3 import NeuroPy3
from mne_lsl.lsl import StreamInfo,StreamOutlet
import numpy as np
import sys

initializing = True
debug_mode = False

def start_LSL_StreamOutLet():
    global sOutlet
    # Create LSL stream outlet
    sInfo = StreamInfo(name='TGAM EEG Stream', stype="EEG", n_channels=1,
                       sfreq=512, dtype='float32', source_id="TGAM-LSL-Bridge")
    sInfo.set_channel_names(["Fp1"])
    sInfo.set_channel_types("eeg")
    sInfo.set_channel_units("microvolts")

    sOutlet = StreamOutlet(sInfo)  # Start Stream
    print("Started Stream:", sInfo)

# Add counters in global variables
push_count = 0
last_print_time = time.time()

def push_sample_to_stream(value):
    global sOutlet
    global initializing
    global push_count, last_print_time  # Reference new global variables
    
    # Increment counter
    push_count += 1
    
    # Keep original pushing logic
    sOutlet.push_sample(np.array([value]))
    
    if debug_mode:
        # Add per-second output logic
        current_time = time.time()
        if current_time - last_print_time >= 1.0:
            print(f"[{time.strftime('%H:%M:%S')}] Forwarded Samples: {push_count}")
            push_count = 0
            last_print_time = current_time
        
    if initializing:
        initializing = False
        print("* Started Forwarding COM data to Stream...")
        
last_sig_quality_val = None
def display_signal_quality(value):
    global last_sig_quality_val  # Add state tracking variable
    
    if value != last_sig_quality_val:
        print(f"[{time.strftime('%H:%M:%S')}] Poor Signal:", value)
        last_sig_quality_val = value

if __name__ == '__main__':
    debug_mode = 'debug' in sys.argv
    start_LSL_StreamOutLet()

    # Ask the user for the serial port, default is COM5
    port = input("Enter serial port for TGAM device (default: COM5): ").strip()
    if not port:
        port = "COM5"
    print(f"* Using port: {port}")
    neuropy = NeuroPy3(port)
    neuropy.setCallBack("rawVoltage", push_sample_to_stream)
    neuropy.setCallBack("poorSignal", display_signal_quality)

    neuropy.start()


    try:
        while True:
            time.sleep(0.1)  # Add delay to reduce CPU usage
    except KeyboardInterrupt:
        print("\n* Session stopped\n")
    finally:
        neuropy.stop()  # Stop NeuroPy3 data reception
