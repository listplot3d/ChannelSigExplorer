from typing import override

import numpy as np
import pyqtgraph as pg
from scipy import signal
from __BaseIndicator import BaseIndicatorHandler

class Offline_Spectrum_PSD_Handler(BaseIndicatorHandler):
    """离线模式下的功率谱密度分析指标"""

    @override
    def __init__(self):
        super().__init__(indicator_update_interval=1, indicator_wave_columns=None)
        self.fft_size = 1024  # FFT大小
        self.window_size = 5  # 分析窗口大小（秒）

    @override
    def create_pyqtgraph_plotWidget(self):
        """
        创建并返回离线频谱分析的绘图组件
        :return: PlotWidget对象
        """
        self.plot_widget = pg.PlotWidget(title="离线频谱分析")
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabels(left='功率 (dB)', bottom='频率 (Hz)')
        self.plot_widget.setLogMode(x=False, y=True)  # Y轴使用对数刻度
        
        # 创建频谱曲线
        self.plotted_spectrum = self.plot_widget.plot(pen='c')
        
        # 添加频段标记区域
        self.add_frequency_bands()
        
        return self.plot_widget
    
    def add_frequency_bands(self):
        """添加脑电频段标记区域"""
        # 定义脑电频段及其颜色
        bands = [
            {"name": "δ (Delta)", "range": (0.5, 4), "color": (100, 100, 255, 50)},
            {"name": "θ (Theta)", "range": (4, 8), "color": (100, 255, 100, 50)},
            {"name": "α (Alpha)", "range": (8, 13), "color": (255, 100, 100, 50)},
            {"name": "β (Beta)", "range": (13, 30), "color": (255, 255, 100, 50)},
            {"name": "γ (Gamma)", "range": (30, 100), "color": (255, 100, 255, 50)}
        ]
        
        # 为每个频段添加标记区域和文本标签
        self.band_regions = []
        for band in bands:
            # 创建区域
            region = pg.LinearRegionItem(
                values=band["range"],
                brush=pg.mkBrush(band["color"]),
                movable=False
            )
            self.plot_widget.addItem(region)
            self.band_regions.append(region)
            
            # 添加文本标签
            text = pg.TextItem(text=band["name"], color="w", anchor=(0.5, 1))
            text.setPos((band["range"][0] + band["range"][1]) / 2, 0)
            self.plot_widget.addItem(text)

    @override
    def process_offline_data_and_update_plot(self, full_data, current_position):
        """
        处理离线数据并更新频谱图
        :param full_data: 完整的通道数据
        :param current_position: 当前时间位置（样本索引）
        """
        self.is_offline_mode = True
        self.offline_data = full_data
        self.current_position = current_position
        
        # 计算分析窗口的样本数
        window_samples = int(self.window_size * self.stream_sample_freq)
        half_window = window_samples // 2
        
        # 计算窗口起始和结束位置
        start_pos = max(0, current_position - half_window)
        end_pos = min(len(full_data), start_pos + window_samples)
        
        # 调整起始位置，确保窗口大小一致
        if end_pos - start_pos < window_samples:
            start_pos = max(0, end_pos - window_samples)
        
        # 提取要分析的数据片段
        if end_pos > start_pos:
            segment_data = full_data[start_pos:end_pos]
            
            # 计算功率谱密度
            freqs, psd = self.compute_psd(segment_data)
            
            # 更新频谱曲线
            self.plotted_spectrum.setData(freqs, psd)
            
            # 设置X轴范围
            self.plot_widget.setXRange(0, min(100, freqs[-1]))
    
    def compute_psd(self, data):
        """
        计算功率谱密度
        :param data: 输入数据
        :return: 频率和对应的功率谱密度
        """
        # 应用汉宁窗
        windowed_data = data * signal.windows.hann(len(data))
        
        # 计算FFT
        fft_size = min(self.fft_size, len(data))
        fft_result = np.fft.rfft(windowed_data, n=fft_size)
        
        # 计算功率谱密度
        psd = np.abs(fft_result) ** 2 / len(data)
        
        # 转换为分贝单位
        psd_db = 10 * np.log10(psd + 1e-10)  # 添加小值避免log(0)
        
        # 计算频率轴
        freqs = np.fft.rfftfreq(fft_size, d=1.0/self.stream_sample_freq)
        
        return freqs, psd_db

    @override
    def process_1_interval_rawdata_and_update_plot(self, interval_data):
        """
        实时模式下的数据处理方法
        在离线模式下不会被直接调用，但会被process_offline_data_and_update_plot间接调用
        """
        if not self.is_offline_mode:
            # 计算功率谱密度
            freqs, psd = self.compute_psd(interval_data)
            
            # 更新频谱曲线
            self.plotted_spectrum.setData(freqs, psd)
            
            # 设置X轴范围
            self.plot_widget.setXRange(0, min(100, freqs[-1]))


if __name__ == '__main__':
    indicator = Offline_Spectrum_PSD_Handler()
    indicator.test_current_indicator_with_simulated_data()
