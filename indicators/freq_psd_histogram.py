from typing import override

import numpy as np
import pyqtgraph as pg

from __BaseIndicator import BaseIndicatorHandler

class PowerSpectrum_Handler_Histogram(BaseIndicatorHandler):
    @override
    def __init__(self):
        super().__init__(indicator_update_interval=2)
        self.bar_item = None  # Used to store the current bar chart object

    @override
    def create_pyqtgraph_plotWidget(self):
        self.plot_widget = pg.PlotWidget(title="Power Spectrum")
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabels(left='Power', bottom='Frequency (Hz)')
        self.plot_widget.setLogMode(x=False, y=True)
        return self.plot_widget

    @override
    def process_1_interval_rawdata_and_update_plot(self, interval_data):
        # Compute the power spectrum
        fft_data = np.fft.fft(interval_data)
        power_spectrum = np.abs(fft_data[:len(fft_data) // 2]) ** 2
        power_spectrum = np.log10(power_spectrum + 1e-8)  # Convert to a logarithmic scale to avoid log(0) issues
        freqs = np.fft.fftfreq(len(interval_data), d=1.0 / self.stream_sample_freq)
        freqs = freqs[:len(freqs) // 2]

        # Clear the old bar chart
        if self.bar_item is not None:
            self.plot_widget.removeItem(self.bar_item)

        # Plot the power spectrum using a bar chart
        self.bar_item = pg.BarGraphItem(x=freqs, height=power_spectrum, width=0.5, brush='b')
        # self.plot_widget.setYRange(-2, 5)  # Adjust the y-range based on the actual power spectrum range
        self.plot_widget.addItem(self.bar_item)

if __name__ == '__main__':
    indicator = PowerSpectrum_Handler_Histogram()
    indicator.test_current_indicator_with_simulated_data()
