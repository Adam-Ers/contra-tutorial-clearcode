@echo off
python3 -m pip install pytmx
python3 -m pip install pygame-ce
echo Controls:
echo Left and Right Arrows - Movement
echo Down Arrow - Duck
echo Z - Jump/Respawn
echo X - Fire
echo C - Dash
echo Shift - Strafe
echo K - Commit Die
echo F - Fullscreen
echo P - Show Framerate
echo.
python3 main.py
pause