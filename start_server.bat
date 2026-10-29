@echo off
rem Starts the Eval Tool as a server for the company network.
rem Colleagues open:  http://(IP address of this PC):2718
rem They need the password stored in server_password.txt (next to this file).
rem Close this window to stop the server.

cd /d "%~dp0"

echo.
echo  Eval Tool server is starting...
echo.
echo  Colleagues open the "Network" address shown below,
echo  for example  http://192.168.10.86:2718  (the numbers are this PC's IP address).
echo  Keep this window open. Close it to stop the server.
echo.

rem Open the app in this PC's browser after a few seconds (once the server is up)
start "" cmd /c "timeout /t 6 /nobreak >nul & start http://localhost:2718"

python -m marimo run app.py --host 0.0.0.0 --port 2718 --headless --token-password-file server_password.txt

rem Only reached if the server stops or fails to start, so the message stays readable
echo.
echo  The server has stopped.
pause
