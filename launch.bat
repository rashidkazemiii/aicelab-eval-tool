@echo off
cd /d "%~dp0backend"
poetry run python "..\main_gui.py"
pause
