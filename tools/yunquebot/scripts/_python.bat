@echo off
rem Deja en PY la ruta de un Python 3.10 o superior. Lo usan los otros .bat.
rem Orden: variable YUNQUEBOT_PYTHON, .venv del bot, py, python.
set "PY="
if defined YUNQUEBOT_PYTHON call :probar "%YUNQUEBOT_PYTHON%"
if not defined PY if exist "%~dp0..\.venv\Scripts\python.exe" call :probar "%~dp0..\.venv\Scripts\python.exe"
if not defined PY call :probar py
if not defined PY call :probar python
if defined PY exit /b 0

echo No se encontro Python 3.10 o superior.
echo Instalalo desde https://www.python.org/downloads/ y marca "Add python.exe to PATH".
echo Si ya lo tienes, define la variable YUNQUEBOT_PYTHON con la ruta de python.exe.
exit /b 1

:probar
for /f "delims=" %%i in ('call %1 -c "import sys; sys.version_info >= (3, 10) and print(sys.executable)" 2^>nul') do set "PY=%%i"
exit /b 0
