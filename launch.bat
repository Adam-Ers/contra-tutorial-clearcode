@echo off
py -m pip install pytmx
py -m pip install pygame
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
py main.py
pause