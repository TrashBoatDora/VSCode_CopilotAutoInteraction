# -*- coding: utf-8 -*-
"""
Hybrid UI Automation Script - 配置管理模組
管理所有腳本參數、路徑、延遲時間等設定
"""

import os
from pathlib import Path

class Config:
    """配置管理類"""
    
    # 基本路徑設定
    PROJECT_ROOT = Path(__file__).parent.parent
    SRC_DIR = PROJECT_ROOT / "src"
    LOGS_DIR = PROJECT_ROOT / "logs"
    ASSETS_DIR = PROJECT_ROOT / "assets"
    PROJECTS_DIR = PROJECT_ROOT / "projects"
    
    # 提示詞檔案路徑
    PROMPT_FILE_PATH = PROJECT_ROOT / "prompt.txt"
    
    # VS Code 相關設定
    VSCODE_EXECUTABLE = r"C:\Users\C250\AppData\Local\Programs\Microsoft VS Code\Code.exe"  # VS Code 可執行檔路徑
    VSCODE_STARTUP_DELAY = 5   # VS Code 啟動等待時間（秒）
    VSCODE_STARTUP_TIMEOUT = 30  # VS Code 啟動超時時間（秒）
    VSCODE_COMMAND_DELAY = 1    # 命令執行間隔時間（秒）
    
    # Copilot Chat 相關設定
    COPILOT_RESPONSE_TIMEOUT = 90   # Copilot 回應超時時間（秒） - 增加到90秒
    COPILOT_CHECK_INTERVAL = 5      # 檢查回應完成間隔（秒）
    COPILOT_COPY_RETRY_MAX = 3      # 複製回應重試次數
    COPILOT_COPY_RETRY_DELAY = 2    # 複製重試間隔（秒）
    
    # 智能等待設定
    SMART_WAIT_ENABLED = True    # 是否啟用智能等待
    SMART_WAIT_MAX_ATTEMPTS = 30  # 智能等待最大嘗試次數 - 增加到30次
    SMART_WAIT_INTERVAL = 2      # 智能等待檢查間隔（秒） - 減少到2秒提高響應性
    SMART_WAIT_TIMEOUT = 90      # 智能等待最大時間（秒） - 與主超時時間保持一致
    
    # Copilot 記憶清除命令序列
    COPILOT_CLEAR_MEMORY_COMMANDS = [
        # 開啟 Copilot Chat
        {'type': 'hotkey', 'keys': ['ctrl', 'shift', 'i'], 'delay': 2},
        # 清除對話歷史 (Ctrl+L)
        {'type': 'hotkey', 'keys': ['ctrl', 'l'], 'delay': 1},
        # 關閉 Copilot Chat
        {'type': 'key', 'key': 'escape', 'delay': 0.5},
    ]
    
    # 圖像辨識設定
    IMAGE_CONFIDENCE = 0.9  # 圖像匹配信心度
    SCREENSHOT_DELAY = 0.5  # 截圖間隔時間
    IMAGE_RECOGNITION_REQUIRED = False  # 是否強制要求圖像檔案
    
    # 圖像資源路徑（更新後的版本）
    STOP_BUTTON_IMAGE = ASSETS_DIR / "stop_button.png"        # Copilot 停止按鈕
    SEND_BUTTON_IMAGE = ASSETS_DIR / "send_button.png"        # Copilot 發送按鈕
    # 以下圖像不再使用，但保留以防需要
    # REGENERATE_BUTTON_IMAGE = ASSETS_DIR / "regenerate_button.png"
    # COPY_BUTTON_IMAGE = ASSETS_DIR / "copy_button.png"
    # COPILOT_INPUT_BOX_IMAGE = ASSETS_DIR / "copilot_input.png"
    
    # 批次處理設定
    BATCH_SIZE = 100        # 每批處理專案數量
    MAX_RETRY_ATTEMPTS = 3  # 失敗重試次數
    
    # 日誌設定
    LOG_LEVEL = "INFO"      # 日誌等級：DEBUG, INFO, WARNING, ERROR
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE_PREFIX = "automation_"
    
    # UI 初始化設定
    UI_RESET_COMMANDS = [
        # # 最大化視窗
        # {'type': 'hotkey', 'keys': ['alt', 'space'], 'delay': 0.5},
        # {'type': 'key', 'key': 'x', 'delay': 0.5},
        # # 關閉終端機
        # {'type': 'hotkey', 'keys': ['ctrl', 'j'], 'delay': 0.5},
        # # 關閉側邊欄
        # {'type': 'hotkey', 'keys': ['ctrl', 'b'], 'delay': 0.5},
        # # 關閉分割編輯器（重複3次確保全關）
        # {'type': 'hotkey', 'keys': ['ctrl', 'w'], 'repeat': 3, 'delay': 0.2},
    ]
    
    # 安全設定
    FAILSAFE_ENABLED = True  # 啟用 pyautogui 故障安全機制
    EMERGENCY_STOP_CORNER = True  # 滑鼠移到左上角停止腳本
    
    @classmethod
    def ensure_directories(cls):
        """確保所有必要目錄存在"""
        directories = [cls.LOGS_DIR, cls.ASSETS_DIR, cls.PROJECTS_DIR]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_log_file_path(cls, prefix=""):
        """取得日誌檔案路徑"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{cls.LOG_FILE_PREFIX}{prefix}_{timestamp}.log"
        return cls.LOGS_DIR / filename
    
    @classmethod
    def validate_assets(cls):
        """驗證必要的圖像資源是否存在（現已可選）"""
        if not cls.IMAGE_RECOGNITION_REQUIRED:
            return True, []
        
        required_images = [
            cls.REGENERATE_BUTTON_IMAGE,
            cls.COPY_BUTTON_IMAGE,
            cls.COPILOT_INPUT_BOX_IMAGE
        ]
        
        missing_images = []
        for image_path in required_images:
            if not image_path.exists():
                missing_images.append(str(image_path))
        
        success = len(missing_images) == 0
        return success, missing_images
    
    @classmethod
    def validate_prompt_file(cls):
        """驗證提示詞檔案是否存在"""
        return cls.PROMPT_FILE_PATH.exists()

# 單例配置實例
config = Config()