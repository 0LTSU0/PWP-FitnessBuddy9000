@ECHO OFF
ECHO Starting pytest
pytest -vv
ECHO.
ECHO ###################################################################################
ECHO.
ECHO Testing done. Press any key to delete temp files
PAUSE
python delete_test_files.py
ECHO.
ECHO Temp files deleted
ECHO.
