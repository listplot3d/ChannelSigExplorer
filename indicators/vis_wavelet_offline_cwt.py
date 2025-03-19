from typing import override

import numpy as np
import pyqtgraph as pg
from scipy import signal
from __BaseIndicator import BaseIndicatorHandler

class Offline_Wavelet_CWT_Handler(BaseIndicatorHandler):
    """Continuous Wavelet Transform frequency analysis indicator for offline mode"""

    @override
    def __init__(self):
        super().__init__(indicator_update_interval=1, indicator_wave_columns=None)
        self.window_size = 10  # Analysis window size (seconds)
        self.position_line = None  # Current position line
        self.cwt_result = None  # Store the continuous wavelet transform results
        self.freqs = None  # Frequency range
        self.times = None  # Time range
        
        # Set frequency range (logarithmic distribution)
        self.min_freq = 1  # Minimum frequency (Hz)
        self.max_freq = 50  # Maximum frequency (Hz)
        self.num_freqs = 50  # Number of frequency points

    @override
    def create_pyqtgraph_plotWidget(self):
        """
        Create and return the plotting widget for offline continuous wavelet transform
        :return: PlotWidget object
        """
        self.plot_widget = pg.PlotWidget(title="Offline Continuous Wavelet Transform Analysis")
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabels(left='Frequency (Hz)', bottom='Time (s)')
        
        # Create image item for displaying the time-frequency plot
        self.img_item = pg.ImageItem()
        self.plot_widget.addItem(self.img_item)
                
        # Add color bar
        self.colorbar = pg.ColorBarItem(
            values=(0, 1),
            colorMap=pg.colormap.get("viridis"),
            label="Energy"
        )
        self.colorbar.setImageItem(self.img_item)
        
        # Create current position line
        self.position_line = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen('r', width=2))
        self.plot_widget.addItem(self.position_line)
        
        # Add frequency band markers
        self.add_frequency_bands()
        
        return self.plot_widget
    
    def add_frequency_bands(self):
        """Add brain wave frequency band markers"""
        # Define brain wave frequency bands
        bands = [
            {"name": "δ (Delta)", "range": (0.5, 4)},
            {"name": "θ (Theta)", "range": (4, 8)},
            {"name": "α (Alpha)", "range": (8, 13)},
            {"name": "β (Beta)", "range": (13, 30)},
            {"name": "γ (Gamma)", "range": (30, 50)}
        ]
        
        # Add horizontal lines and text labels for each frequency band
        for band in bands:
            # Add upper and lower limit lines
            for freq in band["range"]:
                if self.min_freq <= freq <= self.max_freq:
                    line = pg.InfiniteLine(pos=freq, angle=0, pen=pg.mkPen('w', width=1, style=pg.QtCore.Qt.PenStyle.DashLine))
                    self.plot_widget.addItem(line)
            
            # Add text labels
            mid_freq = (band["range"][0] + band["range"][1]) / 2
            if self.min_freq <= mid_freq <= self.max_freq:
                text = pg.TextItem(text=band["name"], color="w", anchor=(0, 0.5))
                text.setPos(0, mid_freq)
                self.plot_widget.addItem(text)

    @override
    def process_offline_data_and_update_plot(self, full_data, current_position):
        """
        Process offline data and update the continuous wavelet transform plot
        :param full_data: Complete channel data
        :param current_position: Current time position (sample index)
        """
        self.is_offline_mode = True
        self.offline_data = full_data
        self.current_position = current_position
        
        # Calculate the number of samples for the analysis window
        window_samples = int(self.window_size * self.stream_sample_freq)
        half_window = window_samples // 2
        
        # Calculate window start and end positions
        start_pos = max(0, current_position - half_window)
        end_pos = min(len(full_data), start_pos + window_samples)
        
        # Adjust start position to ensure consistent window size
        if end_pos - start_pos < window_samples:
            start_pos = max(0, end_pos - window_samples)
        
        # Extract the data segment to analyze
        if end_pos > start_pos:
            segment_data = full_data[start_pos:end_pos]
            
            # Calculate continuous wavelet transform (if not already calculated or data segment changed)
            if self.cwt_result is None or len(self.cwt_result[0]) != len(segment_data):
                self.compute_cwt(segment_data, start_pos)
            
            # Update current position line
            current_time = current_position / self.stream_sample_freq
            self.position_line.setValue(current_time)
    
    def compute_cwt(self, data, start_pos):
        """
        Compute continuous wavelet transform
        :param data: Input data
        :param start_pos: Start position of the data segment (sample index)
        """
        # Generate logarithmically distributed frequency range
        self.freqs = np.logspace(np.log10(self.min_freq), np.log10(self.max_freq), self.num_freqs)
        
        # Calculate continuous wavelet transform
        scales = self.stream_sample_freq / (2 * self.freqs * np.pi)
        self.cwt_result = signal.cwt(data, signal.morlet2, scales)
        
        # Calculate time axis
        self.times = np.arange(start_pos, start_pos + len(data)) / self.stream_sample_freq
        
        # Calculate energy (square of amplitude)
        cwt_power = np.abs(self.cwt_result) ** 2
        
        # Normalize energy
        cwt_power_norm = (cwt_power - cwt_power.min()) / (cwt_power.max() - cwt_power.min() + 1e-10)
        
        # Update image
        self.img_item.setImage(cwt_power_norm)
        
        # Set image position and scale
        rect = pg.QtCore.QRectF(self.times[0], self.freqs[0], self.times[-1] - self.times[0], self.freqs[-1] - self.freqs[0])
        self.img_item.setRect(rect)
        
        # Update color bar
        self.colorbar.setLevels((cwt_power_norm.min(), cwt_power_norm.max()))
        
        # Set Y-axis to logarithmic scale
        self.plot_widget.setLogMode(y=True)
        self.plot_widget.setYRange(np.log10(self.min_freq), np.log10(self.max_freq))

    @override
    def process_1_interval_rawdata_and_update_plot(self, interval_data):
        """
        Data processing method for real-time mode
        This won't be directly called in offline mode
        """
        if not self.is_offline_mode:
            # Continuous wavelet transform processing in real-time mode
            # Simplified implementation, only processing current interval data
            self.compute_cwt(interval_data, 0)


if __name__ == '__main__':
    indicator = Offline_Wavelet_CWT_Handler()
    indicator.test_current_indicator_with_simulated_data()
