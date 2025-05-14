from typing import override
from analys_bands_ratio_wave import BandPowerRatio_Wave_Handler

class BandPowerRatio_Waveβ_Handler(BandPowerRatio_Wave_Handler):
    @override
    def create_pyqtgraph_plotWidget(self):
        plot_widget = super().create_pyqtgraph_plotWidget()
        
        beta_index = list(self.bands_utils.bands.keys()).index("Beta")
        for i, curve in enumerate(self.band_curves):
            if i != beta_index:
                curve.hide()
        
        return plot_widget

if __name__ == '__main__':
    indicator = BandPowerRatio_Waveβ_Handler()
    indicator.test_current_indicator_with_simulated_data()
