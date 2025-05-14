from typing import override

import numpy as np
import pyqtgraph as pg

# Inherit from the base class
from __BaseIndicator import BaseIndicatorHandler
from __bands.WaveBands_Utils import Bands_Utils

class BandPowerRatio_Wave_Handler(BaseIndicatorHandler):
    @override
    def __init__(self):
        super().__init__(indicator_update_interval=2)  # Update every 2 seconds
        self.max_epochs_to_show = 120  # Show up to the most recent 60 epochs

        self.bands_utils = Bands_Utils(5)  # Use 5 brainwave frequency bands

        # Create PyQtGraph graphical layout
        self.plot_widget = None

        # Initialize the cache
        self.bandpwr_percent_data = (  # Cache the power proportion for each frequency band
            np.zeros((self.max_epochs_to_show, self.bands_utils.num_bands)))

        self.band_curves = []  # Store the curve for each frequency band

    @override
    def create_pyqtgraph_plotWidget(self):
        """Create a plot widget to display the power variation of brainwave frequency bands"""
        self.plot_widget = pg.GraphicsLayoutWidget()
        self.plot_widget.setWindowTitle("Real-time Brainwave Frequency Band Power Curves")

        # Create the plot
        plot_item = self.plot_widget.addPlot(title="Power Proportions of Brainwave Frequency Bands")
        bottom_txt = f"TimeSeries (Update Interval = {self.indicator_update_interval} Seconds)"
        plot_item.setLabel("bottom", bottom_txt)
        plot_item.setLabel("left", "Power Intensity")
        plot_item.showGrid(x=True, y=True)
        plot_item.addLegend()

        # Create a curve for each frequency band (with different colors)
        colors = self.bands_utils.colors
        self.band_curves = [
            plot_item.plot(pen=pg.mkPen(color=color, width=2), name=band)
            for band, color in zip(self.bands_utils.bands.keys(), colors)
        ]
        return self.plot_widget

    @override
    def process_1_interval_rawdata_and_update_plot(self, interval_data):
        total_power, band_powers_percentage = (
            self.bands_utils.calc_bandpwr_percentage(interval_data, self.stream_sample_freq))

        # Roll and store power data
        self.bandpwr_percent_data = np.roll(self.bandpwr_percent_data, -1, axis=0)
        self.bandpwr_percent_data[-1, :] = band_powers_percentage

        # Update the power plot
        self.update_power_plot()

    def update_power_plot(self):
        """Update the display of the power curves"""
        x_data = np.arange(self.max_epochs_to_show)  # X-axis corresponds to epoch indices
        for i, curve in enumerate(self.band_curves):
            curve.setData(x_data, self.bandpwr_percent_data[:, i])  # Each curve corresponds to the power data of one frequency band


if __name__ == '__main__':
    indicator = BandPowerRatio_Wave_Handler()
    indicator.test_current_indicator_with_simulated_data()
