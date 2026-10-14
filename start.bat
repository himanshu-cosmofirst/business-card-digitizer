@echo off
cd /d "%~dp0"
python server.py
if errorlevel 1 py -3 server.py
if errorlevel 1 (
  echo.
  echo Could not start. Run setup.bat first and check README.txt.
  pause
)
