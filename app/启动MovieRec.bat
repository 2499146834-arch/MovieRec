@echo off
chcp 65001 >nul
title MovieRec

echo MovieRec - Starting...

start /min "srv" "D:\Qwen 2.5 7B\env\python.exe" "D:\Movie Recommendation\app\server_render.py"

timeout /t 3 /nobreak >nul
start http://127.0.0.1:8520

echo.
echo http://127.0.0.1:8520
echo.
pause
