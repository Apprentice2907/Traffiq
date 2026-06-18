@echo off
echo ================================
echo   ParkSense AI - Starting Up
echo ================================
echo.
echo Installing dependencies...
pip install -r backend/requirements.txt -q
echo.
echo Starting FastAPI server...
cd backend
start /B python app.py
cd ..
echo.
echo Waiting for server to start...
timeout /t 4 /nobreak > nul
echo Opening dashboard...
start http://localhost:8000/docs
start frontend/index.html
echo.
echo ParkSense AI is running!
echo Dashboard: frontend/index.html
echo API Docs:  http://localhost:8000/docs
echo.
pause
