from typing import override

import numpy as np
import pyqtgraph as pg
from __BaseIndicator import BaseIndicatorHandler

class Offline_Waveform_View_Handler(BaseIndicatorHandler):
    """Offline waveform display indicator"""

    @override
    def __init__(self):
        # Use a larger data column count to display more data points
        super().__init__(indicator_update_interval=10, indicator_wave_columns=5000)
        self.view_window_size = 10  # Display 10 seconds of data
        self.vertical_range = None  # Vertical range auto-adjusts

    @override
    def create_pyqtgraph_plotWidget(self):
        """
        Create and return the plotting widget for offline waveform display
        :return: PlotWidget object
        """
        self.plot_widget = pg.PlotWidget(title="Offline Waveform Display")
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabels(left='Amplitude (μV)', bottom='Time (s)')
        self.plot_widget.getViewBox().setMouseEnabled(x=True, y=False)

        # Create two curves: one for the waveform, one for the current position marker
        self.plotted_wave = self.plot_widget.plot(pen='y')  # Waveform curve
        self.position_marker = self.plot_widget.plot(pen=pg.mkPen('r', width=2))  # Position marker
        
        return self.plot_widget

    @override
    def process_offline_data_and_update_plot(self, full_data, current_position):
        """
        Process offline data and update the plot
        :param full_data: Complete channel data
        :param current_position: Current time position (sample index)
        """
        self.is_offline_mode = True
        self.offline_data = full_data
        self.current_position = current_position
        
        # Calculate the data window to display
        window_samples = int(self.view_window_size * self.stream_sample_freq)
        half_window = window_samples // 2
        
        # Calculate window start and end positions
        start_pos = max(0, current_position - half_window)
        end_pos = min(len(full_data), start_pos + window_samples)
        
        # Adjust start position to ensure consistent window size
        if end_pos - start_pos < window_samples:
            start_pos = max(0, end_pos - window_samples)
        
        # Extract the data segment to display
        if end_pos > start_pos:
            view_data = full_data[start_pos:end_pos]
            
            # Calculate time axis
            time_axis = np.arange(start_pos, end_pos) / self.stream_sample_freq
            
            # Update waveform curve
            self.plotted_wave.setData(time_axis, view_data)
            
            # Update current position marker (vertical line)
            current_time = current_position / self.stream_sample_freq
            y_range = self.plot_widget.getViewBox().viewRange()[1]  # Get current Y-axis range of the view
            self.position_marker.setData(
                [current_time, current_time],  # X coordinates (vertical line)
                y_range  # Y coordinate range
            )
            
            # Auto-adjust Y-axis range (first display or when a new channel is selected)
            if self.vertical_range is None:
                data_min, data_max = np.min(view_data), np.max(view_data)
                data_range = data_max - data_min
                # Add 10% margin
                self.vertical_range = [data_min - 0.1 * data_range, data_max + 0.1 * data_range]
                self.plot_widget.setYRange(*self.vertical_range)

    @override
    def process_1_interval_rawdata_and_update_plot(self, interval_data):
        """
        Data processing method for real-time mode
        This won't be directly called in offline mode, but will be indirectly called by process_offline_data_and_update_plot
        """
        if not self.is_offline_mode:
            # Processing method in real-time mode
            # Calculate time axis
            time_axis = np.arange(len(interval_data)) / self.stream_sample_freq
            # Update curve
            self.plotted_wave.setData(time_axis, interval_data)


if __name__ == '__main__':
    indicator = Offline_Waveform_View_Handler()
    indicator.test_current_indicator_with_simulated_data()
