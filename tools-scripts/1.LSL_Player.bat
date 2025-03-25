
@echo on
:: =============== config per project =======================
set PROJECT_DIR=D:\Documents\GitHub_listplot3d\ChannelSigExplorer
set EXEC_BASE_DIR=%PROJECT_DIR%
set EXEC_FILE_PATH=%PROJECT_DIR%\TGAM_sleepdata_sample.edf
::set EXEC_FILE_PATH=D:\data\sleep-edf\sleep-cassette\SC4001E0-PSG.edf



:: ===== only need to validate check points ============
set ANACONDA_DIR=D:\SW\anaconda3
set CONDA_ENV=py312  &:: :<<<<<<<<<<<<<< check point 1

call %ANACONDA_DIR%\Scripts\activate.bat %ANACONDA_DIR%
call conda activate %CONDA_ENV%

set PYTHONPATH=%PROJECT_DIR%;%PYTHONPATH%

cd %EXEC_BASE_DIR%
mne-lsl player %EXEC_FILE_PATH%   &:: :<<<<<<<<<<<<<< check point 2
pause