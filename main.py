# -*- coding: utf-8 -*-
"""
Hybrid UI Automation Script - 主控制腳本
整合所有模組，實作完整的自動化流程控制
"""

import time
import sys
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# 設定模組搜尋路徑
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))

# 導入所有模組
from config.config import config
from src.logger import get_logger, create_project_logger
from src.project_manager import ProjectManager, ProjectInfo
from src.vscode_controller import VSCodeController
from src.copilot_handler import CopilotHandler
from src.image_recognition import ImageRecognition
from src.ui_manager import UIManager
from src.error_handler import (
    ErrorHandler, RetryHandler, RecoveryManager,
    AutomationError, ErrorType, RecoveryAction
)

class HybridUIAutomationScript:
    """混合式 UI 自動化腳本主控制器"""
    
    def __init__(self):
        """初始化主控制器"""
        self.logger = get_logger("MainController")
        
        # 初始化各個模組
        self.project_manager = ProjectManager()
        self.vscode_controller = VSCodeController()
        self.error_handler = ErrorHandler()
        self.copilot_handler = CopilotHandler(self.error_handler)  # 傳入 error_handler
        self.image_recognition = ImageRecognition()
        self.retry_handler = RetryHandler(self.error_handler)
        self.recovery_manager = RecoveryManager()
        self.ui_manager = UIManager()
        
        # 執行選項
        self.use_smart_wait = True  # 預設使用智能等待
        
        # 執行統計
        self.total_projects = 0
        self.processed_projects = 0
        self.successful_projects = 0
        self.failed_projects = 0
        self.skipped_projects = 0
        self.start_time = None
        
        self.logger.info("混合式 UI 自動化腳本初始化完成")
    
    def run(self) -> bool:
        """
        執行完整的自動化流程
        
        Returns:
            bool: 執行是否成功
        """
        try:
            self.start_time = time.time()
            self.logger.create_separator("開始執行自動化腳本")
            
            # 顯示選項對話框
            reset_selected, self.use_smart_wait = self.ui_manager.show_options_dialog()
            
            # 如果選擇重置，執行重置腳本
            if reset_selected:
                self.logger.info("使用者選擇執行專案狀態重置")
                if not self.ui_manager.execute_reset_if_needed(True):
                    self.logger.error("重置專案狀態失敗")
                    return False
            
            self.logger.info(f"使用者選擇{'啟用' if self.use_smart_wait else '停用'}智能等待功能")
            
            # 前置檢查
            if not self._pre_execution_checks():
                return False
            
            # 掃描專案
            projects = self.project_manager.scan_projects()
            if not projects:
                self.logger.error("沒有找到任何專案，結束執行")
                return False
            
            self.total_projects = len(projects)
            self.logger.info(f"總共發現 {self.total_projects} 個專案")
            
            # 取得待處理專案
            pending_projects = self.project_manager.get_pending_projects()
            if not pending_projects:
                self.logger.info("所有專案都已處理完成")
                return True
            
            self.logger.info(f"待處理專案: {len(pending_projects)} 個")
            
            # 分批處理專案
            batches = self.project_manager.get_project_batches()
            self.logger.info(f"將分 {len(batches)} 批處理")
            
            # 執行各批次
            for batch_num, batch in enumerate(batches, 1):
                # 檢查是否收到中斷請求
                if self.error_handler.emergency_stop_requested:
                    self.logger.warning("收到中斷請求，停止處理")
                    break
                    
                self.logger.create_separator(f"處理第 {batch_num}/{len(batches)} 批")
                
                if not self._process_batch(batch, batch_num):
                    self.logger.warning(f"第 {batch_num} 批處理失敗，繼續下一批")
                
                # 檢查是否收到中斷請求（批次完成後）
                if self.error_handler.emergency_stop_requested:
                    self.logger.warning("收到中斷請求，停止處理")
                    break
                
                # 批次間休息（可選）
                if batch_num < len(batches):
                    self.logger.info("批次間休息 30 秒...")
                    # 在休息期間也檢查中斷請求
                    for i in range(30):
                        if self.error_handler.emergency_stop_requested:
                            self.logger.warning("收到中斷請求，停止休息")
                            break
                        time.sleep(1)
            
            # 處理失敗的專案（重試）
            if not self.error_handler.emergency_stop_requested:
                self._handle_failed_projects()
            
            # 生成最終報告
            if not self.error_handler.emergency_stop_requested:
                self._generate_final_report()
            
            return True
            
        except KeyboardInterrupt:
            self.logger.warning("收到 Ctrl+C 中斷請求")
            self.error_handler.emergency_stop_requested = True
            return False
        except Exception as e:
            recovery_action = self.error_handler.handle_error(e, "主流程執行")
            if recovery_action == RecoveryAction.ABORT:
                self.logger.critical("主流程執行失敗，中止自動化")
                return False
            else:
                self.logger.warning("主流程遇到錯誤但嘗試繼續執行")
                return False
        
        finally:
            # 清理環境
            self._cleanup()
    
    def _pre_execution_checks(self) -> bool:
        """
        執行前檢查
        
        Returns:
            bool: 檢查是否通過
        """
        try:
            self.logger.info("執行前置檢查...")
            
            # 檢查配置
            config.ensure_directories()
            
            # 檢查圖像資源
            if not self.image_recognition.validate_required_images():
                self.logger.warning("圖像資源驗證失敗，但繼續執行（使用替代方案）")
                # 可以選擇中止或繼續
                # return False
            
            # 確保乾淨的執行環境
            if not self.vscode_controller.ensure_clean_environment():
                self.logger.error("無法確保乾淨的執行環境")
                return False
            
            self.logger.info("✅ 前置檢查完成")
            return True
            
        except Exception as e:
            self.logger.error(f"前置檢查失敗: {str(e)}")
            return False
    
    def _process_batch(self, projects: List[ProjectInfo], batch_num: int) -> bool:
        """
        處理一批專案
        
        Args:
            projects: 專案列表
            batch_num: 批次編號
            
        Returns:
            bool: 批次處理是否成功
        """
        try:
            batch_start_time = time.time()
            batch_success = 0
            batch_failed = 0
            
            for i, project in enumerate(projects, 1):
                self.logger.info(f"處理專案 {i}/{len(projects)}: {project.name}")
                
                # 檢查是否需要緊急停止
                if self.error_handler.emergency_stop_requested:
                    self.logger.warning("收到緊急停止請求，中止批次處理")
                    break
                
                # 處理單一專案
                success = self._process_single_project(project)
                
                if success:
                    batch_success += 1
                    self.successful_projects += 1
                else:
                    batch_failed += 1
                    self.failed_projects += 1
                
                self.processed_projects += 1
                
                # 項目間短暫休息
                time.sleep(2)
            
            # 批次摘要
            batch_elapsed = time.time() - batch_start_time
            self.logger.info(f"第 {batch_num} 批完成: 成功 {batch_success}, 失敗 {batch_failed}, 耗時 {batch_elapsed:.1f}秒")
            
            return True
            
        except Exception as e:
            self.logger.error(f"處理第 {batch_num} 批時發生錯誤: {str(e)}")
            return False
    
    def _process_single_project(self, project: ProjectInfo) -> bool:
        """
        處理單一專案
        
        Args:
            project: 專案資訊
            
        Returns:
            bool: 處理是否成功
        """
        project_logger = None
        start_time = time.time()
        
        try:
            # 檢查是否收到中斷請求
            if self.error_handler.emergency_stop_requested:
                self.logger.warning(f"收到中斷請求，跳過專案: {project.name}")
                return False
            
            # 創建專案專用日誌
            project_logger = create_project_logger(project.name)
            project_logger.log("開始處理專案")
            
            # 更新專案狀態為處理中
            self.project_manager.update_project_status(project.name, "processing")
            
            # 使用重試機制處理專案
            success, result = self.retry_handler.retry_with_backoff(
                self._execute_project_automation,
                max_attempts=config.MAX_RETRY_ATTEMPTS,
                context=f"專案 {project.name}",
                project=project,
                project_logger=project_logger
            )
            
            # 計算處理時間
            processing_time = time.time() - start_time
            
            if success:
                # 標記專案完成
                self.project_manager.mark_project_completed(project.name, processing_time)
                project_logger.success()
                self.error_handler.reset_consecutive_errors()
                return True
            else:
                # 標記專案失敗
                error_msg = result if isinstance(result, str) else "處理失敗"
                self.project_manager.mark_project_failed(project.name, error_msg, processing_time)
                project_logger.failed(error_msg)
                return False
                
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            
            self.project_manager.mark_project_failed(project.name, error_msg, processing_time)
            
            if project_logger:
                project_logger.failed(error_msg)
            
            self.logger.error(f"處理專案 {project.name} 時發生未捕獲的錯誤: {error_msg}")
            return False
    
    def _execute_project_automation(self, project: ProjectInfo, project_logger) -> bool:
        """
        執行專案自動化的核心邏輯
        
        Args:
            project: 專案資訊
            project_logger: 專案日誌記錄器
            
        Returns:
            bool: 執行是否成功
        """
        try:
            # 檢查中斷請求
            if self.error_handler.emergency_stop_requested:
                raise AutomationError("收到中斷請求", ErrorType.USER_INTERRUPT)
            
            # 步驟1: 開啟專案
            project_logger.log("開啟 VS Code 專案")
            if not self.vscode_controller.open_project(project.path):
                raise AutomationError("無法開啟專案", ErrorType.VSCODE_ERROR)
            
            # 檢查中斷請求
            if self.error_handler.emergency_stop_requested:
                raise AutomationError("收到中斷請求", ErrorType.USER_INTERRUPT)
            
            # 步驟2: 清除 Copilot 記憶
            project_logger.log("清除 Copilot Chat 記憶")
            if not self.vscode_controller.clear_copilot_memory():
                self.logger.warning("Copilot 記憶清除失敗，但繼續執行")
            
            # 檢查中斷請求
            if self.error_handler.emergency_stop_requested:
                raise AutomationError("收到中斷請求", ErrorType.USER_INTERRUPT)
            
            # 步驟3: 處理 Copilot Chat（使用使用者選擇的等待模式）
            project_logger.log(f"處理 Copilot Chat (智能等待: {'開啟' if self.use_smart_wait else '關閉'})")
            success, error_msg = self.copilot_handler.process_project_complete(
                project.path, use_smart_wait=self.use_smart_wait
            )
            
            if not success:
                raise AutomationError(
                    error_msg or "Copilot 處理失敗", 
                    ErrorType.COPILOT_ERROR
                )
            
            # 檢查中斷請求
            if self.error_handler.emergency_stop_requested:
                raise AutomationError("收到中斷請求", ErrorType.USER_INTERRUPT)
            
            # 步驟4: 驗證結果
            project_logger.log("驗證處理結果")
            script_root = Path(__file__).parent  # 腳本根目錄
            execution_result_dir = script_root / "ExecutionResult" / "Success"
            project_name = Path(project.path).name
            has_success_file = execution_result_dir.exists() and any(execution_result_dir.glob(f"{project_name}_Copilot_AutoComplete_*.md"))
            if not has_success_file:
                raise AutomationError("缺少成功執行結果檔案", ErrorType.PROJECT_ERROR)
            
            # 步驟5: 智能關閉專案（確保 Copilot 回應完成）
            project_logger.log("智能關閉專案並清除記憶")
            if not self._smart_close_project():
                self.logger.warning("專案關閉失敗，但處理已完成")
            
            project_logger.log("專案處理完成")
            return True
            
        except AutomationError:
            raise
        except Exception as e:
            raise AutomationError(str(e), ErrorType.UNKNOWN_ERROR)
    
    def _smart_close_project(self) -> bool:
        """
        智能關閉專案，確保 Copilot 回應完成
        
        Returns:
            bool: 關閉是否成功
        """
        try:
            # 如果使用智能等待，表示已經在 _smart_wait_for_response 中等待回應完成
            # 但我們仍需要進行最後確認
            if self.use_smart_wait:
                self.logger.info("使用智能等待模式，進行最後確認...")
                
                # 最後一次確認回應內容
                self.logger.info("最後確認 Copilot 回應...")
                final_response = self.copilot_handler.copy_response()
                
                if final_response and len(final_response) > 100:
                    self.logger.info(f"✅ 確認收到完整回應 ({len(final_response)} 字元)")
                    
                    # 等待3秒確保所有操作完成
                    self.logger.info("等待 3 秒確保所有操作完成...")
                    time.sleep(3)
                    
                    # 嘗試正常關閉
                    return self.vscode_controller.close_current_project(force=False)
                else:
                    self.logger.warning("⚠️ 最後確認時未能獲取到有效回應，但仍嘗試關閉")
                    return self.vscode_controller.close_current_project(force=False)
                
            # 固定等待模式下需要進行額外檢查
            max_attempts = 3
            for attempt in range(max_attempts):
                self.logger.debug(f"嘗試關閉專案 (第 {attempt + 1}/{max_attempts} 次)")
                
                # 先嘗試最後一次複製
                self.logger.info("關閉前嘗試再次複製回應...")
                response = self.copilot_handler.copy_response()
                
                if response and len(response) > 50:
                    self.logger.info(f"✅ 獲取到回應內容 ({len(response)} 字元)")
                else:
                    self.logger.warning("⚠️ 未能獲取到有效回應內容")
                
                # 等待一小段時間確認回應已完成
                time.sleep(3)
                
                # 測試是否可以關閉
                if self.vscode_controller.close_current_project(force=False):
                    self.logger.info("✅ VS Code 成功關閉，Copilot 回應已完成")
                    return True
                else:
                    if attempt < max_attempts - 1:
                        self.logger.info("VS Code 無法正常關閉，可能 Copilot 仍在回應中，等待後重試...")
                        time.sleep(5)  # 增加等待時間
                        continue
                    else:
                        self.logger.warning("達到最大重試次數，強制關閉 VS Code")
                        return self.vscode_controller.close_current_project(force=True)
            
            return False
            
        except Exception as e:
            self.logger.error(f"智能關閉專案時發生錯誤: {str(e)}")
            # 發生錯誤時，嘗試強制關閉
            return self.vscode_controller.close_current_project(force=True)
    
    def _handle_failed_projects(self):
        """處理失敗的專案（重試機制）"""
        try:
            retry_projects = self.project_manager.get_retry_projects()
            
            if not retry_projects:
                self.logger.info("沒有需要重試的專案")
                return
            
            self.logger.create_separator(f"重試失敗專案 ({len(retry_projects)} 個)")
            
            for project in retry_projects:
                self.logger.info(f"重試專案: {project.name} (第 {project.retry_count + 1} 次)")
                
                # 重設專案狀態為待處理
                self.project_manager.update_project_status(project.name, "pending")
                
                # 重新處理
                success = self._process_single_project(project)
                
                if success:
                    self.logger.info(f"✅ 專案 {project.name} 重試成功")
                else:
                    self.logger.warning(f"❌ 專案 {project.name} 重試仍然失敗")
                
                time.sleep(5)  # 重試間休息
                
        except Exception as e:
            self.logger.error(f"處理重試專案時發生錯誤: {str(e)}")
    
    def _generate_final_report(self):
        """生成最終報告"""
        try:
            end_time = time.time()
            total_elapsed = end_time - self.start_time if self.start_time else 0
            
            # 生成摘要
            self.logger.create_separator("執行完成摘要")
            self.logger.batch_summary(
                self.total_projects,
                self.successful_projects,
                self.failed_projects,
                total_elapsed
            )
            
            # 錯誤摘要
            error_summary = self.error_handler.get_error_summary()
            if error_summary.get("total_errors", 0) > 0:
                self.logger.warning(f"總錯誤次數: {error_summary['total_errors']}")
                self.logger.warning(f"最近錯誤: {error_summary['recent_errors']}")
            
            # 保存專案摘要報告
            report_file = self.project_manager.save_summary_report()
            if report_file:
                self.logger.info(f"詳細報告已儲存: {report_file}")
            
        except Exception as e:
            self.logger.error(f"生成最終報告時發生錯誤: {str(e)}")
    
    def _cleanup(self):
        """清理環境"""
        try:
            self.logger.info("清理執行環境...")
            
            # 確保 VS Code 已關閉
            self.vscode_controller.ensure_clean_environment()
            
            # 可以添加其他清理邏輯
            
            self.logger.info("✅ 環境清理完成")
            
        except Exception as e:
            self.logger.error(f"清理環境時發生錯誤: {str(e)}")

def main():
    """主函數"""
    try:
        print("=" * 60)
        print("混合式 UI 自動化腳本")
        print("Hybrid UI Automation Script")
        print("=" * 60)
        
        # 創建並運行腳本
        automation_script = HybridUIAutomationScript()
        success = automation_script.run()
        
        if success:
            print("✅ 自動化腳本執行完成")
            return 0
        else:
            print("❌ 自動化腳本執行失敗")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️ 用戶中斷執行")
        return 2
    except Exception as e:
        print(f"💥 發生未預期的錯誤: {str(e)}")
        return 3

if __name__ == "__main__":
    exit(main())