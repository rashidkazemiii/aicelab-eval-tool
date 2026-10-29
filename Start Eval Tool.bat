@echo off
rem Starts the Eval Tool on this computer only.
rem The app opens in your web browser. Close this window to stop it.
rem First time on a new computer, install the libraries once with:
rem     pip install -r backend\requirements.txt

cd /d "%~dp0"
python -m marimo run app.py
pause
