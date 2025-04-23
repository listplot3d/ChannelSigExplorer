from typing import override

import numpy as np
import pyqtgraph as pg
from __BaseIndicator import BaseIndicatorHandler

class PowerSpectrumHandler_Wave(BaseIndicatorHandler):
    @override
    def __init__(self):
        super().__init__(indicator_update_interval=1)

    @override
    def create_pyqtgraph_plotWidget(self):
        self.plot_widget = pg.PlotWidget(title="Power Spectrum")
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabels(left='Power', bottom='Frequency (Hz)')
        self.plot_widget.setLogMode(x=False, y=True)
        self.plotted_wave = self.plot_widget.plot(pen='y')  # 曲线
        self.add_frequency_bands()

        return self.plot_widget

    def add_frequency_bands(self):
        """Add EEG frequency band marking regions."""
        # Define EEG frequency bands and their colors
        bands = [
            {"name": "δ", "range": (0.5, 4), "color": (100, 100, 255, 50)},
            {"name": "θ", "range": (4, 8), "color": (100, 255, 100, 50)},
            {"name": "α", "range": (8, 13), "color": (255, 100, 100, 50)},
            {"name": "β", "range": (13, 30), "color": (255, 255, 100, 50)},
            {"name": "γ", "range": (30, 100), "color": (255, 100, 255, 50)}
        ]
        
        # Add marking regions and text labels for each frequency band
        self.band_regions = []
        for band in bands:
            # Create region for each frequency band
            region = pg.LinearRegionItem(
                values=band["range"],
                brush=pg.mkBrush(band["color"]),
                movable=False
            )
            self.plot_widget.addItem(region)
            self.band_regions.append(region)
            
            # Add text label for each band
            text = pg.TextItem(text=band["name"], color="w", anchor=(0.5, 1))
            # Set the text at the center x of the band, but fix y at a constant value (e.g., y=5)
            text.setPos((band["range"][0] + band["range"][1]) / 2, 5)
            self.plot_widget.addItem(text)

    @override
    def process_1_interval_rawdata_and_update_plot(self, interval_data):
        fft_data = np.fft.fft(interval_data)
        power_spectrum = np.abs(fft_data[:len(fft_data) // 2]) ** 2
        freqs = np.fft.fftfreq(len(interval_data), d=1.0 / self.stream_sample_freq)
        freqs = freqs[:len(freqs) // 2]

        self.plotted_wave.setData(freqs, power_spectrum)



if __name__ == '__main__':
    indicator = PowerSpectrumHandler_Wave()
    indicator.test_current_indicator_with_simulated_data()