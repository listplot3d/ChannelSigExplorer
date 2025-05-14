from typing import override
import numpy as np
import pyqtgraph as pg
from __BaseIndicator import BaseIndicatorHandler
from __bands.WaveBands_Utils import Bands_Utils

class BandPowerRatio_Sigma_Handler(BaseIndicatorHandler):
    @override
    def __init__(self):
        super().__init__(indicator_update_interval=2)
        self.max_epochs_to_show = 120
        
        # Use 8-band configuration which includes Sigma wave (11-16Hz)
        self.bands_utils = Bands_Utils(6)
        
        # Initialize data buffer
        self.bandpwr_percent_data = np.zeros((self.max_epochs_to_show, self.bands_utils.num_bands))
        self.band_curves = []

    @override
    def create_pyqtgraph_plotWidget(self):
        self.plot_widget = pg.GraphicsLayoutWidget()
        self.plot_widget.setWindowTitle("Sigma Band (11-16Hz) Power Ratio")
        
        plot_item = self.plot_widget.addPlot(title="Sigma Band Power Ratio")
        bottom_txt = f"TimeSeries (Update Interval = {self.indicator_update_interval} Seconds)"
        plot_item.setLabel("bottom", bottom_txt)
        plot_item.setLabel("left", "Power Intensity")
        plot_item.showGrid(x=True, y=True)
        plot_item.addLegend()

        # Get colors for all frequency bands
        colors = self.bands_utils.colors
        bands = list(self.bands_utils.bands.keys())
        
        # Create curve only for Sigma band
        sigma_index = bands.index("Sigma")  # Assuming 8-band config includes Sigma wave
        self.band_curves = [
            plot_item.plot(pen=pg.mkPen(color=colors[sigma_index], width=2), name="Sigma (11-16Hz)")
        ]
        
        return self.plot_widget

    @override
    def process_1_interval_rawdata_and_update_plot(self, interval_data):
        total_power, band_powers_percentage = (
            self.bands_utils.calc_bandpwr_percentage(interval_data, self.stream_sample_freq))
        
        # Roll and update data buffer
        self.bandpwr_percent_data = np.roll(self.bandpwr_percent_data, -1, axis=0)
        self.bandpwr_percent_data[-1, :] = band_powers_percentage
        
        # Update plot
        self.update_power_plot()

    def update_power_plot(self):
        """Display only Sigma band power"""
        x_data = np.arange(self.max_epochs_to_show)
        sigma_index = list(self.bands_utils.bands.keys()).index("Sigma")
        
        if self.band_curves:
            self.band_curves[0].setData(x_data, self.bandpwr_percent_data[:, sigma_index])

if __name__ == '__main__':
    indicator = BandPowerRatio_Sigma_Handler()
    indicator.test_current_indicator_with_simulated_data()