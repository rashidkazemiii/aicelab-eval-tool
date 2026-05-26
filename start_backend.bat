@echo off
cd /d "%~dp0backend"
"C:\Users\kaz\AppData\Local\pypoetry\Cache\virtualenvs\eval-tool-1ZblJDTh-py3.13\Scripts\python.exe" -m uvicorn main:app --reload
