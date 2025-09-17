# -*- coding: utf-8 -*-
"""
Hybrid UI Automation Script - 錯誤處理與恢復模組
處理異常情況、失敗重試、緊急停止等機制
"""

import time
import traceback
import signal
import sys
from pathlib import Path
from typing import Optional, Callable, Any, Dict, List, Tuple
from functools import wraps
from enum import Enum

# 導入配置和日誌
sys.path.append(str(Path(__file__).parent.parent))
from config.config import config
from src.logger import get_logger

class ErrorType(Enum):
    """錯誤類型枚舉"""
    VSCODE_ERROR = "vscode_error"
    COPILOT_ERROR = "copilot_error"
    IMAGE_RECOGNITION_ERROR = "image_recognition_error"
    PROJECT_ERROR = "project_error"
    SYSTEM_ERROR = "system_error"
    USER_INTERRUPT = "user_interrupt"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"

class RecoveryAction(Enum):
    """恢復動作枚舉"""
    RETRY = "retry"
    SKIP = "skip"
    RESTART_VSCODE = "restart_vscode"
    CLEAN_ENVIRONMENT = "clean_environment"
    ABORT = "abort"
    CONTINUE = "continue"

class AutomationError(Exception):
    """自動化腳本專用異常類"""
    
    def __init__(self, message: str, error_type: ErrorType = ErrorType.UNKNOWN_ERROR, 
                 recoverable: bool = True, suggested_action: RecoveryAction = RecoveryAction.RETRY):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.recoverable = recoverable
        self.suggested_action = suggested_action
        self.timestamp = time.time()

class ErrorHandler:
    """錯誤處理器"""
    
    def __init__(self):
        """初始化錯誤處理器"""
        self.logger = get_logger("ErrorHandler")
        self.error_count = 0
        self.error_history: List[Dict] = []
        self.emergency_stop_requested = False
        self.max_consecutive_errors = 10  # 增加到10次，提高容錯性
        self.consecutive_errors = 0
        
        # 設定信號處理器（緊急停止）
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)
        
        self.logger.info("錯誤處理器初始化完成")
    
    def _handle_interrupt(self, signum, frame):
        """處理中斷信號"""
        self.logger.emergency_stop(f"收到中斷信號 {signum}")
        self.emergency_stop_requested = True
    
    def handle_error(self, error: Exception, context: str = "", 
                    error_type: ErrorType = None, recoverable: bool = True) -> RecoveryAction:
        """
        處理錯誤並決定恢復策略
        
        Args:
            error: 異常對象
            context: 錯誤上下文
            error_type: 錯誤類型
            recoverable: 是否可恢復
            
        Returns:
            RecoveryAction: 建議的恢復動作
        """
        try:
            if isinstance(error, KeyboardInterrupt):
                self.logger.critical("🛑 緊急停止 - 原因: 用戶中斷 (KeyboardInterrupt)")
                sys.exit(130)
            self.error_count += 1
            self.consecutive_errors += 1
            
            # 如果是 AutomationError，使用其內建資訊
            if isinstance(error, AutomationError):
                error_type = error.error_type
                recoverable = error.recoverable
                suggested_action = error.suggested_action
            else:
                if error_type is None:
                    error_type = self._classify_error(error)
                suggested_action = self._suggest_recovery_action(error_type, recoverable)
            
            # 記錄錯誤
            error_record = {
                "timestamp": time.time(),
                "error_type": error_type.value,
                "message": str(error),
                "context": context,
                "recoverable": recoverable,
                "suggested_action": suggested_action.value,
                "traceback": traceback.format_exc()
            }
            self.error_history.append(error_record)
            
            # 記錄到日誌
            self.logger.error(f"[{error_type.value}] {context}: {str(error)}")
            
            # 檢查是否需要緊急停止
            if self._should_emergency_stop():
                self.logger.emergency_stop("連續錯誤過多或收到停止請求")
                return RecoveryAction.ABORT
            
            # 返回建議的恢復動作
            self.logger.warning(f"建議恢復動作: {suggested_action.value}")
            return suggested_action
            
        except Exception as handler_error:
            self.logger.critical(f"錯誤處理器本身發生錯誤: {str(handler_error)}")
            return RecoveryAction.ABORT
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """
        分類錯誤類型
        
        Args:
            error: 異常對象
            
        Returns:
            ErrorType: 錯誤類型
        """
        error_msg = str(error).lower()
        
        if "timeout" in error_msg:
            return ErrorType.TIMEOUT_ERROR
        elif "vscode" in error_msg or "code" in error_msg:
            return ErrorType.VSCODE_ERROR
        elif "copilot" in error_msg:
            return ErrorType.COPILOT_ERROR
        elif "image" in error_msg or "screenshot" in error_msg:
            return ErrorType.IMAGE_RECOGNITION_ERROR
        elif "project" in error_msg or "file" in error_msg:
            return ErrorType.PROJECT_ERROR
        elif isinstance(error, KeyboardInterrupt):
            return ErrorType.USER_INTERRUPT
        elif isinstance(error, (OSError, IOError, SystemError)):
            return ErrorType.SYSTEM_ERROR
        else:
            return ErrorType.UNKNOWN_ERROR
    
    def _suggest_recovery_action(self, error_type: ErrorType, recoverable: bool) -> RecoveryAction:
        """
        建議恢復動作
        
        Args:
            error_type: 錯誤類型
            recoverable: 是否可恢復
            
        Returns:
            RecoveryAction: 建議的恢復動作
        """
        if not recoverable:
            return RecoveryAction.ABORT
        
        if error_type == ErrorType.USER_INTERRUPT:
            return RecoveryAction.ABORT
        elif error_type == ErrorType.VSCODE_ERROR:
            # VS Code 錯誤時，首先嘗試清理環境，而不是立即重啟
            # 這樣可以避免強制終止導致的崩潰
            return RecoveryAction.CLEAN_ENVIRONMENT
        elif error_type == ErrorType.COPILOT_ERROR:
            return RecoveryAction.RETRY
        elif error_type == ErrorType.IMAGE_RECOGNITION_ERROR:
            return RecoveryAction.RETRY
        elif error_type == ErrorType.PROJECT_ERROR:
            return RecoveryAction.SKIP
        elif error_type == ErrorType.TIMEOUT_ERROR:
            return RecoveryAction.RETRY
        elif error_type == ErrorType.SYSTEM_ERROR:
            return RecoveryAction.CLEAN_ENVIRONMENT
        else:
            return RecoveryAction.RETRY
    
    def _should_emergency_stop(self) -> bool:
        """
        判斷是否應該緊急停止
        
        Returns:
            bool: 是否應該停止
        """
        if self.emergency_stop_requested:
            return True
        
        if self.consecutive_errors >= self.max_consecutive_errors:
            self.logger.error(f"連續錯誤次數達到上限 ({self.max_consecutive_errors})")
            return True
        
        return False
    
    def reset_consecutive_errors(self):
        """重設連續錯誤計數"""
        if self.consecutive_errors > 0:
            self.logger.info(f"重設連續錯誤計數 (之前: {self.consecutive_errors})")
            self.consecutive_errors = 0
    
    def get_error_summary(self) -> Dict:
        """
        取得錯誤摘要統計
        
        Returns:
            Dict: 錯誤摘要
        """
        if not self.error_history:
            return {"total_errors": 0}
        
        error_types = {}
        for record in self.error_history:
            error_type = record["error_type"]
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        recent_errors = [r for r in self.error_history if time.time() - r["timestamp"] < 3600]  # 最近一小時
        
        return {
            "total_errors": len(self.error_history),
            "recent_errors": len(recent_errors),
            "consecutive_errors": self.consecutive_errors,
            "error_types": error_types,
            "last_error": self.error_history[-1] if self.error_history else None
        }

