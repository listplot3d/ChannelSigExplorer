import logging
import os
import traceback
from enum import Enum
import mne
import numpy as np
from datetime import datetime
import pyedflib
from pyqtgraph.Qt import QtCore, QtWidgets
from mne_lsl.lsl import resolve_streams
from mne_lsl.stream import StreamLSL
from GUIComp_Utils import GUI_Utils
from indicators.__Indicator_Global_Cfg import Indicator_Globals

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

class DevicesInfo:
    """Collection of channels and sampling frequencies for all devices"""

    # Muse
    MUSE_ALL = DeviceInfo(["AF7", "AF8", "TP10"],
                          256,
                          "Muse All")

    MUSE = DeviceInfo(["AF7"],
                      256,
                      "Muse")
    #
    # MUSE_S = DeviceInfo(["AF7"],
    #                     512,  # BlueMuse LSL shows 256, but the actual rate is 512 Hz. Use this value here.
    #                     "Muse S")

    # MNE-LSL Player
    PLAYER_ALL = DeviceInfo(["EEG Fpz-Cz", "EEG Pz-Oz"],
                            100,
                            "Player All")

    PLAYER = DeviceInfo(["EEG Fpz-Cz"],
                        100,
                        "Player")

    # TGMA
    TGMA_ALL = DeviceInfo(["Fp1", "Fp2"],
                          256,
                          "TGMA All")

    TGMA = DeviceInfo(["Fp1"], 256,
                      "TGMA")


