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
cd ..

:: Sanal ortami kontrol et
if not exist "venv\Scripts\activate.bat" (
    echo [HATA] Sanal ortam bulunamadi! Lutfen kurulum adimlarini izleyin.
    pause
    exit /b 1
)

:: Sanal ortami aktif et
call venv\Scripts\activate.bat

:: Waitress yuklu degilse kur
python -c "import waitress" 2>nul
if errorlevel 1 (
    echo [*] Waitress kurulyor...
    pip install waitress
)

:: Ortam degiskenlerini uretim moduna ayarla
set FLASK_APP=run.py
set FLASK_ENV=production
set FDYS_CONFIG=production

echo [*] Sunucu http://0.0.0.0:8080 adresinde baslatiliyor...
echo [*] Durdurmak icin CTRL+C basin.
echo.

:: Waitress ile baslat
waitress-serve --port=8080 --threads=8 "app:create_app('production')"

pause
