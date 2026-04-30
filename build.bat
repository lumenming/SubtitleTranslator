@echo off
echo ========================================
echo   Subtitle Translator - Build EXE
echo   Author: Your Name
echo   Email: your@email.com
echo   URL: https://github.com/yourname/subtitle-translator
echo   Version: 1.0.0
echo ========================================
echo.

cd /d "%~dp0"

echo Cleaning old builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist SubtitleTranslator.spec del SubtitleTranslator.spec

echo.
echo Building executable...
py -m PyInstaller --onefile --noconsole --name "SubtitleTranslator" app.py

echo.
echo ========================================
echo Build complete! EXE is in dist\SubtitleTranslator.exe
echo ========================================
pause
