@echo off
echo Cleaning previous builds...
rmdir /s /q build dist
echo Building application...
pyinstaller --clean video_cutter.spec
echo Build complete!
pause