@echo off
rem Starts the Eval Tool as a server for the company network.
rem Colleagues open:  http://ZSC-PC:2718
rem They need the password stored in server_password.txt (next to this file).
rem Close this window to stop the server.

cd /d "%~dp0"
marimo run app.py --host 0.0.0.0 --port 2718 --headless --token-password-file server_password.txt
