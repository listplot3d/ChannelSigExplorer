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
        return self.plot_widget

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