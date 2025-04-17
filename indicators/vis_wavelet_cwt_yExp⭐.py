from typing import override
import numpy as np
import pyqtgraph as pg
import pywt
from __BaseIndicator import BaseIndicatorHandler


class WaveletCWT_Handler(BaseIndicatorHandler):
    @override
    def __init__(self):
        super().__init__(indicator_update_interval=2)

        # Initialize the heatmap data
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
        bottom_txt = f"Timeline Frames (1 Frame = {self.indicator_update_interval} Seconds)"
        plot_item.setLabel("bottom", bottom_txt)
        plot_item.setLabel("left", "Frequency (Hz, Log Scale)")

        # Initialize heatmap data
        self.heatmap_widget.setImage(self.grey_heatmap_data, autoLevels=True)

        # Create a green colormap
        green_cmap = pg.ColorMap(
            pos=[0.0, 1.0],  # Define the positions for the color mapping (0 = min value, 1 = max value)
            color=[(0, 0, 0), (0, 255, 0)]  # From black (0, 0, 0) to green (0, 255, 0)
        )
        lut = green_cmap.getLookupTable(nPts=256)  # Get the lookup table for the colormap
        self.heatmap_widget.setLookupTable(lut)  # Apply the colormap
        self.heatmap_widget.setLevels((0, 1))  # Set the data range (0 to 1)

        # Set y-axis tick labels (log scale)
        self.frequencies = np.logspace(np.log10(1), np.log10(self.num_frequencies), self.num_frequencies)  # From 1Hz to 128Hz
        y_ticks = self._generate_log_ticks(self.frequencies)
        plot_item.getAxis("left").setTicks([y_ticks])

        # Add dashed lines for brainwave frequency bands
        self._add_brainwave_lines(plot_item, self.frequencies)
        
        # Add text item to display current dominant frequency
        self.dominant_freq_text = pg.TextItem(text="Peak: -- Hz", color="white", anchor=(0, 0))
        self.dominant_freq_text.setPos(2, 2)  # Position in the top-left area of plot
        plot_item.addItem(self.dominant_freq_text)

        return self.plot_layout

    def _generate_log_ticks(self, frequencies):
        """
        Generate y-axis tick labels for a logarithmic scale
        :param frequencies: Frequency points on a logarithmic scale
        :return: List of ticks in the format [(index, label), ...]
        """
        # Select a subset of tick points to avoid overcrowding
        num_ticks = 10  # Number of ticks to display
        tick_indices = np.linspace(0, len(frequencies) - 1, num_ticks, dtype=int)
        tick_labels = [f"{frequencies[i]:.1f}" for i in tick_indices]

        # Return the tick list
        return list(zip(tick_indices, tick_labels))

    def _add_brainwave_lines(self, plot_item, frequencies):
        """
        Add dashed lines to the plot area to indicate boundaries of different brainwave frequency bands
        :param plot_item: The plot area (plot_item)
        :param frequencies: Frequencies on a logarithmic scale
        """
        # Define brainwave frequency band boundaries
        brainwave_bands = {
            "Delta": 4,  # Delta upper limit: 4 Hz
            "Theta": 8,  # Theta upper limit: 8 Hz
            "Alpha": 13,  # Alpha upper limit: 13 Hz
            "Beta": 30,  # Beta upper limit: 30 Hz
            "Gamma": self.num_frequencies  # Gamma upper limit: 128 Hz
        }

        # Find the corresponding index for each frequency in the logarithmic scale
        for freq_label, freq in brainwave_bands.items():
            # Get the closest index to the frequency
            index = np.abs(frequencies - freq).argmin()

            # Add a dashed line to the plot area (with updated dashed line style)
            # line = pg.InfiniteLine(pos=index, angle=0, pen=pg.mkPen('grey', dash=[14, 10], width=1))
            # plot_item.addItem(line)

            # Add a text label
            text = pg.TextItem(text=f"--------\n{freq_label}", color='white', anchor=(0.5, 0.3))  # Text label
            text.setPos(self.heatmap_columns - 1, index)  # Position it on the right side of the heatmap
            plot_item.addItem(text)

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
        sampling_rate = self.stream_sample_freq  # Assume a sampling rate of 256 Hz

        # Use the frequencies defined in create_pyqtgraph_plotWidget
        # No need to regenerate them here

        # Compute the corresponding scales
        scales = pywt.scale2frequency(self.wavelet, self.frequencies) * sampling_rate

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
        compressed_column = np.mean(new_column, axis=1)  # Compress to 1D

        # Roll the grey_heatmap_data to update the leftmost column
        self.grey_heatmap_data = np.roll(self.grey_heatmap_data, shift=-1, axis=1)

        # Insert the new column (latest data at the rightmost position)
        self.grey_heatmap_data[:, -1] = compressed_column
        
        # Find the highest power frequency
        max_index = np.argmax(compressed_column)
        dominant_freq = self.frequencies[max_index]
        
        # Update text with the current dominant frequency
        self.dominant_freq_text.setText(f"Peak: {dominant_freq:.1f} Hz")

        # Update the heatmap display
        self.heatmap_widget.setImage(self.grey_heatmap_data, autoLevels=False, levels=(0, 1))


if __name__ == '__main__':
    indicator = WaveletCWT_Handler()
    indicator.test_current_indicator_with_simulated_data()
