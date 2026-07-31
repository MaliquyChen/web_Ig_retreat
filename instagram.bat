@echo off
chcp 65001 > nul
title Instagram 活動互動系統
echo ==========================================
echo 🚀 正在啟動 Instagram 活動互動系統...
echo ==========================================
echo.
echo 提示：
echo - 後台控制中心: http://127.0.0.1:5000/
echo - 大螢幕顯示頁: http://127.0.0.1:5000/screen?character_id=all
echo.
echo 正在啟動伺服器，請勿關閉此視窗...
echo ------------------------------------------

python app.py

pause
