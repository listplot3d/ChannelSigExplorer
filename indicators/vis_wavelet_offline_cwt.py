from typing import override

import numpy as np
import pyqtgraph as pg
from scipy import signal
from __BaseIndicator import BaseIndicatorHandler

class Offline_Wavelet_CWT_Handler(BaseIndicatorHandler):
    """u79bbu7ebfu6a21u5f0fu4e0bu7684u5c0fu6ce2u53d8u6362u65f6u9891u5206u6790u6307u6807"""

    @override
    def __init__(self):
        super().__init__(indicator_update_interval=1, indicator_wave_columns=None)
        self.window_size = 10  # u5206u6790u7a97u53e3u5927u5c0fuff08u79d2uff09
        self.position_line = None  # u5f53u524du4f4du7f6eu7ebf
        self.cwt_result = None  # u5b58u50a8u5c0fu6ce2u53d8u6362u7ed3u679c
        self.freqs = None  # u9891u7387u8303u56f4
        self.times = None  # u65f6u95f4u8303u56f4
        
        # u8bbeu7f6eu9891u7387u8303u56f4uff08u5bf9u6570u5206u5e03uff09
        self.min_freq = 1  # u6700u5c0fu9891u7387uff08Hzuff09
        self.max_freq = 50  # u6700u5927u9891u7387uff08Hzuff09
        self.num_freqs = 50  # u9891u7387u70b9u6570

    @override
    def create_pyqtgraph_plotWidget(self):
        """
        u521bu5efau5e76u8fd4u56deu79bbu7ebfu5c0fu6ce2u53d8u6362u7684u7ed8u56feu7ec4u4ef6
        :return: PlotWidgetu5bf9u8c61
        """
        self.plot_widget = pg.PlotWidget(title="u79bbu7ebfu5c0fu6ce2u53d8u6362u5206u6790")
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabels(left='u9891u7387 (Hz)', bottom='u65f6u95f4 (s)')
        
        # u521bu5efau56feu50cfu9879u7528u4e8eu663eu793au65f6u9891u56fe
        self.img_item = pg.ImageItem()
        self.plot_widget.addItem(self.img_item)
        
        # u6dfbu52a0u989cu8272u6761
        self.colorbar = pg.ColorBarItem(
            values=(0, 1),
            colorMap=pg.colormap.get("viridis"),
            label="u80fdu91cf"
        )
        self.colorbar.setImageItem(self.img_item)
        
        # u521bu5efau5f53u524du4f4du7f6eu7ebf
        self.position_line = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen('r', width=2))
        self.plot_widget.addItem(self.position_line)
        
        # u6dfbu52a0u9891u6bb5u6807u8bb0
        self.add_frequency_bands()
        
        return self.plot_widget
    
    def add_frequency_bands(self):
        """u6dfbu52a0u8111u7535u9891u6bb5u6807u8bb0"""
        # u5b9au4e49u8111u7535u9891u6bb5
        bands = [
            {"name": "u03b4 (Delta)", "range": (0.5, 4)},
            {"name": "u03b8 (Theta)", "range": (4, 8)},
            {"name": "u03b1 (Alpha)", "range": (8, 13)},
            {"name": "u03b2 (Beta)", "range": (13, 30)},
            {"name": "u03b3 (Gamma)", "range": (30, 50)}
        ]
        
        # u4e3au6bcfu4e2au9891u6bb5u6dfbu52a0u6c34u5e73u7ebfu548cu6587u672cu6807u7b7e
        for band in bands:
            # u6dfbu52a0u4e0au4e0bu9650u7ebf
            for freq in band["range"]:
                if self.min_freq <= freq <= self.max_freq:
                    line = pg.InfiniteLine(pos=freq, angle=0, pen=pg.mkPen('w', width=1, style=pg.QtCore.Qt.PenStyle.DashLine))
                    self.plot_widget.addItem(line)
            
            # u6dfbu52a0u6587u672cu6807u7b7e
            mid_freq = (band["range"][0] + band["range"][1]) / 2
            if self.min_freq <= mid_freq <= self.max_freq:
                text = pg.TextItem(text=band["name"], color="w", anchor=(0, 0.5))
                text.setPos(0, mid_freq)
                self.plot_widget.addItem(text)

    @override
    def process_offline_data_and_update_plot(self, full_data, current_position):
        """
        u5904u7406u79bbu7ebfu6570u636eu5e76u66f4u65b0u5c0fu6ce2u53d8u6362u56fe
        :param full_data: u5b8cu6574u7684u901au9053u6570u636e
        :param current_position: u5f53u524du65f6u95f4u4f4du7f6euff08u6837u672cu7d22u5f15uff09
        """
        self.is_offline_mode = True
        self.offline_data = full_data
        self.current_position = current_position
        
        # u8ba1u7b97u5206u6790u7a97u53e3u7684u6837u672cu6570
        window_samples = int(self.window_size * self.stream_sample_freq)
        half_window = window_samples // 2
        
        # u8ba1u7b97u7a97u53e3u8d77u59cbu548cu7ed3u675fu4f4du7f6e
        start_pos = max(0, current_position - half_window)
        end_pos = min(len(full_data), start_pos + window_samples)
        
        # u8c03u6574u8d77u59cbu4f4du7f6euff0cu786eu4fddu7a97u53e3u5927u5c0fu4e00u81f4
        if end_pos - start_pos < window_samples:
            start_pos = max(0, end_pos - window_samples)
        
        # u63d0u53d6u8981u5206u6790u7684u6570u636eu7247u6bb5
        if end_pos > start_pos:
            segment_data = full_data[start_pos:end_pos]
            
            # u8ba1u7b97u5c0fu6ce2u53d8u6362uff08u5982u679cu8fd8u6ca1u6709u8ba1u7b97u8fc7u6216u6570u636eu7247u6bb5u53d8u5316uff09
            if self.cwt_result is None or len(self.cwt_result[0]) != len(segment_data):
                self.compute_cwt(segment_data, start_pos)
            
            # u66f4u65b0u5f53u524du4f4du7f6eu7ebf
            current_time = current_position / self.stream_sample_freq
            self.position_line.setValue(current_time)
    
    def compute_cwt(self, data, start_pos):
        """
        u8ba1u7b97u8fdeu7eedu5c0fu6ce2u53d8u6362
        :param data: u8f93u5165u6570u636e
        :param start_pos: u6570u636eu7247u6bb5u7684u8d77u59cbu4f4du7f6euff08u6837u672cu7d22u5f15uff09
        """
        # u751fu6210u5bf9u6570u5206u5e03u7684u9891u7387u8303u56f4
        self.freqs = np.logspace(np.log10(self.min_freq), np.log10(self.max_freq), self.num_freqs)
        
        # u8ba1u7b97u5c0fu6ce2u53d8u6362
        scales = self.stream_sample_freq / (2 * self.freqs * np.pi)
        self.cwt_result = signal.cwt(data, signal.morlet2, scales)
        
        # u8ba1u7b97u65f6u95f4u8f74
        self.times = np.arange(start_pos, start_pos + len(data)) / self.stream_sample_freq
        
        # u8ba1u7b97u80fdu91cfuff08u5e45u5ea6u7684u5e73u65b9uff09
        cwt_power = np.abs(self.cwt_result) ** 2
        
        # u5f52u4e00u5316u80fdu91cf
        cwt_power_norm = (cwt_power - cwt_power.min()) / (cwt_power.max() - cwt_power.min() + 1e-10)
        
        # u66f4u65b0u56feu50cf
        self.img_item.setImage(cwt_power_norm)
        
        # u8bbeu7f6eu56feu50cfu4f4du7f6eu548cu6bd4u4f8b
        rect = pg.QtCore.QRectF(self.times[0], self.freqs[0], self.times[-1] - self.times[0], self.freqs[-1] - self.freqs[0])
        self.img_item.setRect(rect)
        
        # u66f4u65b0u989cu8272u6761
        self.colorbar.setLevels((cwt_power_norm.min(), cwt_power_norm.max()))
        
        # u8bbeu7f6eYu8f74u4e3au5bf9u6570u523bu5ea6
        self.plot_widget.setLogMode(y=True)
        self.plot_widget.setYRange(np.log10(self.min_freq), np.log10(self.max_freq))

    @override
    def process_1_interval_rawdata_and_update_plot(self, interval_data):
        """
        u5b9eu65f6u6a21u5f0fu4e0bu7684u6570u636eu5904u7406u65b9u6cd5
        u5728u79bbu7ebfu6a21u5f0fu4e0bu4e0du4f1au88abu76f4u63a5u8c03u7528
        """
        if not self.is_offline_mode:
            # u5b9eu65f6u6a21u5f0fu4e0bu7684u5c0fu6ce2u53d8u6362u5904u7406
            # u7b80u5316u5b9eu73b0uff0cu53eau5904u7406u5f53u524du95f4u9694u6570u636e
            self.compute_cwt(interval_data, 0)


if __name__ == '__main__':
    indicator = Offline_Wavelet_CWT_Handler()
    indicator.test_current_indicator_with_simulated_data()