class RetryHandler:
    """重試處理器"""
    
    def __init__(self, error_handler: ErrorHandler):
        """初始化重試處理器"""
        self.error_handler = error_handler
        self.logger = get_logger("RetryHandler")
        self.logger.info("重試處理器初始化完成")
    
    def retry_with_backoff(self, func: Callable, max_attempts: int = None,
                          backoff_factor: float = 2.0, initial_delay: float = 1.0,
                          context: str = "", *args, **kwargs) -> Tuple[bool, Any]:
        """
        使用指數退避策略重試函數
        
        Args:
            func: 要重試的函數
            max_attempts: 最大重試次數
            backoff_factor: 退避因子
            initial_delay: 初始延遲時間
            context: 重試上下文
            *args, **kwargs: 函數參數
            
        Returns:
            Tuple[bool, Any]: (是否成功, 結果)
        """
        if max_attempts is None:
            max_attempts = config.MAX_RETRY_ATTEMPTS
        
        delay = initial_delay
        
        for attempt in range(1, max_attempts + 1):
            try:
                self.logger.info(f"嘗試執行 {context} (第 {attempt}/{max_attempts} 次)")
                result = func(*args, **kwargs)
                
                # 成功時重設連續錯誤計數
                self.error_handler.reset_consecutive_errors()
                self.logger.info(f"✅ {context} 執行成功")
                return True, result
                
            except Exception as e:
                recovery_action = self.error_handler.handle_error(
                    e, f"{context} (嘗試 {attempt}/{max_attempts})"
                )
                
                if recovery_action == RecoveryAction.ABORT:
                    self.logger.error(f"❌ {context} 中止執行")
                    return False, None
                
                if attempt < max_attempts:
                    if recovery_action == RecoveryAction.SKIP:
                        self.logger.warning(f"⏭️ {context} 跳過此次嘗試")
                        return False, None
                    
                    self.logger.warning(f"⏱️ {context} 等待 {delay:.1f} 秒後重試...")
                    time.sleep(delay)
                    delay *= backoff_factor
                else:
                    self.logger.error(f"❌ {context} 達到最大重試次數，放棄執行")
                    return False, None
        
        return False, None

