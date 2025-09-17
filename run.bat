@echo off
title Hybrid UI Automation Script
color 0A

echo.
echo ████████████████████████████████████████████████
echo ██                                            ██
echo ██    Hybrid UI Automation Script             ██
echo ██    VS Code Copilot 自動化腳本              ██
echo ██                                            ██
echo ████████████████████████████████████████████████
echo.

echo 請選擇要執行的操作：
echo.
echo [1] 執行完整自動化腳本
echo [2] 執行基本測試
echo [3] 建立圖像模板指南
echo [4] 檢查環境設定
echo [5] 查看說明文件
echo [0] 退出
echo.

set /p choice=請輸入選項 (0-5): 

if "%choice%"=="1" goto run_main
if "%choice%"=="2" goto run_test
if "%choice%"=="3" goto image_guide
if "%choice%"=="4" goto check_env
if "%choice%"=="5" goto show_help
if "%choice%"=="0" goto exit
goto invalid

:run_main
echo.
echo 正在啟動自動化腳本...
echo 注意：請確保已經：
echo 1. 在 projects/ 目錄放置了要處理的專案
echo 2. 在 assets/ 目錄放置了必要的圖像模板
echo 3. VS Code 已正確安裝並可透過 'code' 命令啟動
echo.
if not exist ".venv\Scripts\python.exe" (
    echo ❌ 虛擬環境未找到，請先執行 install.bat
    pause
    goto menu
)
pause
.venv\Scripts\python.exe main.py
pause
goto menu

:run_test
echo.
echo 執行基本測試...
if not exist ".venv\Scripts\python.exe" (
    echo ❌ 虛擬環境未找到，請先執行 install.bat
    pause
    goto menu
)
.venv\Scripts\python.exe test_basic.py
pause
goto menu

:image_guide
echo.
echo ===============================================
echo 圖像模板建立指南
echo ===============================================
echo.
echo 需要建立以下三個圖像模板：
echo.
echo 1. regenerate_button.png
echo    - 開啟 VS Code 和 Copilot Chat
echo    - 發送一個測試提示
echo    - 等待回應完成後，截取「重新生成」按鈕
echo    - 儲存為 assets/regenerate_button.png
echo.
echo 2. copy_button.png
echo    - 在 Copilot Chat 回應區域
echo    - 截取「複製」按鈕（通常在回應右上角）
echo    - 儲存為 assets/copy_button.png
echo.
echo 3. copilot_input.png
echo    - 截取 Copilot Chat 的輸入框區域
echo    - 包含輸入框和周邊一些背景
echo    - 儲存為 assets/copilot_input.png
echo.
echo 注意事項：
echo - 使用一致的 VS Code 主題（建議 Dark+）
echo - 確保縮放比例為 100%%
echo - 截圖要清晰，避免模糊
echo - 圖像大小建議在 50x50 到 200x200 像素之間
echo.
pause
goto menu

:check_env
echo.
echo 檢查環境設定...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未安裝或不在 PATH 中
) else (
    echo ✓ Python 已安裝
    python --version
)

REM Check VS Code
code --version >nul 2>&1
if errorlevel 1 (
    echo ❌ VS Code 未安裝或 'code' 命令不可用
) else (
    echo ✓ VS Code 已安裝
    code --version | head -1
)

REM Check pip packages
echo.
echo 檢查 Python 套件...
python -c "import pyautogui; print('✓ pyautogui 已安裝')" 2>nul || echo ❌ pyautogui 未安裝
python -c "import cv2; print('✓ opencv-python 已安裝')" 2>nul || echo ❌ opencv-python 未安裝
python -c "import pyperclip; print('✓ pyperclip 已安裝')" 2>nul || echo ❌ pyperclip 未安裝
python -c "import psutil; print('✓ psutil 已安裝')" 2>nul || echo ❌ psutil 未安裝

REM Check directories
echo.
echo 檢查目錄結構...
if exist "projects\" (echo ✓ projects/ 目錄存在) else (echo ❌ projects/ 目錄不存在)
if exist "assets\" (echo ✓ assets/ 目錄存在) else (echo ❌ assets/ 目錄不存在)
if exist "logs\" (echo ✓ logs/ 目錄存在) else (echo ❌ logs/ 目錄不存在)

REM Check required files
echo.
echo 檢查必要檔案...
if exist "main.py" (echo ✓ main.py 存在) else (echo ❌ main.py 不存在)
if exist "requirements.txt" (echo ✓ requirements.txt 存在) else (echo ❌ requirements.txt 不存在)

echo.
pause
goto menu

:show_help
echo.
echo ===============================================
echo 使用說明
echo ===============================================
echo.
echo 快速開始：
echo 1. 執行 install.bat 安裝依賴套件
echo 2. 將要處理的專案資料夾放入 projects/ 目錄
echo 3. 根據指南建立圖像模板放入 assets/ 目錄  
echo 4. 執行主腳本開始自動化
echo.
echo 重要注意事項：
echo - 確保 VS Code 已安裝 Copilot 擴充功能
echo - 使用 Dark+ 主題以確保圖像識別準確性
echo - 執行期間避免操作電腦以免干擾自動化
echo - 建議在虛擬機中執行以確保環境穩定
echo.
echo 更多詳細資訊請參閱 README.md
echo.
pause
goto menu

:invalid
echo.
echo 無效的選項，請重新選擇。
pause
goto menu

:menu
cls
goto start

:exit
echo.
echo 感謝使用 Hybrid UI Automation Script！
echo.
exit /b 0

:start
cls
goto :eof