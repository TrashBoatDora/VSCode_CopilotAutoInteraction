# -*- coding: utf-8 -*-
"""
Hybrid UI Automation Script - 配置管理模組
管理所有腳本參數、路徑、延遲時間等設定
"""

from pathlib import Path


class Config:
    """配置管理類"""
    
    # ==================== 基本路徑設定 ====================
    PROJECT_ROOT = Path(__file__).parent.parent
    SRC_DIR = PROJECT_ROOT / "src"
    LOGS_DIR = PROJECT_ROOT / "logs"
    ASSETS_DIR = PROJECT_ROOT / "assets"
    PROJECTS_DIR = PROJECT_ROOT / "projects"
    
    # ==================== 輸出目錄設定 ====================
    OUTPUT_BASE_DIR = PROJECT_ROOT / "output"
    EXECUTION_RESULT_DIR = OUTPUT_BASE_DIR / "ExecutionResult"
    ORIGINAL_SCAN_RESULT_DIR = OUTPUT_BASE_DIR / "OriginalScanResult"
    CWE_RESULT_DIR = ORIGINAL_SCAN_RESULT_DIR  # 別名，保留向後相容
    
    # ==================== 提示詞檔案路徑 ====================
    PROMPTS_DIR = PROJECT_ROOT / "prompts"
    PROMPT1_FILE_PATH = PROMPTS_DIR / "prompt1.txt"  # 第一輪互動使用
    PROMPT2_FILE_PATH = PROMPTS_DIR / "prompt2.txt"  # 第二輪以後互動使用
    
    # 專案專用提示詞模式設定
    PROMPT_SOURCE_MODE = "global"  # "global" 或 "project"
    PROJECT_PROMPT_FILENAME = "prompt.txt"  # 專案目錄下的提示詞檔名
    
    # ==================== CWE 漏洞掃描設定 ====================
    CWE_SCAN_ENABLED = False  # 是否啟用 CWE 掃描功能
    
    # ==================== VS Code 相關設定 ====================
    VSCODE_EXECUTABLE = "/snap/bin/code"  # VS Code 可執行檔路徑
    VSCODE_STARTUP_DELAY = 5   # VS Code 啟動等待時間（秒）
    VSCODE_STARTUP_TIMEOUT = 9999999999999999999999999  # VS Code 啟動超時時間（秒）
    VSCODE_COMMAND_DELAY = 1    # 命令執行間隔時間（秒）
    
    # ==================== Copilot Chat 相關設定 ====================
    COPILOT_RESPONSE_TIMEOUT = 9999999999999999999999999   # Copilot 回應超時時間（秒）
    COPILOT_CHECK_INTERVAL = 3      # 檢查回應完成間隔（秒）
    COPILOT_COPY_RETRY_MAX = 3      # 複製回應重試次數
    COPILOT_COPY_RETRY_DELAY = 2    # 複製重試間隔（秒）
    
    # Artificial Suicide 模式專用重試設定
    AS_MODE_MAX_RETRY_PER_LINE = 10  # AS 模式中每一行的最大重試次數
    
    # 模型切換設定
    COPILOT_SWITCH_MODEL_ON_START = True  # 是否在開始時切換模型
    COPILOT_MODEL_SWITCH_DELAY = 1  # 模型切換後的等待時間（秒）
    
    # 智能等待設定
    SMART_WAIT_ENABLED = True    # 是否啟用智能等待
    SMART_WAIT_MAX_ATTEMPTS = 30  # 智能等待最大嘗試次數
    SMART_WAIT_INTERVAL = 2      # 智能等待檢查間隔（秒）
    SMART_WAIT_TIMEOUT = 99999999999999999999999  # 智能等待最大時間（秒）
    
    # ==================== 圖像辨識設定 ====================
    IMAGE_CONFIDENCE = 0.9  # 圖像匹配信心度
    SCREENSHOT_DELAY = 0.5  # 截圖間隔時間
    
    # 圖像資源路徑
    STOP_BUTTON_IMAGE = ASSETS_DIR / "stop_button.png"
    SEND_BUTTON_IMAGE = ASSETS_DIR / "send_button.png"
    NEWCHAT_SAVE_IMAGE = ASSETS_DIR / "NewChat_Save.png"
    UNDO_CHECK_IMAGE = ASSETS_DIR / "undo_check.png"
    
    # ==================== 多輪互動設定 ====================
    INTERACTION_MAX_ROUNDS = 3      # 最大互動輪數
    INTERACTION_ENABLED = True      # 是否啟用反覆互動功能
    INTERACTION_ROUND_DELAY = 2     # 每輪互動間隔時間（秒）
    INTERACTION_INCLUDE_PREVIOUS_RESPONSE = True  # 是否在新一輪中包含上一輪回應
    INTERACTION_SHOW_UI_ON_STARTUP = True  # 是否在啟動時顯示設定介面
    
    # CopilotChat 修改結果處理設定
    COPILOT_CHAT_MODIFICATION_ACTION = "keep"  # 'keep'(保留) 或 'revert'(復原)
    
    # ==================== 日誌設定 ====================
    LOG_LEVEL = "DEBUG"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE_PREFIX = "automation_"
    
    # ==================== 工具方法 ====================
    @classmethod
    def ensure_directories(cls):
        """確保所有必要目錄存在"""
        directories = [cls.LOGS_DIR, cls.ASSETS_DIR, cls.PROJECTS_DIR, cls.PROMPTS_DIR]
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
    def validate_prompt_files(cls):
        """驗證多輪提示詞檔案是否存在"""
        return cls.PROMPT1_FILE_PATH.exists(), cls.PROMPT2_FILE_PATH.exists()
    
    @classmethod
    def get_prompt_file_path(cls, round_number: int = 1, project_path: str = None):
        """根據輪數和專案路徑取得對應的提示詞檔案路徑"""
        if cls.PROMPT_SOURCE_MODE == "project" and project_path:
            return Path(project_path) / cls.PROJECT_PROMPT_FILENAME
        return cls.PROMPT1_FILE_PATH if round_number == 1 else cls.PROMPT2_FILE_PATH
    
    @classmethod
    def get_project_prompt_path(cls, project_path: str):
        """取得專案專用提示詞檔案路徑"""
        return Path(project_path) / cls.PROJECT_PROMPT_FILENAME
    
    @classmethod
    def validate_project_prompt_file(cls, project_path: str):
        """驗證專案專用提示詞檔案是否存在"""
        return cls.get_project_prompt_path(project_path).exists()
    
    @classmethod
    def load_project_prompt_lines(cls, project_path: str):
        """載入專案專用提示詞的所有行"""
        try:
            prompt_path = cls.get_project_prompt_path(project_path)
            if not prompt_path.exists():
                return []
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        except Exception:
            return []
    
    @classmethod
    def count_project_prompt_lines(cls, project_path: str):
        """計算專案專用提示詞的行數"""
        return len(cls.load_project_prompt_lines(project_path))


# 單例配置實例
config = Config()
