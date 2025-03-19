import logging
from typing import override

import numpy as np
import pyqtgraph as pg
from __BaseIndicator import BaseIndicatorHandler

class Simple_Waveform_MA_Handler(BaseIndicatorHandler):
    @override
    def __init__(self):
        super().__init__(indicator_update_interval=0.1, indicator_wave_columns=200)

    @override
    def create_pyqtgraph_plotWidget(self):
        self.plot_widget = pg.PlotWidget(title="Waveform Down-Sampled with Averaging")
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabels(left='Amplitude (μV)')
        buttom_txt = f"TimeSeries (Update Interval = {self.indicator_update_interval} Seconds)"
        self.plot_widget.setLabel("bottom", buttom_txt)
        self.plot_widget.getViewBox().setMouseEnabled(x=True, y=False)
        
        self.plotted_wave = self.plot_widget.plot(pen='y')  # 曲线
        return self.plot_widget

    @override
    def process_1_interval_rawdata_and_update_plot(self, interval_data):
        logging.debug(f"Simple_Waveform_MA_Handler: sliced_data rcvd {interval_data.shape}")
        # 更新指标数组
        avg_value = np.mean(interval_data)
        self.waveDataIn1D_mgr.append(avg_value)
        # 更新曲线
        self.plotted_wave.setData(self.waveDataIn1D_mgr.buf)

if __name__ == '__main__':
    indicator = Simple_Waveform_MA_Handler()
    indicator.test_current_indicator_with_simulated_data()
