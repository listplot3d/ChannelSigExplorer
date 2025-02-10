## User Scenario for this software can be：
* Real-time data analysis/visualization tool for BioSignal channel. In another word, real-time visualization tool for LSL Stream's single channel
* Gallary framework for BioSig indicators
* Connectivity examples for EEG headbands
* EEG headband quality evaluation tool
* End-to-End example for BioSig/EEG applications

## How to Run
1. Hardware requirement
  this software is tested based on laptop with below metrics:
  2.60Ghz CPU + 8G Memory + Win11 (no graphic card)

2.Setup Environment
    conda create -n py12_env python=3.12
    conda activate py12_env
    conda install --file requirements.txt

3.Execute below commands in two different anaconda prompt
   mne-lsl player "../tools-LSLstream_providers/sample_data_SC4001E0-PSG.edf"
   python main_window.py

## How does it like
![app_screenshot](tutorials/app_screenshot.png)