def error_handler_decorator(error_type: ErrorType = ErrorType.UNKNOWN_ERROR,
                          recoverable: bool = True,
                          suggested_action: RecoveryAction = RecoveryAction.RETRY):
    """
    錯誤處理裝飾器
    
    Args:
        error_type: 預設錯誤類型
        recoverable: 是否可恢復
        suggested_action: 建議恢復動作
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 如果不是 AutomationError，包裝成 AutomationError
                if not isinstance(e, AutomationError):
                    raise AutomationError(
                        str(e), error_type, recoverable, suggested_action
                    ) from e
                else:
                    raise
        return wrapper
    return decorator

class RecoveryManager:
    """恢復管理器"""
    
    def __init__(self):
        """初始化恢復管理器"""
        self.logger = get_logger("RecoveryManager")
        self.logger.info("恢復管理器初始化完成")
    
    def execute_recovery_action(self, action: RecoveryAction, context: str = "") -> bool:
        """
        執行恢復動作
        
        Args:
            action: 恢復動作
            context: 上下文
            
        Returns:
            bool: 恢復是否成功
        """
        try:
            self.logger.info(f"執行恢復動作: {action.value} ({context})")
            
            if action == RecoveryAction.RETRY:
                # 簡單等待後重試
                time.sleep(2)
                return True
                
            elif action == RecoveryAction.SKIP:
                # 跳過當前操作
                self.logger.warning("跳過當前操作")
                return True
                
            elif action == RecoveryAction.RESTART_VSCODE:
                # 重啟 VS Code
                return self._restart_vscode()
                
            elif action == RecoveryAction.CLEAN_ENVIRONMENT:
                # 清理環境
                return self._clean_environment()
                
            elif action == RecoveryAction.ABORT:
                # 中止執行
                self.logger.critical("中止自動化執行")
                return False
                
            elif action == RecoveryAction.CONTINUE:
                # 繼續執行
                return True
                
            else:
                self.logger.warning(f"未知的恢復動作: {action.value}")
                return False
                
        except Exception as e:
            self.logger.error(f"執行恢復動作時發生錯誤: {str(e)}")
            return False
    
    def _restart_vscode(self) -> bool:
        """重啟 VS Code"""
        try:
            # 這裡需要導入 vscode_controller，但要避免循環導入
            # 使用延遲導入
            from src.vscode_controller import ensure_clean_environment
            return ensure_clean_environment()
        except Exception as e:
            self.logger.error(f"重啟 VS Code 失敗: {str(e)}")
            return False
    
    def _clean_environment(self) -> bool:
        """清理環境"""
        try:
            self.logger.info("開始清理環境...")
            
            # 導入 vscode_controller，使用延遲導入避免循環依賴
            from src.vscode_controller import ensure_clean_environment
            
            # 先嘗試優雅關閉
            self.logger.info("嘗試優雅關閉所有VS Code實例...")
            result = ensure_clean_environment()
            
            if not result:
                self.logger.warning("優雅關閉失敗，等待系統穩定...")
                # 等待更長時間讓系統穩定
                time.sleep(10)
                
                # 再次嘗試清理
                self.logger.info("重新嘗試清理環境...")
                result = ensure_clean_environment()
            
            if result:
                self.logger.info("✅ 環境清理成功")
            else:
                self.logger.warning("⚠️ 環境清理可能未完全成功，但繼續執行")
            
            # 額外等待時間確保系統穩定
            time.sleep(3)
            
            return True  # 即使清理未完全成功也返回True，允許繼續執行
            
        except Exception as e:
            self.logger.error(f"清理環境失敗: {str(e)}")
            return False

# 創建全域實例
error_handler = ErrorHandler()
retry_handler = RetryHandler(error_handler)
recovery_manager = RecoveryManager()

# 便捷函數
def handle_error(error: Exception, context: str = "") -> RecoveryAction:
    """處理錯誤的便捷函數"""
    return error_handler.handle_error(error, context)

def retry_operation(func: Callable, max_attempts: int = None, context: str = "", *args, **kwargs):
    """重試操作的便捷函數"""
    return retry_handler.retry_with_backoff(func, max_attempts, context=context, *args, **kwargs)

def execute_recovery(action: RecoveryAction, context: str = "") -> bool:
    """執行恢復的便捷函數"""
    return recovery_manager.execute_recovery_action(action, context)

def get_error_summary() -> Dict:
    """取得錯誤摘要的便捷函數"""
    return error_handler.get_error_summary()