import numpy as np


class Bands_Utils:
    # Define frequency bands and color information
    BRAIN_WAVES_BANDS = {
        "4_bands": {
            "Theta": {"range": (4, 8), "color": '#f1c40f'},
            "Alpha": {"range": (8, 13), "color": '#3498db'},
            "Beta": {"range": (13, 30), "color": '#e74c3c'},
            "Gamma": {"range": (30, 100), "color": '#9b59b6'}
        },
        "5_bands": {
            "Delta": {"range": (0.5, 4), "color": '#2ecc71'},
            "Theta": {"range": (4, 8), "color": '#f1c40f'},
            "Alpha": {"range": (8, 13), "color": '#3498db'},
            "Beta": {"range": (13, 30), "color": '#e74c3c'},
            "Gamma": {"range": (30, 100), "color": '#9b59b6'}
        },
        "6_bands": {
            "Delta": {"range": (0.5, 4), "color": '#2ecc71'},
            "Theta": {"range": (4, 8), "color": '#f1c40f'},
            "Part Alpha": {"range": (8, 11), "color": '#85c1e9'},
            "Sigma": {"range": (11, 16), "color": '#3498db'}, #spindle detection
            "Part Beta": {"range": (16, 30), "color": '#e74c3c'},
            "Gamma": {"range": (30, 100), "color": '#9b59b6'}
        },
        "7_bands": {
            "Theta": {"range": (4, 8), "color": '#f1c40f'},
            "Low Alpha": {"range": (8, 10), "color": '#85c1e9'},
            "High Alpha": {"range": (10, 13), "color": '#3498db'},
            "Low Beta": {"range": (13, 20), "color": '#f1948a'},
            "High Beta": {"range": (20, 30), "color": '#e74c3c'},
            "Low Gamma": {"range": (30, 50), "color": '#c39bd3'},
            "Middle Gamma": {"range": (50, 100), "color": '#9b59b6'}
        },
        "8_bands": {
            "Delta": {"range": (0.5, 4), "color": '#2ecc71'},
            "Theta": {"range": (4, 8), "color": '#f1c40f'},
            "Low Alpha": {"range": (8, 10), "color": '#85c1e9'},
            "High Alpha": {"range": (10, 13), "color": '#3498db'},
            "Low Beta": {"range": (13, 20), "color": '#f1948a'},
            "High Beta": {"range": (20, 30), "color": '#e74c3c'},
            "Low Gamma": {"range": (30, 50), "color": '#c39bd3'},
            "Middle Gamma": {"range": (50, 100), "color": '#9b59b6'}
        }

    }
    def __init__(self, bands_num):
        try:
            self.bands_config = self.BRAIN_WAVES_BANDS[f"{bands_num}_bands"]
        except KeyError:
            raise ValueError(f"bands_num({bands_num}) is out of supported range")
            
        self.num_bands = bands_num
        self.bands = {name: info["range"] for name, info in self.bands_config.items()}
        self.colors = [info["color"] for info in self.bands_config.values()]

    def calc_bandpwr_percentage(self, epoch_data, freq):
        # Compute brainwave power for each frequency band using NumPy
        freqs, power_spectrum = self.calc_power_spectrum(epoch_data, fs=freq)
        total_power_spectrum = np.sum(power_spectrum)
        band_powers_percentage = []

        for band_name, band_info in self.bands_config.items():
            low, high = band_info["range"]
            band_power = np.sum(
                power_spectrum[(freqs >= low) & (freqs < high)])  # Calculate power for the frequency band
            band_powers_percentage.append(band_power / total_power_spectrum)

        return total_power_spectrum, band_powers_percentage

    def calc_power_spectrum(self, signal, fs):
        """
        Compute the Power Spectral Density (PSD) using NumPy
        :param signal: Input signal
        :param fs: Sampling frequency
        :return: Frequency array, Power Spectral Density
        """
        n = len(signal)  # Length of the signal
        freq = np.fft.rfftfreq(n, d=1 / fs)  # Compute frequency components
        fft_vals = np.fft.rfft(signal)  # Fast Fourier Transform
        psd = (1 / (fs * n)) * np.abs(fft_vals) ** 2  # Compute power spectral density
        psd[1:-1] *= 2  # Convert two-sided spectrum to one-sided spectrum
        return freq, psd
