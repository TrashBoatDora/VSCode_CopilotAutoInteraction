@echo off
echo ========================================
echo   Hybrid UI Automation Script
echo ========================================
echo.
echo 請選擇操作：
echo.
echo [1] 執行主腳本
echo [2] 執行測試
echo [3] 檢查環境
echo [4] 退出
echo.
set /p choice="請輸入選擇 (1-4): "

if "%choice%"=="1" goto run_main
if "%choice%"=="2" goto run_test  
if "%choice%"=="3" goto check_env
if "%choice%"=="4" goto exit
goto menu

:run_main
echo.
echo 執行主腳本...
if not exist ".venv\Scripts\python.exe" (
    echo 錯誤：虛擬環境未找到，請先執行 install.bat
    pause
    exit
)
.venv\Scripts\python.exe main.py
pause
exit

:run_test
echo.
echo 執行測試...
if not exist ".venv\Scripts\python.exe" (
    echo 錯誤：虛擬環境未找到，請先執行 install.bat
    pause
    exit
)
.venv\Scripts\python.exe test_basic.py
pause
exit

:check_env
echo.
echo 環境檢查...
python --version
if exist ".venv\Scripts\python.exe" (
    echo 虛擬環境：已建立
) else (
    echo 虛擬環境：未建立
)
pause
exit

:exit
exit