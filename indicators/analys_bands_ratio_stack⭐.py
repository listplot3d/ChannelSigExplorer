from typing import override

import numpy as np
import pyqtgraph as pg

# Inherit from the base class
from __BaseIndicator import BaseIndicatorHandler
from __bands.WaveBands_Utils import Bands_Utils

class BandPowerRatio_Stack_Handler(BaseIndicatorHandler):
    @override
    def __init__(self):
        super().__init__(indicator_update_interval=2)
        self.max_epochs_to_show = 60  # Maximum of 60 recent epochs to display

        self.bands_utils = Bands_Utils(5)  # Use N brainwave frequency bands

        # Create a PyQtGraph layout
        self.plot_widget = None

        # Initialize the buffer
        self.bandpwr_percent_data = np.zeros((self.max_epochs_to_show, self.bands_utils.num_bands))  # Cache the power percentages for each band

        self.fill_plots = []  # Store the filled regions for each band
        self.curves = []  # Store the boundary lines for each band

    @override
    def create_pyqtgraph_plotWidget(self):
        """Create a stacked plot to display the power intensity of brainwave bands."""
        self.plot_widget = pg.GraphicsLayoutWidget()
        self.plot_widget.setWindowTitle("Real-Time Brainwave Band Power Intensity Stacked Plot (Filled)")

        # Create the plot
        plot_item = self.plot_widget.addPlot(title="Brainwave Band Power Ratios (Stacked Display)")
        bottom_txt = f"Time Epochs (1 Epoch = {self.indicator_update_interval} Seconds)"
        plot_item.setLabel("bottom", bottom_txt)
        plot_item.setLabel("left", "Power Intensity")
        plot_item.showGrid(x=True, y=True)

        # Create a legend and position it in the top-left corner
        legend = pg.LegendItem(offset=(10, 10))  # Offset of (10, 10) means 10 pixels from the top-left corner
        legend.setParentItem(plot_item.vb)  # Bind the legend to the ViewBox of the plot area

        # Get the color for each band
        colors = self.bands_utils.colors

        for band, color in zip(self.bands_utils.bands.keys(), colors):
            # Add a transparent filled region
            fill = pg.FillBetweenItem(None, None, brush=pg.mkBrush(color + "90"))
            self.fill_plots.append(fill)
            plot_item.addItem(fill)

            # Add a boundary line for each band (ensure it's of type PlotDataItem)
            curve = plot_item.plot(pen=pg.mkPen(color=color, width=2), name=band)
            self.curves.append(curve)

            # Add the current band to the legend
            legend.addItem(curve, band)

        return self.plot_widget

    @override
    def process_1_interval_rawdata_and_update_plot(self, interval_data):
        """Process the data and update the stacked plot."""
        # Compute the power percentage for each band
        total_power, band_powers_percentage = (
            self.bands_utils.calc_bandpwr_percentage(interval_data, self.stream_sample_freq))

        # Roll and store the power data
        self.bandpwr_percent_data = np.roll(self.bandpwr_percent_data, -1, axis=0)
        self.bandpwr_percent_data[-1, :] = band_powers_percentage

        # Update the stacked plot
        self.update_stack_plot()

    def update_stack_plot(self):
        """Update the display of the stacked plot."""
        x_data = np.arange(self.max_epochs_to_show)  # X-axis represents the epoch indices
        cumulative_data = np.zeros(self.max_epochs_to_show)  # For cumulative stacking calculations

        # Update the data for each band
        for i, (fill, curve) in enumerate(zip(self.fill_plots, self.curves)):
            # Update the boundary line
            y_data = cumulative_data + self.bandpwr_percent_data[:, i]
            curve.setData(x_data, y_data)

            # Update the filled region
            if i == 0:
                # The first band uses 0 as the lower boundary
                fill.setCurves(pg.PlotDataItem(x_data, np.zeros_like(x_data)), curve)
            else:
                # Other bands use the previous band's upper boundary
                fill.setCurves(self.curves[i - 1], curve)

            # Update the cumulative value
            cumulative_data = y_data

        # Dynamically adjust the Y-axis range
        max_power = np.sum(self.bandpwr_percent_data, axis=1).max()  # Maximum power after stacking
        min_power = 0  # The minimum power of the stacked plot is 0
        if self.curves:
            self.curves[0].getViewBox().setYRange(min_power, max_power + 0.1 * max_power)

if __name__ == '__main__':
    indicator = BandPowerRatio_Stack_Handler()
    indicator.test_current_indicator_with_simulated_data()
