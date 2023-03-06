@ECHO OFF
set python_cmd=python3
ECHO Select python command to use:
ECHO 1. python
ECHO 2. python3
set /p input= Enter 1 or 2: 
if %input% == 1 (
    set python_cmd=python
)
ECHO Executing command: %python_cmd% -m pytest -vv --cov-report term-missing --cov=app
%python_cmd% -m pytest -vv --cov-report term-missing --cov=app
ECHO.
ECHO ###################################################################################
ECHO.
ECHO Testing done. Press any key to delete temp files
PAUSE
%python_cmd% delete_test_files.py
ECHO.
ECHO Temp files deleted
ECHO.
