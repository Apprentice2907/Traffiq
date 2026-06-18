@echo off
echo Starting ParkSense AI...
cd backend
start /B python app.py
timeout /t 3
cd ../frontend
start index.html
echo ParkSense AI is running.
pause
