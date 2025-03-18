import os
import numpy as np
import pyedflib
import mne
from datetime import datetime
import time
from pyqtgraph.Qt import QtCore, QtWidgets
from GUIComp_Utils import GUI_Utils
from indicators.__Indicator_Global_Cfg import Indicator_Globals

class FileDataManager:
    """
    文件数据管理器，用于离线模式下加载和处理EEG数据文件
    """

    def __init__(self, main_window, debug_mode=False):
        self.main_window = main_window
        self.status_bar = main_window.status_bar
        self.debug_mode = debug_mode
        
        # 数据相关属性
        self.file_path = None  # 当前加载的文件路径
        self.data = None       # 加载的数据
        self.channel_names = []  # 通道名称列表
        self.sample_freq = 0     # 采样频率
        self.data_length = 0     # 数据长度（样本数）
        self.duration = 0        # 数据持续时间（秒）
        
        # 时间轴控制
        self.current_position = 0  # 当前时间位置（样本索引）
        self.timeline_slider = None  # 时间轴滑块
        
        # 选中的通道
        self.selected_channel = None  # 当前选中的通道索引

    def add_file_menu_on_toolbar(self, toolbar):
        """
        在工具栏上添加文件操作菜单
        """
        # 创建文件菜单
        file_menu = QtWidgets.QMenu("文件操作", toolbar)
        file_menu.addAction("加载EDF文件").triggered.connect(self.load_edf_file)
        file_menu.addAction("加载CSV文件").triggered.connect(self.load_csv_file)
        
        # 创建工具按钮
        file_button = GUI_Utils.transform_menu_to_toolbutton("📂", file_menu)
        toolbar.addWidget(file_button)
        
        # 添加通道选择下拉框（当文件加载后才会有内容）
        self.channel_combo = QtWidgets.QComboBox()
        self.channel_combo.setMinimumWidth(150)
        self.channel_combo.setEnabled(False)
        self.channel_combo.currentIndexChanged.connect(self.on_channel_selected)
        toolbar.addWidget(QtWidgets.QLabel("选择通道: "))
        toolbar.addWidget(self.channel_combo)

    def add_timeline_controls_on_toolbar(self, toolbar):
        """
        在工具栏上添加时间轴控制
        """
        # 添加时间轴滑块
        self.timeline_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.timeline_slider.setMinimum(0)
        self.timeline_slider.setMaximum(100)  # 初始设置，加载文件后会更新
        self.timeline_slider.setValue(0)
        self.timeline_slider.setEnabled(False)
        self.timeline_slider.valueChanged.connect(self.on_timeline_changed)
        self.timeline_slider.setMinimumWidth(200)
        
        # 添加时间标签
        self.time_label = QtWidgets.QLabel("00:00 / 00:00")
        
        # 添加到工具栏
        toolbar.addWidget(QtWidgets.QLabel("时间轴: "))
        toolbar.addWidget(self.timeline_slider)
        toolbar.addWidget(self.time_label)

    def load_edf_file(self):
        """
        加载EDF文件
        """
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.main_window, "选择EDF文件", "", "EDF Files (*.edf);;All Files (*)"
        )
        
        if not file_path:
            return
            
        try:
            # 使用pyedflib加载EDF文件
            with pyedflib.EdfReader(file_path) as f:
                n_channels = f.signals_in_file
                self.channel_names = f.getSignalLabels()
                self.sample_freq = f.getSampleFrequency(0)  # 假设所有通道采样率相同
                
                # 读取所有通道数据
                self.data = np.zeros((n_channels, f.getNSamples()[0]))
                for i in range(n_channels):
                    self.data[i, :] = f.readSignal(i)
                
                self.data_length = self.data.shape[1]
                self.duration = self.data_length / self.sample_freq
            
            self.file_path = file_path
            self._update_ui_after_file_load()
            self.status_bar.showMessage(f"已加载EDF文件: {os.path.basename(file_path)}")
            
        except Exception as e:
            self.status_bar.showMessage(f"加载EDF文件失败: {str(e)}")
            if self.debug_mode:
                print(f"Error loading EDF file: {str(e)}")

    def load_csv_file(self):
        """
        加载CSV文件
        """
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.main_window, "选择CSV文件", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
            
        try:
            # 使用numpy加载CSV文件
            data = np.loadtxt(file_path, delimiter=',', skiprows=1)
            
            # 假设第一列是时间，其余列是通道数据
            # 转置数据使通道在第一维
            self.data = data[:, 1:].T
            
            # 从第一行读取通道名称
            with open(file_path, 'r') as f:
                header = f.readline().strip().split(',')
                self.channel_names = header[1:]  # 跳过第一列（时间列）
            
            # 计算采样频率（假设时间列单位为秒）
            time_column = data[:, 0]
            if len(time_column) > 1:
                time_diff = time_column[1] - time_column[0]
                self.sample_freq = 1 / time_diff
            else:
                self.sample_freq = 250  # 默认值
            
            self.data_length = self.data.shape[1]
            self.duration = self.data_length / self.sample_freq
            
            self.file_path = file_path
            self._update_ui_after_file_load()
            self.status_bar.showMessage(f"已加载CSV文件: {os.path.basename(file_path)}")
            
        except Exception as e:
            self.status_bar.showMessage(f"加载CSV文件失败: {str(e)}")
            if self.debug_mode:
                print(f"Error loading CSV file: {str(e)}")

    def _update_ui_after_file_load(self):
        """
        文件加载后更新UI
        """
        # 更新通道下拉框
        self.channel_combo.clear()
        self.channel_combo.addItems(self.channel_names)
        self.channel_combo.setEnabled(True)
        
        # 选择第一个通道
        if self.channel_names:
            self.selected_channel = 0
            self.channel_combo.setCurrentIndex(0)
        
        # 更新时间轴滑块
        self.timeline_slider.setMaximum(self.data_length - 1)
        self.timeline_slider.setValue(0)
        self.timeline_slider.setEnabled(True)
        
        # 更新时间标签
        self._update_time_label()
        
        # 设置全局配置中的采样频率
        Indicator_Globals.stream_freq = self.sample_freq
        
        # 关闭所有已加载的指标
        self.main_window.close_all_indicators()

    def on_channel_selected(self, index):
        """
        通道选择变更处理
        """
        if index >= 0 and index < len(self.channel_names):
            self.selected_channel = index
            # 更新所有已加载指标
            self._update_all_indicators()
            self.status_bar.showMessage(f"已选择通道: {self.channel_names[index]}")

    def on_timeline_changed(self, value):
        """
        时间轴滑块变更处理
        """
        self.current_position = value
        self._update_time_label()
        # 更新所有已加载指标
        self._update_all_indicators()

    def _update_time_label(self):
        """
        更新时间标签
        """
        if self.data is not None:
            current_time = self.current_position / self.sample_freq
            total_time = self.duration
            
            # 格式化为分:秒
            current_min, current_sec = divmod(int(current_time), 60)
            total_min, total_sec = divmod(int(total_time), 60)
            
            self.time_label.setText(f"{current_min:02d}:{current_sec:02d} / {total_min:02d}:{total_sec:02d}")

    def _update_all_indicators(self):
        """
        更新所有已加载的指标
        """
        if self.data is None or self.selected_channel is None:
            return
            
        for handler in self.main_window.loaded_indicators:
            if hasattr(handler, 'process_offline_data_and_update_plot'):
                # 获取当前通道的数据
                channel_data = self.data[self.selected_channel]
                # 调用离线处理方法
                handler.process_offline_data_and_update_plot(channel_data, self.current_position)

    def get_channel_data(self, channel_index=None):
        """
        获取指定通道的数据
        """
        if self.data is None:
            return None
            
        if channel_index is None:
            channel_index = self.selected_channel
            
        if channel_index is not None and 0 <= channel_index < self.data.shape[0]:
            return self.data[channel_index]
            
        return None

    def get_current_view_data(self, window_size=None):
        """
        获取当前视图的数据片段
        """
        if self.data is None or self.selected_channel is None:
            return None
            
        if window_size is None:
            # 默认显示10秒数据
            window_size = int(10 * self.sample_freq)
            
        # 计算窗口起始和结束位置
        start_pos = max(0, self.current_position - window_size // 2)
        end_pos = min(self.data_length, start_pos + window_size)
        
        # 调整起始位置，确保窗口大小一致
        start_pos = max(0, end_pos - window_size)
        
        # 获取数据片段
        return self.data[self.selected_channel, start_pos:end_pos], start_pos, end_pos
