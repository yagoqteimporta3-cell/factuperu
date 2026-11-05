@echo off
title FactuPeru
cd /d "C:\Users\PC\Proyectos\factuperu"

echo ==========================================
echo    FactuPeru - Sistema de gestion
echo ==========================================
echo.
echo  Abriendo el navegador en unos segundos...
start "" powershell -NoProfile -Command "Start-Sleep -Seconds 3; Start-Process 'http://127.0.0.1:8000'"
echo.
echo  NO cierres esta ventana mientras uses el sistema.
echo  Para apagar: cierra esta ventana o presiona Ctrl+C.
echo.
venv\Scripts\python.exe manage.py runserver

pause
