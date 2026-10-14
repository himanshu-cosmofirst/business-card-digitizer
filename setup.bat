@echo off
cd /d "%~dp0"
echo Installing Python packages...
python -m pip install -r requirements.txt
if errorlevel 1 py -3 -m pip install -r requirements.txt
echo.
echo Python packages installed.
echo Make sure Tesseract OCR is installed in C:\Program Files\Tesseract-OCR\
pause
