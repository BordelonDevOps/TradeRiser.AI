@echo off
echo ========================================
echo TradeRiser Setup Script for Windows
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo ✓ Python is installed
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)
echo ✓ Virtual environment created
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo ✓ Virtual environment activated
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
echo ✓ Pip upgraded
echo.

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install requirements
    pause
    exit /b 1
)
echo ✓ Requirements installed
echo.

REM Copy environment file
if not exist ".env" (
    echo Creating .env file from template...
    copy ".env.example" ".env"
    echo ✓ .env file created
    echo.
    echo IMPORTANT: Please edit .env file and add your API keys!
    echo Required: ALPHA_VANTAGE_API_KEY
    echo Optional: TWITTER_API_KEY, FRED_API_KEY
    echo.
) else (
    echo ✓ .env file already exists
    echo.
)

REM Check if Redis is available (optional)
redis-server --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠ Redis is not installed (optional for caching)
    echo You can install Redis from: https://redis.io/download
    echo The application will use in-memory caching instead
    echo.
) else (
    echo ✓ Redis is available
    echo.
)

echo ========================================
echo Setup completed successfully!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file and add your API keys
echo 2. Run: python run.py
echo 3. Open http://localhost:5000 in your browser
echo.
echo For API keys:
echo - Alpha Vantage: https://www.alphavantage.co/support/#api-key
echo - Twitter: https://developer.twitter.com/
echo - FRED: https://fred.stlouisfed.org/docs/api/api_key.html
echo.
pause