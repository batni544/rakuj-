@echo off
title Rakuji Security Bot
color 0A
echo.
echo  ================================================
echo   ^|^|   Rakuji Security Bot baslatiliyor...   ^|^|
echo  ================================================
echo.
cd /d "%~dp0"
python bot.py
echo.
echo  Bot durdu. Kapatmak icin bir tusa basin...
pause > nul
