@echo off
setlocal
title YunqueBot - Discord
cd /d "%~dp0"
call "%~dp0scripts\_python.bat" || goto fin

if exist "configuracion\.env" goto dependencias
copy "configuracion\.env.example" "configuracion\.env" >nul
echo Se ha creado configuracion\.env a partir de .env.example.
echo Rellena DISCORD_TOKEN y DISCORD_CHANNEL_ID, guarda y vuelve a abrir este archivo.
start "" notepad "configuracion\.env"
goto fin

:dependencias
"%PY%" -c "import discord" >nul 2>&1 && goto arrancar
echo Instalando discord.py...
"%PY%" -m pip install -r requirements.txt || goto fin

:arrancar
"%PY%" yunquebot.py discord

:fin
echo.
pause
