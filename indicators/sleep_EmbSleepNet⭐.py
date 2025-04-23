from typing import override
import numpy as np
import pyqtgraph as pg
import pathlib, importlib

global torch  # Deferred loading due to high initialization cost
global resample  # Deferred loading due to high initialization cost

from __BaseIndicator import BaseIndicatorHandler

from __sleep_staging.EmbedSleepNet_model_arch import EmbedSleepNet  # Assume model file is in the same directory or already in the path


class EmbedSleepNet_Staging_Handler(BaseIndicatorHandler):
    @override
    def __init__(self):
        super().__init__(indicator_update_interval=30)

        # Deferred model loading
        self.model = None
        self.device = None

        # Initialize heatmap data
        self.num_stages = 5  # Number of sleep stages in classification
        self.heatmap_columns = 60
        # Create an RGB heatmap data buffer
        self.rgb_heatmap_data = np.zeros((self.num_stages, self.heatmap_columns, 3), dtype=np.uint8)

        # Sleep stage labels (in order: Wake, REM, N1, N2, N3)
        self.sleep_stage_labels = ["Wake", "REM", "N1", "N2", "N3"]
        self.init_completed = False

    def load_model(self):
        """Deferred model loading"""
        global torch, resample

        torch = importlib.import_module("torch")
        resample = importlib.import_module('scipy.signal').resample

        self.model = EmbedSleepNet()
        model_path = pathlib.Path(__file__).parent / '__sleep_staging/EmbedSleepNet_model_binary.pth'
        self.model.load_state_dict(torch.load(model_path, map_location='cpu', weights_only=True))
        self.model.eval()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)

    @override
    def create_pyqtgraph_plotWidget(self):
        # Create the heatmap display window
        self.plot_layout = pg.GraphicsLayoutWidget()
        self.plot_layout.setWindowTitle("Heatmap Graph")

        # Create heatmap
        self.heatmap_widget = pg.ImageItem(axisOrder='row-major')  # Specify row-major order
        plot_item = self.plot_layout.addPlot(row=0, col=0)  # Add the heatmap to the layout
        plot_item.addItem(self.heatmap_widget)
        bottom_txt = f"TimeSeries (Update Interval = {self.indicator_update_interval} Seconds)"
        plot_item.setLabel("bottom", bottom_txt)
        plot_item.setLabel('left', 'Sleep Stages')  # Set the Y-axis label

        # Reverse the Y-axis (achieved through a transformation matrix)
        transform = pg.QtGui.QTransform()
        transform.scale(1, -1)  # Keep X-axis normal, and reverse the Y-axis
        transform.translate(0, -self.num_stages)  # Translate to align the reversed Y-axis
        self.heatmap_widget.setTransform(transform)

        # Set initial heatmap data
        self.heatmap_widget.setImage(self.rgb_heatmap_data, autoLevels=False, levels=(0, 255))

        # Set Y-axis tick labels and center-align them
        y_ticks = [(i + 0.5, label) for i, label in enumerate(reversed(self.sleep_stage_labels))]
        plot_item.getAxis("left").setTicks([y_ticks])

        return self.plot_layout

    @override
    def process_1_interval_rawdata_and_update_plot(self, interval_data):
        # Deferred model loading to improve application startup performance
        if not self.init_completed:
            self.load_model()
            self.init_completed = True

        # Downsample to 3000 points
        resampled_data = resample(interval_data, 3000)

        # Prepare data for model inference
        input_data = torch.tensor(resampled_data, dtype=torch.float32).view(1, 1, 1, 3000)
        input_data = input_data.to(self.device)

        # Perform model inference
        with torch.no_grad():
            output = self.model(input_data)

        softmax_output = torch.softmax(output, dim=2).squeeze().cpu().numpy()  # 1D array

        # Reorder output to: Wake(0), REM(4), N1(1), N2(2), N3(3)
        reordered_output = softmax_output[[0, 4, 1, 2, 3]]

        # Update the heatmap data
        self.update_heatmap(reordered_output)

    def update_heatmap(self, new_column):
        """
        Update the heatmap data using a rolling mechanism.
        :param new_column: Model's softmax output (1D array with length equal to num_classes)
        """
        # Normalize new_column to the range 0-255
        normalized_data = (new_column * 255).astype(np.uint8)

        # Roll the rgb_heatmap_data to update the last column
        self.rgb_heatmap_data = np.roll(self.rgb_heatmap_data, shift=-1, axis=1)  # Roll columns

        # Copy normalized data to the end of each channel
        self.rgb_heatmap_data[:, -1, 0] = normalized_data  # Red channel
        self.rgb_heatmap_data[:, -1, 1] = normalized_data  # Green channel
        self.rgb_heatmap_data[:, -1, 2] = normalized_data  # Blue channel

        max_pos = np.argmax(normalized_data)  # Get the index of the maximum value
        max_value = normalized_data[max_pos].item()  # Get the maximum value as a scalar

        # Update the red channel with enhanced intensity
        self.rgb_heatmap_data[max_pos, -1, 2] = min(max_value + 122, 255)  # Ensure it does not exceed 255

        # Update heatmap display
        self.heatmap_widget.setImage(self.rgb_heatmap_data, autoLevels=False, levels=(0, 255))


if __name__ == '__main__':
    indicator = EmbedSleepNet_Staging_Handler()
    indicator.test_current_indicator_with_simulated_data()
