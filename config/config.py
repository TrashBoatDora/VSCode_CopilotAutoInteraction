# -*- coding: utf-8 -*-
"""
Hybrid UI Automation Script - 配置管理模組
管理所有腳本參數、路徑、延遲時間等設定
"""

import os
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
    # 統一輸出目錄（所有結果都放在這裡）
    OUTPUT_BASE_DIR = PROJECT_ROOT / "output"
    EXECUTION_RESULT_DIR = OUTPUT_BASE_DIR / "ExecutionResult"
    ORIGINAL_SCAN_RESULT_DIR = OUTPUT_BASE_DIR / "OriginalScanResult"
    CWE_RESULT_DIR = OUTPUT_BASE_DIR / "CWE_Result"
    VICIOUS_PATTERN_DIR = OUTPUT_BASE_DIR / "vicious_pattern"
    
    # ==================== 提示詞檔案路徑 ====================
    PROMPTS_DIR = PROJECT_ROOT / "prompts"
    PROMPT1_FILE_PATH = PROMPTS_DIR / "prompt1.txt"  # 第一輪互動使用
    PROMPT2_FILE_PATH = PROMPTS_DIR / "prompt2.txt"  # 第二輪以後互動使用
    
    # 專案專用提示詞模式設定
    PROMPT_SOURCE_MODE = "global"  # "global" 或 "project"
    PROJECT_PROMPT_FILENAME = "prompt.txt"  # 專案目錄下的提示詞檔名
    
    # ==================== CWE 漏洞掃描設定 ====================
    CWE_SCAN_ENABLED = False  # 是否啟用 CWE 掃描功能
    CWE_SCAN_OUTPUT_DIR = PROJECT_ROOT / "cwe_scan_results"  # CWE 掃描結果目錄
    CWE_PROMPT_OUTPUT_DIR = PROMPTS_DIR / "cwe_generated"  # CWE 生成的提示詞目錄
    CWE_SCAN_BEFORE_PROMPT = True  # 是否在生成提示詞前先掃描
    CWE_USE_GENERATED_PROMPT = True  # 是否使用 CWE 生成的提示詞
    CWE_PROMPT_MODE = "detailed"  # 提示詞模式: "detailed", "simple", "focused"
    CWE_SCAN_CWES = []  # 要掃描的 CWE 列表，空列表表示全部
    CWE_INTEGRATE_CODEQL_JSON = True  # 是否整合既有的 CodeQL JSON 結果
    CWE_CODEQL_JSON_DIR = PROJECT_ROOT.parent / "CodeQL-query_derive" / "python_query_output"  # CodeQL JSON 目錄
    
    # ==================== VS Code 相關設定 ====================
    VSCODE_EXECUTABLE = "/usr/bin/code"  # VS Code 可執行檔路徑
    VSCODE_STARTUP_DELAY = 5   # VS Code 啟動等待時間（秒）
    VSCODE_STARTUP_TIMEOUT = 9999999999999999999999999  # VS Code 啟動超時時間（秒）
    VSCODE_COMMAND_DELAY = 1    # 命令執行間隔時間（秒）
    
    # ==================== Copilot Chat 相關設定 ====================
    COPILOT_RESPONSE_TIMEOUT = 9999999999999999999999999   # Copilot 回應超時時間（秒）
    COPILOT_CHECK_INTERVAL = 3      # 檢查回應完成間隔（秒）
    COPILOT_COPY_RETRY_MAX = 3      # 複製回應重試次數（copilot_handler 內部）
    COPILOT_COPY_RETRY_DELAY = 2    # 複製重試間隔（秒）
    
    # Artificial Suicide 模式專用重試設定
    AS_MODE_MAX_RETRY_PER_LINE = 10  # AS 模式中每一行的最大重試次數（包含所有失敗類型）
    
    # 模型切換設定
    COPILOT_SWITCH_MODEL_ON_START = True  # 是否在開始時切換模型
    COPILOT_MODEL_SWITCH_DELAY = 1  # 模型切換後的等待時間（秒）
    
    # 智能等待設定
    SMART_WAIT_ENABLED = True    # 是否啟用智能等待
    SMART_WAIT_MAX_ATTEMPTS = 30  # 智能等待最大嘗試次數
    SMART_WAIT_INTERVAL = 2      # 智能等待檢查間隔（秒）
    SMART_WAIT_TIMEOUT = 99999999999999999999999      # 智能等待最大時間（秒）
    
    # ==================== 圖像辨識設定 ====================
    IMAGE_CONFIDENCE = 0.9  # 圖像匹配信心度
    SCREENSHOT_DELAY = 0.5  # 截圖間隔時間
    
    # 圖像資源路徑
    STOP_BUTTON_IMAGE = ASSETS_DIR / "stop_button.png"        # Copilot 停止按鈕
    SEND_BUTTON_IMAGE = ASSETS_DIR / "send_button.png"        # Copilot 發送按鈕
    NEWCHAT_SAVE_IMAGE = ASSETS_DIR / "NewChat_Save.png"      # 新聊天保存提示
    UNDO_CHECK_IMAGE = ASSETS_DIR / "undo_check.png"          # Undo 確認對話框
    
    # ==================== 多輪互動設定 ====================
    INTERACTION_MAX_ROUNDS = 3      # 最大互動輪數
    INTERACTION_ENABLED = True      # 是否啟用反覆互動功能
    INTERACTION_ROUND_DELAY = 2     # 每輪互動間隔時間（秒）
    INTERACTION_INCLUDE_PREVIOUS_RESPONSE = True  # 是否在新一輪提示詞中包含上一輪 Copilot 回應
    INTERACTION_SHOW_UI_ON_STARTUP = True  # 是否在啟動時顯示設定介面
    INTERACTION_RESPONSE_CHAINING_PREFIX = "我們繼續基於前一次的討論。你的上一次回答是：\n\n"  # 回應串接前綴
    INTERACTION_RESPONSE_CHAINING_SUFFIX = "\n\n現在，請針對以下問題或指示繼續：\n\n"  # 回應串接後綴
    
    # CopilotChat 修改結果處理設定
    COPILOT_CHAT_MODIFICATION_ACTION = "keep"  # 預設行為：'keep'(保留) 或 'revert'(復原)
    
    # ==================== 檔案處理限制設定 ====================
    MAX_FILES_TO_PROCESS = None  # 限制總共處理的檔案數量（None 表示無限制）
    
    # ==================== 日誌設定 ====================
    LOG_LEVEL = "DEBUG"      # 日誌等級：DEBUG, INFO, WARNING, ERROR
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
        prompt1_exists = cls.PROMPT1_FILE_PATH.exists()
        prompt2_exists = cls.PROMPT2_FILE_PATH.exists()
        return prompt1_exists, prompt2_exists
    
    @classmethod
    def get_prompt_file_path(cls, round_number: int = 1, project_path: str = None):
        """
        根據輪數和專案路徑取得對應的提示詞檔案路徑
        
        Args:
            round_number: 互動輪數
            project_path: 專案路徑（專案模式時使用）
            
        Returns:
            Path: 提示詞檔案路徑
        """
        if cls.PROMPT_SOURCE_MODE == "project" and project_path:
            # 專案專用提示詞模式：返回專案目錄下的 prompt.txt
            project_dir = Path(project_path)
            return project_dir / cls.PROJECT_PROMPT_FILENAME
        else:
            # 全域提示詞模式：根據輪數返回對應檔案
            if round_number == 1:
                return cls.PROMPT1_FILE_PATH
            else:
                return cls.PROMPT2_FILE_PATH
    
    @classmethod
    def get_project_prompt_path(cls, project_path: str):
        """
        取得專案專用提示詞檔案路徑
        
        Args:
            project_path: 專案路徑
            
        Returns:
            Path: 專案提示詞檔案路徑
        """
        project_dir = Path(project_path)
        return project_dir / cls.PROJECT_PROMPT_FILENAME
    
    @classmethod
    def validate_project_prompt_file(cls, project_path: str):
        """
        驗證專案專用提示詞檔案是否存在
        
        Args:
            project_path: 專案路徑
            
        Returns:
            bool: 檔案是否存在
        """
        prompt_path = cls.get_project_prompt_path(project_path)
        return prompt_path.exists()
    
    @classmethod
    def load_project_prompt_lines(cls, project_path: str):
        """
        載入專案專用提示詞的所有行
        
        Args:
            project_path: 專案路徑
            
        Returns:
            List[str]: 提示詞行列表，失敗時返回空列表
        """
        try:
            prompt_path = cls.get_project_prompt_path(project_path)
            if not prompt_path.exists():
                return []
            
            with open(prompt_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
            
            return lines
        except Exception:
            return []
    
    @classmethod
    def count_project_prompt_lines(cls, project_path: str):
        """
        計算專案專用提示詞的行數
        
        Args:
            project_path: 專案路徑
            
        Returns:
            int: 提示詞行數，失敗時返回0
        """
        lines = cls.load_project_prompt_lines(project_path)
        return len(lines)

# 單例配置實例
config = Config()
