@echo off
setlocal
title YunqueBot - Prueba
cd /d "%~dp0"
call "%~dp0scripts\_python.bat" || goto fin

echo Usando %PY%
echo.
"%PY%" yunquebot.py selftest

:fin
echo.
pause
