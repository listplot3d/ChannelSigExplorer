@echo on
:: Load shared configuration
call common_config.bat

:: =============== Project specific configuration ===============
set EXEC_BASE_DIR=%PROJECT_DIR%
set EXEC_FILE_PATH=%PROJECT_DIR%\main_window.py

:: ===== Verification checkpoints ============

call %ANACONDA_DIR%\Scripts\activate.bat %ANACONDA_DIR%
call conda activate %CONDA_ENV%

set PYTHONPATH=%PROJECT_DIR%;%PYTHONPATH%

cd %EXEC_BASE_DIR%
python %EXEC_FILE_PATH%  &:: :<<<<<<<<<<<<<< check point 
pause