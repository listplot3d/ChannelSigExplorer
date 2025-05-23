import logging
import os
import traceback
import mne
import numpy as np
from datetime import datetime
import time
import pyedflib
from pyqtgraph.Qt import QtCore, QtWidgets
from mne_lsl.lsl import resolve_streams
from mne_lsl.stream import StreamLSL
from GUIComp_Utils import GUI_Utils
from pathlib import Path
import yaml  


mne.set_log_level('WARNING')  # Set MNE log level to WARNING


class DeviceInfo:
    """Device information class, including channel selection, sample frequency, and device name"""

    def __init__(self, channel_picks, sample_freq, name=""):
        self.channel_picks = channel_picks
        self.sample_freq = sample_freq
        self.name = name  # Newly added device name attribute

    def __repr__(self):
        return (
            f"DeviceInfo(name={self.name}, channel_picks={self.channel_picks}, "
            f"sample_freq={self.sample_freq} Hz)"
        )

class DeviceInfoDatabase:
    """Collection of channels and sampling frequencies for all devices"""

    # Muse
    MUSE_ALL = DeviceInfo(["AF7", "AF8", "TP10"],
                          256,
                          "Muse All")

    MUSE = DeviceInfo(["AF7"],
                      256,
                      "Muse")

    #### Muse S + BlueMuse + mne-lsl viewer will hang after a few minutes due to freq config problem"""
    # MUSE_S = DeviceInfo(["AF7"],
    #                      512,  # BlueMuse shows 512, marked 256hz in stream, and actual push rate is
    #                                         is 512 Hz. Use this value here.
                         # "Muse S")

    # MNE-LSL Player
    PLAYER_ALL = DeviceInfo(["EEG Fpz-Cz", "EEG Pz-Oz"],
                            100,
                            "Player All")

    PLAYER = DeviceInfo(["EEG Fpz-Cz"],
                        100,
                        "Player")

    # TGAM
    TGMA_ALL = DeviceInfo(["Fp1", "Fp2"],
                          512,
                          "TGMA All")

    TGMA = DeviceInfo(["Fp1"], 512,
                      "TGAM")

    # Flexolink
    FLEXOLINK_ALL = DeviceInfo(["Fpz-Raw", "Fpz-Filtered"], 250,
                      "Flexo")
    FLEXOLINK = DeviceInfo(["Fpz-Filtered"], 250,
                      "Flexo")


