from typing import override
import numpy as np
import pyqtgraph as pg
import pywt
from __BaseIndicator import BaseIndicatorHandler


class WaveletCWT_Handler(BaseIndicatorHandler):
    @override
    def __init__(self):
        super().__init__(indicator_update_interval=2)

        # Initialize heatmap data
        self.num_frequencies = 128  # Frequency resolution (number of scales in CWT)
        self.heatmap_columns = 60  # Time window width (number of columns) for the heatmap
        self.grey_heatmap_data = np.zeros((self.num_frequencies, self.heatmap_columns), dtype=np.float32)  # Single-channel grayscale

        # Select wavelet
        self.wavelet = 'cmor1.5-1.0'  # Define Morse wavelet with bandwidth and center frequency
        self.init_completed = True

    @override
    def create_pyqtgraph_plotWidget(self):
        # Create the heatmap display window
        self.plot_layout = pg.GraphicsLayoutWidget()
        self.plot_layout.setWindowTitle("Real-time CWT Heatmap")

        # Create heatmap
        self.heatmap_widget = pg.ImageItem(axisOrder='row-major')
        plot_item = self.plot_layout.addPlot(row=0, col=0)  # Add the heatmap to the layout
        plot_item.addItem(self.heatmap_widget)
        bottom_txt = f"Timeline Epochs (1 Epoch = {self.indicator_update_interval} Seconds)"
        plot_item.setLabel("bottom", bottom_txt)
        plot_item.setLabel("left", "Frequency (Hz)")

        # Initialize heatmap with data
        self.heatmap_widget.setImage(self.grey_heatmap_data, autoLevels=True)

        # Create a green colormap
        green_cmap = pg.ColorMap(
            pos=[0.0, 1.0],  # Define the positions for the color mapping (0 = min value, 1 = max value)
            color=[(0, 0, 0), (0, 255, 0)]  # From black (0, 0, 0) to green (0, 255, 0)
        )
        lut = green_cmap.getLookupTable(nPts=256)  # Get the lookup table for the colormap
        self.heatmap_widget.setLookupTable(lut)  # Apply the colormap
        self.heatmap_widget.setLevels((0, 1))  # Set the data range (0 to 1)

        return self.plot_layout

    @override
    def process_1_interval_rawdata_and_update_plot(self, interval_data):
        # Perform Continuous Wavelet Transform (CWT)
        cwt_spectrum = self.compute_cwt(interval_data)

        # Update the heatmap
        self.update_heatmap(cwt_spectrum)

    def compute_cwt(self, signal):
        """
        Perform Continuous Wavelet Transform (CWT) to analyze the signal in the time-frequency domain
        :param signal: Input signal (1D array)
        :return: Spectrum intensity from the CWT (2D array)
        """
        # Define the range of wavelet scales to cover the frequency range
        sampling_rate = self.stream_sample_freq  # Assume sampling rate is 256 Hz
        frequencies = np.linspace(1, self.num_frequencies, self.num_frequencies)
        scales = pywt.scale2frequency(self.wavelet, frequencies) * sampling_rate

        # Perform the CWT using pywt.cwt
        cwt_coefficients, _ = pywt.cwt(signal, scales, self.wavelet, sampling_period=1/sampling_rate)

        # Compute spectrum intensity (absolute values)
        spectrum_intensity = np.abs(cwt_coefficients)

        # Normalize to the range [0, 1]
        normalized_intensity = spectrum_intensity / np.max(spectrum_intensity)
        return normalized_intensity

    def update_heatmap(self, new_column):
        """
        Perform a rolling update of the heatmap data
        :param new_column: Spectrum intensity data from the CWT (2D array)
        """
        compressed_column = np.mean(new_column, axis=1)  # Compress to 1D (average across the axis)

        # Roll the grey_heatmap_data to update the leftmost column
        self.grey_heatmap_data = np.roll(self.grey_heatmap_data, shift=-1, axis=1)

        # Insert the new column (latest data at the rightmost position)
        self.grey_heatmap_data[:, -1] = compressed_column

        # Update the heatmap display
        self.heatmap_widget.setImage(self.grey_heatmap_data, autoLevels=False, levels=(0, 1))

if __name__ == '__main__':
    indicator = WaveletCWT_Handler()
    indicator.test_current_indicator_with_simulated_data()
