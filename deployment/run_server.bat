@echo off
title FDYS Uretim Sunucusu (Waitress)
color 0A

echo ==================================================
echo.
echo     FDYS - Fabrika Dijital Yonetim Sistemi
echo     Uretim Sunucusu Baslatiliyor...
echo.
echo ==================================================

:: Proje kok dizinine gec
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%.."

:: Sanal ortami kontrol et
set "VENV_DIR=.venv"
if not exist "%VENV_DIR%\Scripts\activate.bat" set "VENV_DIR=venv"
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [HATA] Sanal ortam bulunamadi! Lutfen kurulum adimlarini izleyin.
    pause
    exit /b 1
)

set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "WAITRESS_EXE=%VENV_DIR%\Scripts\waitress-serve.exe"

:: Waitress yuklu degilse kur
"%PYTHON_EXE%" -c "import waitress" 2>nul
if errorlevel 1 (
    echo [*] Waitress kurulyor...
    "%PYTHON_EXE%" -m pip install waitress
)

:: Ortam degiskenlerini uretim moduna ayarla
set FLASK_APP=run.py
set FLASK_ENV=production
set FDYS_CONFIG=production
set FDYS_SECRET_KEY=super-secret-key-for-production

echo [*] Sunucu http://0.0.0.0:8080 adresinde baslatiliyor...
echo [*] Durdurmak icin CTRL+C basin.
echo.

:: Waitress ile baslat
"%WAITRESS_EXE%" --port=8080 --threads=8 "run:app"

pause
