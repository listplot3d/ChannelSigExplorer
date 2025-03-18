from typing import override

import numpy as np
import pyqtgraph as pg
from __BaseIndicator import BaseIndicatorHandler

class Offline_Waveform_View_Handler(BaseIndicatorHandler):
    """u79bbu7ebfu6a21u5f0fu4e0bu7684u6ce2u5f62u663eu793au6307u6807"""

    @override
    def __init__(self):
        # u4f7fu7528u8f83u5927u7684u6570u636eu5217u6570uff0cu4ee5u663eu793au66f4u591au7684u6570u636eu70b9
        super().__init__(indicator_update_interval=10, indicator_wave_columns=5000)
        self.view_window_size = 10  # u663eu793a10u79d2u7684u6570u636e
        self.vertical_range = None  # u5782u76f4u8303u56f4u81eau52a8u8c03u6574

    @override
    def create_pyqtgraph_plotWidget(self):
        """
        u521bu5efau5e76u8fd4u56deu79bbu7ebfu6ce2u5f62u663eu793au7684u7ed8u56feu7ec4u4ef6
        :return: PlotWidgetu5bf9u8c61
        """
        self.plot_widget = pg.PlotWidget(title="u79bbu7ebfu6ce2u5f62u663eu793a")
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabels(left='u5e45u5ea6 (\u03bcV)', bottom='u65f6u95f4(s)')
        
        # u521bu5efau4e24u6761u66f2u7ebfuff1au4e00u6761u7528u4e8eu6ce2u5f62uff0cu4e00u6761u7528u4e8eu5f53u524du4f4du7f6eu6807u8bb0
        self.plotted_wave = self.plot_widget.plot(pen='y')  # u6ce2u5f62u66f2u7ebf
        self.position_marker = self.plot_widget.plot(pen=pg.mkPen('r', width=2))  # u4f4du7f6eu6807u8bb0
        
        return self.plot_widget

    @override
    def process_offline_data_and_update_plot(self, full_data, current_position):
        """
        u5904u7406u79bbu7ebfu6570u636eu5e76u66f4u65b0u56feu8868
        :param full_data: u5b8cu6574u7684u901au9053u6570u636e
        :param current_position: u5f53u524du65f6u95f4u4f4du7f6euff08u6837u672cu7d22u5f15uff09
        """
        self.is_offline_mode = True
        self.offline_data = full_data
        self.current_position = current_position
        
        # u8ba1u7b97u8981u663eu793au7684u6570u636eu7a97u53e3
        window_samples = int(self.view_window_size * self.stream_sample_freq)
        half_window = window_samples // 2
        
        # u8ba1u7b97u7a97u53e3u8d77u59cbu548cu7ed3u675fu4f4du7f6e
        start_pos = max(0, current_position - half_window)
        end_pos = min(len(full_data), start_pos + window_samples)
        
        # u8c03u6574u8d77u59cbu4f4du7f6euff0cu786eu4fddu7a97u53e3u5927u5c0fu4e00u81f4
        if end_pos - start_pos < window_samples:
            start_pos = max(0, end_pos - window_samples)
        
        # u63d0u53d6u8981u663eu793au7684u6570u636eu7247u6bb5
        if end_pos > start_pos:
            view_data = full_data[start_pos:end_pos]
            
            # u8ba1u7b97u65f6u95f4u8f74
            time_axis = np.arange(start_pos, end_pos) / self.stream_sample_freq
            
            # u66f4u65b0u6ce2u5f62u66f2u7ebf
            self.plotted_wave.setData(time_axis, view_data)
            
            # u66f4u65b0u5f53u524du4f4du7f6eu6807u8bb0uff08u5782u76f4u7ebfuff09
            current_time = current_position / self.stream_sample_freq
            y_range = self.plot_widget.getViewBox().viewRange()[1]  # u83b7u53d6u5f53u524du89c6u56feu7684Yu8f74u8303u56f4
            self.position_marker.setData(
                [current_time, current_time],  # Xu5750u6807uff08u5782u76f4u7ebfuff09
                y_range  # Yu5750u6807u8303u56f4
            )
            
            # u81eau52a8u8c03u6574Yu8f74u8303u56f4uff08u9996u6b21u663eu793au6216u5f53u9009u62e9u4e86u65b0u901au9053uff09
            if self.vertical_range is None:
                data_min, data_max = np.min(view_data), np.max(view_data)
                data_range = data_max - data_min
                # u6dfbu52a010%u7684u4f59u91cf
                self.vertical_range = [data_min - 0.1 * data_range, data_max + 0.1 * data_range]
                self.plot_widget.setYRange(*self.vertical_range)

    @override
    def process_1_interval_rawdata_and_update_plot(self, interval_data):
        """
        u5b9eu65f6u6a21u5f0fu4e0bu7684u6570u636eu5904u7406u65b9u6cd5
        u5728u79bbu7ebfu6a21u5f0fu4e0bu4e0du4f1au88abu76f4u63a5u8c03u7528uff0cu4f46u4f1au88ab process_offline_data_and_update_plot u95f4u63a5u8c03u7528
        """
        if not self.is_offline_mode:
            # u5b9eu65f6u6a21u5f0fu4e0bu7684u5904u7406u65b9u5f0f
            # u8ba1u7b97u65f6u95f4u8f74
            time_axis = np.arange(len(interval_data)) / self.stream_sample_freq
            # u66f4u65b0u66f2u7ebf
            self.plotted_wave.setData(time_axis, interval_data)


if __name__ == '__main__':
    indicator = Offline_Waveform_View_Handler()
    indicator.test_current_indicator_with_simulated_data()
