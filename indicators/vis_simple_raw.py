from typing import override

import numpy as np
import pyqtgraph as pg
from __BaseIndicator import BaseIndicatorHandler

class Simple_Waveform_Raw_Handler(BaseIndicatorHandler):
    """Real-time EEG waveform processing module"""

    @override
    def __init__(self):
        super().__init__(indicator_update_interval=0.1, indicator_wave_columns=2000)
        # Note: The parameter `indicator_update_interval` is not actually used, only `indicator_graph_columns` is utilized.

    @override
    def create_pyqtgraph_plotWidget(self):
        """
        Create and return the real-time waveform plotting widget.
        :return: PlotWidget object
        """
        self.plot_widget = pg.PlotWidget(title="Real-time EEG Waveform")
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabels(left='Amplitude (μV)', bottom='Time(s)')
        self.plot_widget.getViewBox().setMouseEnabled(x=True, y=False)
        
        self.plotted_wave = self.plot_widget.plot(pen='y')  # Plot the curve
        return self.plot_widget

    @override
    def process_new_data_and_update_plot(self, data_arrived):
        """
        Note: The function overridden in this indicator file is different from other indicators
        because it outputs all raw data without processing it into epochs.
        As a result, it does not use `rawDataInEpochs_Mgr`.
        Be cautious when using this indicator file as a template.
        """
        # Update the buffer
        self.waveDataIn1D_mgr.append(data_arrived)
        indicator_wave_columns = self.waveDataIn1D_mgr.buf_len
        # Compute the time axis based on the sampling frequency
        time_axis = np.arange(indicator_wave_columns) / self.stream_sample_freq  # Time axis (seconds)

        # Update the curve
        self.plotted_wave.setData(time_axis, self.waveDataIn1D_mgr.buf)  # Use the time axis as x data


if __name__ == '__main__':
    indicator = Simple_Waveform_Raw_Handler()
    indicator.test_current_indicator_with_simulated_data()