class EEGStreamManager:

    def __init__(self, main_window):
        self.main_window = main_window
        self.status_bar = main_window.status_bar
        self.stream: StreamLSL = None  # LSL stream instance
        self.timer = None
        self.recording = False  # Whether it is recording
        self.record_file = None  # Recording file object
        self.record_file_name = None  # Recording file name
        self.device_info = None
        self.record_button = None  # Recording button reference
        self.data_buffer = None  # 新增数据缓冲区

    def add_conn_menu_on_toolbar(self, toolbar):
        """Add connection menu"""
        connect_menu = QtWidgets.QMenu("🎧", toolbar)
        connect_menu.addAction("* Muse 2016 (via BlueMuse)").triggered.connect(
            lambda: self.connect_eeg_stream(DevicesInfo.MUSE))
        # connect_menu.addAction("Muse_S").triggered.connect(
        #     lambda: self.connect_eeg_stream(DevicesInfo.MUSE_S))
        connect_menu.addAction("* LSL Player (via MNE-LSL)").triggered.connect(
            lambda: self.connect_eeg_stream(DevicesInfo.PLAYER))
        connect_menu.addAction("* TGMA (via TGAM-LSL-Bridge)").triggered.connect(
            lambda: self.connect_eeg_stream(DevicesInfo.TGMA))

        connect_button = GUI_Utils.transform_menu_to_toolbutton("🔗", connect_menu)
        toolbar.addWidget(connect_button)

    def add_record_menu_on_toolbar(self, toolbar):
        """Add recording menu as a toolbutton"""
        # 创建一个菜单
        record_menu = QtWidgets.QMenu("🎦", toolbar)

        # 添加选项
        record_menu.addAction("Record Current Channel").triggered.connect(self.record_current_channel)
        record_menu.addAction("Record Whole Stream").triggered.connect(self.record_whole_stream)

        # 创建工具按钮并关联菜单
        self.record_button = GUI_Utils.transform_menu_to_toolbutton("🎦", record_menu)

        # 添加工具按钮到工具栏
        toolbar.addWidget(self.record_button)

    def record_current_channel(self):
        """Handle recording of the current selected channel"""
        if self.recording:
            # 停止录制
            self.recording = False
            self.record_button.setText("🎦")
            self.status_bar.showMessage("Recording stopped")
            self.close_recording_file()
        else:
            if not self.stream:
                self.status_bar.showMessage("Please connect stream before recording")
                return

            # 开始录制
            self.recording = True
            self.record_button.setText("⏹️")
            self.open_recording_file()

            self.status_bar.showMessage(
                f"Recording channels {self.device_info.channel_picks} to {self.record_file_name}")

    def record_whole_stream(self):
        """Handle 'record whole stream' option"""
        title = "To Be Implemented"
        text = "Your contribution to the source repository is more than welcome!"
        QtWidgets.QMessageBox.information(None, title, text)

    def toggle_recording(self):
        """Toggle recording state"""
        if self.recording:
            # Stop recording
            self.recording = False
            self.record_button.setText("🎦")
            self.status_bar.showMessage("recording stopped")
            self.close_recording_file()
        else:
            if not self.stream:
                self.status_bar.showMessage("please connect stream before recording")
                return

            # Start recording
            self.recording = True
            self.record_button.setText("⏹️")
            self.open_recording_file()
            self.status_bar.showMessage(f"recording channels{self.device_info.channel_picks} to {self.record_file_name}")

    def open_recording_file(self):
        """Open an EDF+ file for recording"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.record_file_name = f"./{self.device_info.name}_case_{timestamp}.edf"
        # channel_names = self.stream.ch_names
        channel_names = self.device_info.channel_picks
        channel_count = len(channel_names)
        sample_rate = self.device_info.sample_freq

        # Create EDF+ file
        self.record_file = pyedflib.EdfWriter(self.record_file_name, channel_count, file_type=pyedflib.FILETYPE_EDFPLUS)

        # Set signal parameters
        signal_headers = []
        for i in range(channel_count):
            signal_headers.append({
                'label': channel_names[i] if channel_names[i] else f"Channel_{i}",
                'dimension': 'uV',
                'sample_rate': sample_rate,
                'physical_min': -500,
                'physical_max': 500,
                'digital_min': -32768,
                'digital_max': 32767,
                'prefilter': '',
                'transducer': ''
            })
        self.record_file.setSignalHeaders(signal_headers)
        self.data_buffer = np.empty((channel_count, 0))  # 初始化缓冲区

    def save_data_to_file(self, data):
        """Save data to an EDF+ file"""
        # 将新数据添加到缓冲区
        self.data_buffer = np.hstack((self.data_buffer, data))
        
        required_samples = self.device_info.sample_freq
        if self.data_buffer.shape[1] >= required_samples:
            # 提取满1秒的数据
            data_to_write = self.data_buffer[:, :required_samples]
            self.data_buffer = self.data_buffer[:, required_samples:]
            
            # 转换为微伏并写入文件
            sample_list = [data_to_write[i, :] * 1e6 for i in range(data_to_write.shape[0])]
            self.record_file.writeSamples(sample_list)

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
            self.status_bar.showMessage(f"Data saved: {self.record_file_name}")

    def connect_eeg_stream(self, deviceInfo):
        """Connect to an EEG data stream"""
        self.device_info = deviceInfo
        real_freq = deviceInfo.sample_freq
        indicator_cfg_freq = Indicator_Globals.stream_freq

        if real_freq != indicator_cfg_freq:
            self.status_bar.showMessage(f"Before using {self.device_info.name}, please change setting to this [ "
                                        f" indicators/__Indicator_Global_Cfg.py: stream_freq={real_freq}]")
            return

        try:
            stream_list = resolve_streams(stype='EEG') + resolve_streams(stype='eeg')
            if not stream_list:
                self.status_bar.showMessage("didn't find any streams")
                return

            sinfo = stream_list[0]
            self.stream = StreamLSL(bufsize=1, name=sinfo.name, stype=sinfo.stype, source_id=sinfo.source_id)
            self.stream.connect()
            self.stream.pick("eeg")

            self.start_timer()
            self.status_bar.showMessage(f"connected to {deviceInfo.channel_picks}")

        except Exception as e:
            traceback.print_exc()
            self.status_bar.showMessage("stream connection failed")

    def disconnect_stream(self):
        """Disconnect the EEG data stream"""
        if self.stream:
            self.stream.disconnect()

    def start_timer(self):
        """Start a timer"""
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.check_newdata_and_process)
        self.timer.start(30)  # Update every 30 ms

    def check_newdata_and_process(self):
        """Periodically update the display and save the latest data"""
        try:
            if self.stream.n_new_samples < 1:
                return

            data, _ = self.get_new_data_from_stream()

            if data is not None:
                # Display data from the selected channels
                selected_channel_data = data
                # Update the specified channel in the graphical interface
                for handler in self.main_window.loaded_indicators:
                    handler.process_new_data_and_update_plot(selected_channel_data)

                # If recording, save data from all channels
                if self.recording and self.record_file:
                    self.save_data_to_file(data)
        except Exception as e:
            traceback.print_exc()
            self.status_bar.showMessage("failed to process new data")

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
