# Version Control:
# 2024.12.29 init version, tested with MNE-LSL viewer, by Shawn Li
# 2025.02.06 added poor signal display, by Shawn Li

import time
from NeuroPy3 import NeuroPy3
from mne_lsl.lsl import StreamInfo,StreamOutlet
import numpy as np

initializing = True

def start_LSL_StreamOutLet():
    global sOutlet
    # 创建LSL流输出端点
    sInfo = StreamInfo(name='TGAM EEG Stream', stype="EEG", n_channels=1,
                       sfreq=256, dtype='float32', source_id="TGAM-LSL-Bridge")
    sInfo.set_channel_names(["Fp1"])
    sInfo.set_channel_types("eeg")
    sInfo.set_channel_units("microvolts")

    sOutlet = StreamOutlet(sInfo)  # Start Stream
    print("Started Stream:", sInfo)

def push_sample_to_stream(value):
    global sOutlet
    global initializing

    # data = np.array([value], dtype=np.int16)
    sOutlet.push_sample(np.array([value]))
    if initializing:
        initializing = False
        print("* Started Forwarding COM data to Stream...",)

def display_signal_quality(value):
    print("Poor Signal:", value)

if __name__ == '__main__':
    start_LSL_StreamOutLet()

    # connect to NeuroSky TGMA device through COM, and forward data to LSL stream
    neuropy = NeuroPy3("COM5")
    neuropy.setCallBack("rawVoltage", push_sample_to_stream)
    neuropy.setCallBack("poorSignal", display_signal_quality)

    neuropy.start()


    try:
        while True:
            time.sleep(0.1)  # 稍作延时，避免过度占用CPU
    except KeyboardInterrupt:
        print("\n* Session stopped\n")
    finally:
        neuropy.stop()  # 停止NeuroPy3数据接收
