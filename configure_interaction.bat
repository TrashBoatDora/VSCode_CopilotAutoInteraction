@echo off
chcp 65001 >nul
echo ========================================
echo    Copilot Chat 多輪互動設定工具
echo ========================================
echo.

cd /d "%~dp0"

echo 啟動設定介面...
python src\interaction_settings_ui.py

echo.
echo 設定完成！
pause