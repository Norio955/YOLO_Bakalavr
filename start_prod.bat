@echo off
:: Цей скрипт запускає програму без чорного вікна консолі на фоні
call .venv\Scripts\activate.bat
set APP_LOG_LEVEL=INFO

:: Використовуємо pythonw.exe щоб сховати консоль
start pythonw main.py