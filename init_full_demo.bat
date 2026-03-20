@echo off
cd /d %~dp0

echo === [1/3] Makemigrations ===
python manage.py makemigrations
if errorlevel 1 goto :error

echo === [2/3] Migrate ===
python manage.py migrate
if errorlevel 1 goto :error

echo === [3/3] Seed full demo data ===
python init_full_demo.py
if errorlevel 1 goto :error

echo.
echo Hoan tat. Chay server bang lenh: python manage.py runserver
goto :eof

:error
echo.
echo Co loi xay ra khi khoi tao CSDL demo.
exit /b 1
