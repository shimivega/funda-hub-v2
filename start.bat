@echo off
echo Starting Funda App...

:: Create virtual environment if it doesn't exist
if not exist "venv\Scripts\activate" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    pip install --upgrade pip
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

:: Create necessary directories if they don't exist
if not exist "uploads" mkdir uploads
if not exist "resources" mkdir resources

:: Initialize the database
python -c "from app import app, db; app.app_context().push(); db.create_all()"

:: Start the Flask application
set FLASK_APP=app.py
set FLASK_ENV=development
flask run

pause