class EEGStreamManager:


    def __init__(self, main_window,debug_mode = False):
        self.main_window = main_window
        self.status_bar = main_window.status_bar
        self.stream: StreamLSL = None  # LSL stream instance
        self.timer = None
        self.recording = False  # Whether it is recording
        self.record_file = None  # Recording file object
        self.record_file_name = None  # Recording file name
        self.device_info = None
        self.record_button = None  # Recording button reference
        self.data_buffer = None  
        self.debug_mode = debug_mode
        self.debug_counter = 0  
        self.debug_sample_counter = 0 
        self.debug_last_print_time = time.time()  
        self.write_count = 0  # For tracking file write operations
        self.first_write_time = None  # For tracking first write timestamp
        self.total_written_samples = 0  # For tracking total written samples
        self.log_file = open("eeg_stream.log", "a")
        self.log_message("EEGStreamManager initialized")

    def add_conn_menu_on_toolbar(self, toolbar):
        """Add connection menu"""
        connect_menu = QtWidgets.QMenu("🎧", toolbar)
        connect_menu.addAction("* Muse 2016 (via BlueMuse)").triggered.connect(
            lambda: self.connect_eeg_stream(DeviceInfoDatabase.MUSE))
        # connect_menu.addAction("* Muse S (via BlueMuse)").triggered.connect(
        #     lambda: self.connect_eeg_stream(DeviceInfoDatabase.MUSE_S))
        connect_menu.addAction("* LSL Player (via MNE-LSL)").triggered.connect(
            lambda: self.connect_eeg_stream(DeviceInfoDatabase.PLAYER))
        connect_menu.addAction("* TGMA (via TGAM-LSL-Bridge)").triggered.connect(
            lambda: self.connect_eeg_stream(DeviceInfoDatabase.TGMA))
        connect_menu.addAction("* FlexoLink (via FlexoTool)").triggered.connect(
            lambda: self.connect_eeg_stream(DeviceInfoDatabase.FLEXOLINK))
        connect_button = GUI_Utils.transform_menu_to_toolbutton("🔗", connect_menu)
        toolbar.addWidget(connect_button)

    def add_record_menu_on_toolbar(self, toolbar):
        """Add recording menu as a toolbutton"""
        # create menu for recording options
        record_menu = QtWidgets.QMenu("recording", toolbar)
        self.record_channel_action = record_menu.addAction("Current Channel")
        self.record_channel_action.triggered.connect(self.record_current_channel)

        # self.record_stream_action = record_menu.addAction("Whole Stream")
        # self.record_stream_action.triggered.connect(self.record_whole_stream)
        
        self.record_button = GUI_Utils.transform_menu_to_toolbutton("🔴", record_menu)
        toolbar.addWidget(self.record_button)

    def record_current_channel(self):
        """Handle recording of the current selected channel"""
        if self.recording:
            # stop recording
            self.recording = False
            self.record_button.setText("🔴")
            # self.log_message("Recording stopped")
            self.log_message("Recording stopped")
            self.close_recording_file()
        else:
            if not self.stream:
                self.log_message("Please connect stream before recording")
                return

            # start recording
            self.recording = True
            self.record_button.setText("🟥")
            self.record_channel_action.setText("Current Channel")  
            self.open_recording_file()
            self.log_message(
                f"Recording channels {self.device_info.channel_picks} to {self.record_file_name}")

    def record_whole_stream(self):
        """Handle 'record whole stream' option"""
        title = "To Be Implemented"
        text = "Your contribution to the source repository is more than welcome!"
        QtWidgets.QMessageBox.information(None, title, text)

    def open_recording_file(self):
        """Open an EDF+ file for recording"""
        # Create data_recorded directory if not exists
        os.makedirs("./data_recorded", exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.record_file_name = f"./data_recorded/{self.device_info.name}_case_{timestamp}.edf"
        channel_names = self.device_info.channel_picks
        channel_count = len(channel_names)
        sample_rate = self.device_info.sample_freq

        # Create EDF+ file
        self.record_file = pyedflib.EdfWriter(self.record_file_name, channel_count, file_type=pyedflib.FILETYPE_EDFPLUS)

        # Reset write count and first write time for new recording
        self.write_count = 0
        self.first_write_time = time.time()
        self.total_written_samples = 0

        # Set signal parameters
        signal_headers = []
        for i in range(channel_count):
            signal_headers.append({
                'label': channel_names[i] if channel_names[i] else f"Channel_{i}",
                'dimension': 'uV',
                'sample_frequency': sample_rate,  # Changed from 'sample_rate' to 'sample_frequency'
                'physical_min': -327.68*2,
                'physical_max': 327.67*2,
                'digital_min': -32768,
                'digital_max': 32767,
                'prefilter': '',
                'transducer': ''
            })
        self.record_file.setSignalHeaders(signal_headers)
        # Initialize buffer with proper dimensions
        self.data_buffer = np.empty((channel_count, 0))

    def check_newdata_and_process(self):
        """Periodically update the display and save the latest data"""
        try:
            if self.stream.n_new_samples < 1:
                return

            data, _ = self.get_new_data_from_stream()

            if data is None:
                return

            if self.debug_mode:
                samples_this_call = data.shape[1]  # Get number of samples in this call
                self.debug_sample_counter += samples_this_call

                # Calculate time difference
                current_time = time.time()
                if current_time - self.debug_last_print_time >= 1.0:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"DEBUG:[{timestamp}] Received samples/s: {self.debug_sample_counter}")
                    self.debug_sample_counter = 0
                    self.debug_last_print_time = current_time

            # Keep original data processing logic
            selected_channel_data = data
            for handler in self.main_window.loaded_indicators:
                handler.process_new_data_and_update_plot(selected_channel_data)

            if self.recording and self.record_file:
                self.save_data_to_file(data)
        except Exception as e:
            traceback.print_exc()
            self.log_message("failed to process new data")

    def save_data_to_file(self, data):
        # Check if data_buffer is None and initialize if needed 
        # although numpy 1.x don't need below part of code, but numpy 2.x needs it
        if self.data_buffer is None:
            channel_count = len(self.device_info.channel_picks)
            self.data_buffer = np.empty((channel_count, 0))
            self.write_count = 0
            self.first_write_time = time.time()
            
        """Save data to an EDF+ file"""
        # Add new data to buffer
        self.data_buffer = np.hstack((self.data_buffer, data))
        
        required_samples = self.device_info.sample_freq
        if self.data_buffer.shape[1] >= required_samples:
            # Extract data for 1 second
            data_to_write = self.data_buffer[:, :required_samples]
            self.data_buffer = self.data_buffer[:, required_samples:]
            
            # Convert to microvolts and write to file
            sample_list = [data_to_write[i, :] for i in range(data_to_write.shape[0])]
            self.record_file.writeSamples(sample_list)

            # Update total written samples
            self.total_written_samples += data_to_write.shape[1]
            # Update write count and calculate sample rate every 10 writes
            self.write_count += 1
            # Fallback: ensure first_write_time is set
            if self.first_write_time is None:
                self.first_write_time = time.time()
            if self.write_count % 10 == 0:
                elapsed_time = time.time() - self.first_write_time
                sample_rate = self.total_written_samples / elapsed_time
                self.log_message(f"Write sampling rate: {sample_rate:.2f} samples/sec")

    def close_recording_file(self):
        """Close the EDF+ file"""
        if self.record_file:
            self.record_file.close()
            self.record_file = None

            # Get the current timestamp and generate a new file name
            end_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name, ext = os.path.splitext(self.record_file_name)  # Split file name and extension
            new_file_name = f"{base_name}_to_{end_timestamp}{ext}"

            # Rename the file
            os.rename(self.record_file_name, new_file_name)

            # Update the file name and display the status
            self.record_file_name = new_file_name
            self.log_message(f"Data saved: {self.record_file_name}")

    def connect_eeg_stream(self, deviceInfo):
        """Connect to an EEG data stream"""
        self.device_info = deviceInfo
        real_freq = deviceInfo.sample_freq
        
        # read YAML config file
        config_path = Path(__file__).parent / 'indicators/indicator_global_config.yaml'
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        indicator_cfg_freq = config['STREAM']['sample_freq']

        if real_freq != indicator_cfg_freq:
            # update config
            config['STREAM']['sample_freq'] = real_freq
            
            # write to YAML file
            with open(config_path, 'w') as f:
                yaml.dump(config, f, sort_keys=False)
                
            self.log_message(f" indicator_global_config.yaml updated: {real_freq}Hz")
            QtCore.QCoreApplication.processEvents() # make sure the message is displayed
            indicator_cfg_freq = real_freq

        try:
            stream_list = resolve_streams(stype='EEG') + resolve_streams(stype='eeg')
            if not stream_list:
                self.log_message("No stream found")
                return

            sinfo = stream_list[0]
            self.stream = StreamLSL(bufsize=1, name=sinfo.name, stype=sinfo.stype, source_id=sinfo.source_id)
            self.stream.connect()
            self.stream.pick("eeg")

            assert "CPz" not in self.stream.ch_names  
            self.stream.add_reference_channels("CPz")

            self.start_timer()
            self.log_message(f"connected to {deviceInfo.channel_picks}")

        except Exception as e:
            traceback.print_exc()
            self.log_message("stream connection failed")

    def disconnect_stream(self):
        """Disconnect the EEG data stream"""
        if self.stream:
            self.stream.disconnect()

    def start_timer(self):
        """Start a timer"""
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.check_newdata_and_process)
        self.timer.start(50)  # Update every 50 ms

    def get_new_data_from_stream(self):
        """Get data from all channels in the EEG stream"""
        secs_for_new_data = self.stream.n_new_samples / self.device_info.sample_freq
        data = self.stream.get_data(winsize=secs_for_new_data, picks=self.device_info.channel_picks)  # picks=None means all channels
        return data

    def get_selected_channel_data(self, data):
        """Extract data from the selected channel"""
        if self.device_info.channel_picks is None:
            print("need to pick channels")
            exit(1)
        return data[self.device_info.channel_picks.index(self.device_info.channel_picks[0]), :]
    
    def log_message(self, message):
        """Log message to file and display in status bar"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_file.write(log_entry)
        self.log_file.flush() 
        self.status_bar.showMessage(message)  # Changed from self.log_message to status_bar.showMessage

    def __del__(self):
        """Clean up resources"""
        if hasattr(self, 'log_file') and self.log_file:
            self.log_file.close()