# -*- coding: utf-8 -*-
"""
Hybrid UI Automation Script - 統一日誌系統模組

設計原則：
1. 一次執行 = 一個日誌檔案（不論有多少模組）
2. 所有模組共用同一個日誌實例
3. 清晰的時間戳和模組標識
4. 支援分隔線和結構化輸出
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# 全域變數：確保整個執行週期只有一個日誌檔案
_GLOBAL_LOG_FILE: Optional[Path] = None
_GLOBAL_LOGGER: Optional[logging.Logger] = None
_EXECUTION_START_TIME: Optional[datetime] = None


def _get_config():
    """安全地獲取 config，避免循環導入"""
    try:
        from config.config import config
        return config
    except ImportError:
        return None


def _initialize_global_logger() -> logging.Logger:
    """
    初始化全域日誌記錄器（整個執行週期只執行一次）
    """
    global _GLOBAL_LOG_FILE, _GLOBAL_LOGGER, _EXECUTION_START_TIME
    
    if _GLOBAL_LOGGER is not None:
        return _GLOBAL_LOGGER
    
    # 記錄執行開始時間
    _EXECUTION_START_TIME = datetime.now()
    timestamp = _EXECUTION_START_TIME.strftime("%Y%m%d_%H%M%S")
    
    # 設定日誌目錄和檔案
    config = _get_config()
    if config:
        logs_dir = config.LOGS_DIR
        log_level = getattr(logging, config.LOG_LEVEL, logging.DEBUG)
        log_format = config.LOG_FORMAT
    else:
        logs_dir = Path(__file__).parent.parent / "logs"
        log_level = logging.DEBUG
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logs_dir.mkdir(parents=True, exist_ok=True)
    _GLOBAL_LOG_FILE = logs_dir / f"execution_{timestamp}.log"
    
    # 創建根日誌記錄器
    _GLOBAL_LOGGER = logging.getLogger("CopilotAutomation")
    _GLOBAL_LOGGER.setLevel(logging.DEBUG)
    _GLOBAL_LOGGER.handlers.clear()  # 清除可能存在的舊處理器
    
    # 設定格式器
    formatter = logging.Formatter(log_format)
    
    # 檔案處理器（記錄所有級別）
    file_handler = logging.FileHandler(_GLOBAL_LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    _GLOBAL_LOGGER.addHandler(file_handler)
    
    # 控制台處理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    _GLOBAL_LOGGER.addHandler(console_handler)
    
    # 記錄啟動資訊
    _GLOBAL_LOGGER.info("=" * 70)
    _GLOBAL_LOGGER.info(f"🚀 Copilot Automation 執行開始")
    _GLOBAL_LOGGER.info(f"   時間: {_EXECUTION_START_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    _GLOBAL_LOGGER.info(f"   日誌檔案: {_GLOBAL_LOG_FILE}")
    _GLOBAL_LOGGER.info("=" * 70)
    
    return _GLOBAL_LOGGER


class AutomationLogger:
    """
    自動化腳本專用日誌記錄器
    
    所有模組共用同一個底層 logger，但各自標識模組名稱
    """
    
    def __init__(self, module_name: str = "Main"):
        """
        初始化日誌記錄器
        
        Args:
            module_name: 模組名稱（用於日誌中的標識）
        """
        self.module_name = module_name
        self._logger = _initialize_global_logger()
    
    def _format_message(self, message: str) -> str:
        """格式化訊息，加入模組標識"""
        return f"[{self.module_name}] {message}"
    
    def debug(self, message: str):
        """記錄除錯訊息"""
        self._logger.debug(self._format_message(message))
    
    def info(self, message: str):
        """記錄一般訊息"""
        self._logger.info(self._format_message(message))
    
    def warning(self, message: str):
        """記錄警告訊息"""
        self._logger.warning(self._format_message(message))
    
    def error(self, message: str):
        """記錄錯誤訊息"""
        self._logger.error(self._format_message(message))
    
    def critical(self, message: str):
        """記錄嚴重錯誤訊息"""
        self._logger.critical(self._format_message(message))
    
    def log(self, message: str):
        """記錄一般訊息（info 的別名，相容舊 API）"""
        self.info(message)
    
    def success(self, message: str = "處理成功"):
        """記錄成功訊息"""
        self.info(f"✅ {message}")
    
    def failed(self, message: str = "處理失敗"):
        """記錄失敗訊息"""
        self.error(f"❌ {message}")
    
    # ========== 結構化日誌方法 ==========
    
    def create_separator(self, title: str = ""):
        """創建分隔線"""
        if title:
            # 計算填充
            total_width = 70
            title_with_space = f" {title} "
            padding_total = total_width - len(title_with_space)
            left_padding = padding_total // 2
            right_padding = padding_total - left_padding
            separator = "=" * left_padding + title_with_space + "=" * right_padding
        else:
            separator = "=" * 70
        self._logger.info(separator)
    
    def project_start(self, project_name: str):
        """記錄專案開始處理"""
        self.create_separator(f"專案: {project_name}")
        self.info(f"🚀 開始處理專案")
    
    def project_success(self, project_name: str, elapsed_time: float = None):
        """記錄專案處理成功"""
        time_info = f" (耗時: {elapsed_time:.2f}秒)" if elapsed_time else ""
        self.info(f"✅ 專案處理成功{time_info}")
    
    def project_failed(self, project_name: str, error_msg: str, elapsed_time: float = None):
        """記錄專案處理失敗"""
        time_info = f" (耗時: {elapsed_time:.2f}秒)" if elapsed_time else ""
        self.error(f"❌ 專案處理失敗{time_info}")
        self.error(f"   錯誤: {error_msg}")
    
    def phase_start(self, phase_name: str, details: str = ""):
        """記錄階段開始"""
        msg = f"▶️  {phase_name}"
        if details:
            msg += f" - {details}"
        self.info(msg)
    
    def phase_end(self, phase_name: str, success: bool = True):
        """記錄階段結束"""
        emoji = "✅" if success else "❌"
        status = "完成" if success else "失敗"
        self.info(f"{emoji} {phase_name} {status}")
    
    def scan_result(self, scanner: str, vuln_count: int, file_path: str = ""):
        """記錄掃描結果"""
        if vuln_count > 0:
            self.info(f"🚨 {scanner}: 發現 {vuln_count} 個漏洞" + (f" ({file_path})" if file_path else ""))
        else:
            self.info(f"✅ {scanner}: 無漏洞" + (f" ({file_path})" if file_path else ""))
    
    def copilot_interaction(self, action: str, status: str, details: str = ""):
        """記錄 Copilot 互動操作"""
        emoji = "✅" if status == "SUCCESS" else "❌" if status == "ERROR" else "ℹ️"
        message = f"{emoji} {action}"
        if details:
            message += f" - {details}"
        
        if status == "ERROR":
            self.error(message)
        else:
            self.info(message)
    
    def image_recognition(self, image_name: str, found: bool, confidence: float = 0.0):
        """記錄圖像識別結果"""
        if found:
            self.debug(f"🔍 圖像識別: {image_name} - 找到 (信心度: {confidence:.2f})")
        else:
            self.debug(f"🔍 圖像識別: {image_name} - 未找到")
    
    def retry_attempt(self, context: str, attempt: int, max_attempts: int):
        """記錄重試嘗試"""
        self.warning(f"🔄 重試: {context} (第 {attempt}/{max_attempts} 次)")
    
    def batch_summary(self, total: int, success: int, failed: int, elapsed_time: float):
        """記錄批次處理摘要"""
        success_rate = (success / total * 100) if total > 0 else 0
        self.create_separator("執行摘要")
        self.info(f"📊 總專案數: {total}")
        self.info(f"   ✅ 成功: {success}")
        self.info(f"   ❌ 失敗: {failed}")
        self.info(f"   📈 成功率: {success_rate:.1f}%")
        self.info(f"   ⏱️  總耗時: {elapsed_time:.2f}秒")
    
    def emergency_stop(self, reason: str):
        """記錄緊急停止"""
        self.critical(f"🛑 緊急停止 - 原因: {reason}")
    
    @staticmethod
    def get_log_file_path() -> Optional[str]:
        """取得當前日誌檔案路徑"""
        return str(_GLOBAL_LOG_FILE) if _GLOBAL_LOG_FILE else None
    
    @staticmethod
    def get_execution_start_time() -> Optional[datetime]:
        """取得執行開始時間"""
        return _EXECUTION_START_TIME


# ========== 便捷函數 ==========

def get_logger(module_name: str = "Main") -> AutomationLogger:
    """
    取得日誌記錄器實例
    
    Args:
        module_name: 模組名稱
        
    Returns:
        AutomationLogger: 日誌記錄器實例
    """
    return AutomationLogger(module_name)


def finalize_logging():
    """
    結束日誌記錄（在程式結束時呼叫）
    """
    global _GLOBAL_LOGGER, _EXECUTION_START_TIME
    
    if _GLOBAL_LOGGER and _EXECUTION_START_TIME:
        end_time = datetime.now()
        elapsed = (end_time - _EXECUTION_START_TIME).total_seconds()
        
        _GLOBAL_LOGGER.info("=" * 70)
        _GLOBAL_LOGGER.info(f"🏁 Copilot Automation 執行結束")
        _GLOBAL_LOGGER.info(f"   結束時間: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        _GLOBAL_LOGGER.info(f"   總執行時間: {elapsed:.2f} 秒")
        _GLOBAL_LOGGER.info(f"   日誌檔案: {_GLOBAL_LOG_FILE}")
        _GLOBAL_LOGGER.info("=" * 70)
