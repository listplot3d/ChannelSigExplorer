import itertools
import logging
import sys
from pathlib import Path 
import yaml  

import numpy as np
from pyqtgraph.Qt import QtWidgets, QtCore

from __Data_IO_Utils import DataMgr_Raw_In_Intervals, DataMgr_Wave_In_1D
from __bands.WaveBands_Utils import Bands_Utils

class BaseIndicatorHandler:


    def __init__(self, indicator_update_interval, indicator_wave_columns=None):        
        config_path = Path(__file__).parent / 'indicator_global_config.yaml'
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        logging.basicConfig(level=config['LOGGING']['level'], format=config['LOGGING']['log_format'])

        self.stream_sample_freq = config['STREAM']['sample_freq']

        self.plot_widget = None  # Plotting widget
        self.plotted_wave = None  # Curve

        """
        For most indicators displayed in the plot, raw data is not directly shown.
        Instead, raw data is divided into intervals. Each interval is used to
        compute the indicator once, and the indicator results are then updated on the plot.
        """
        self.indicator_update_interval = indicator_update_interval
        interval_rawdata_len = int(self.stream_sample_freq * indicator_update_interval)

        # Group raw data into intervals and store
        self.intervalsData_mgr = (
            DataMgr_Raw_In_Intervals(one_interval_data_len=interval_rawdata_len, num_intervals=2))

        # indicator_data_in_1d is not required for every indicator
        if indicator_wave_columns is not None:
            self.waveDataIn1D_mgr = DataMgr_Wave_In_1D(indicator_wave_columns)
            
        # 离线模式相关属性
        self.is_offline_mode = False
        self.offline_data = None
        self.current_position = 0

    def create_pyqtgraph_plotWidget(self):
        raise NotImplementedError

    def process_1_interval_rawdata_and_update_plot(self, interval_data):
        raise NotImplementedError

    def process_new_data_and_update_plot(self, data_arrived):
        """
        Update real-time waveform
        :param data_arrived: Newly received EEG data
        """
        # Update buffer
        interval_data = self.intervalsData_mgr.append_new_data_and_return_1st_filled_row(data_arrived)

        if interval_data is not None:
            self.process_1_interval_rawdata_and_update_plot(interval_data)
            self.intervalsData_mgr.delete_1st_filled_row()
            
    def test_current_indicator_with_simulated_data(self):
        """
        Test the current real-time waveform processing module.
        - Create a plotting window.
        - Simulate a 256Hz real-time signal data stream.
        - Update the plot and display it.
        """
        # Create PyQt application instance
        app = QtWidgets.QApplication([])

        # Create main window
        win = QtWidgets.QMainWindow()
        win.setWindowTitle("Testing Indicator: " + self.__class__.__name__)
        win.resize(800, 600)

        # Create plotting area
        plot_widget = self.create_pyqtgraph_plotWidget()

        # Add plotting area to the window
        dock = QtWidgets.QDockWidget("", win)
        dock.setWidget(plot_widget)
        win.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, dock)
        win.show()

        """ Simulation signal parameters """
        signal_duration = 5  # Duration of a single signal cycle (seconds)

        # Define brainwave frequency band parameters (frequency range and amplitude)

        # Convert frequency band parameters to a list
        wave_params = [
            {'name': name, 'freq': (start + end) / 2, 'amp': 0.5, 'target_amp': 0.5, 'change_speed': 0.05}
            for name, info in Bands_Utils.BRAIN_WAVES_BANDS["8_bands"].items()
            for start, end in [info["range"]]
        ]

        # Time counter and amplitude update interval (in seconds)
        time_counter = 0
        amplitude_update_interval = 2  # Update target amplitude every 2 seconds

        def generate_dynamic_signal():
            nonlocal time_counter
            t = time_counter / self.stream_sample_freq  # Current time (in seconds)

            # Generate dynamic signal
            signal_value = 0.0
            for wave in wave_params:
                # Smoothly transition to target amplitude
                wave['amp'] += (wave['target_amp'] - wave['amp']) * wave['change_speed']

                # Generate a waveform for the current frequency band
                signal_value += wave['amp'] * np.sin(2 * np.pi * wave['freq'] * t)

            # Update time counter and target amplitude
            time_counter += 1
            if t % amplitude_update_interval < (1 / self.stream_sample_freq):  # Avoid frequent updates
                for wave in wave_params:
                    wave['target_amp'] = np.random.uniform(0.1, 0.9)  # Generate new random target amplitude

            return signal_value

        # Use a generator to dynamically generate the signal
        signal_iterator = itertools.cycle(iter(generate_dynamic_signal, None))

        # Use a timer to update the plot
        timer = QtCore.QTimer()
        timer.timeout.connect(lambda: self.process_new_data_and_update_plot(next(signal_iterator)))
        timer.start(int(1000 / self.stream_sample_freq))

        # Run the application
        sys.exit(app.exec())


if __name__ == '__main__':
    print("This is BaseIndicator for inheritance, and it's not supposed to run")
