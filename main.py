# -*- coding: utf-8 -*-
"""
Hybrid UI Automation Script - 主控制腳本
整合所有模組，實作完整的自動化流程控制
"""

import time
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
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
    ErrorHandler, RecoveryManager,
    AutomationError, ErrorType, RecoveryAction
)
from src.cwe_scan_manager import CWEScanManager
from src.cwe_scan_ui import show_cwe_scan_settings
from src.checkpoint_manager import CheckpointManager, check_for_resumable_execution

class HybridUIAutomationScript:
    """混合式 UI 自動化腳本主控制器"""
    
    def __init__(self):
        """初始化主控制器"""
        self.logger = get_logger("MainController")
        
        # 初始化各個模組
        self.project_manager = ProjectManager()
        self.vscode_controller = VSCodeController()
        self.error_handler = ErrorHandler()
        self.checkpoint_manager = CheckpointManager()  # 檢查點管理器（需先初始化）
        self.copilot_handler = CopilotHandler(
            self.error_handler, 
            interaction_settings=None,
            cwe_scan_manager=None,
            cwe_scan_settings=None,
            checkpoint_manager=self.checkpoint_manager  # 傳遞 checkpoint 管理器
        )  # 初始化時傳入基本參數
        self.image_recognition = ImageRecognition()
        self.recovery_manager = RecoveryManager()
        self.ui_manager = UIManager()
        self.cwe_scan_manager = None  # CWE 掃描管理器（按需初始化）
        
        # 執行選項
        self.use_smart_wait = True  # 預設使用智能等待
        self.interaction_settings = None  # 儲存互動設定
        self.cwe_scan_settings = None  # CWE 掃描設定
        
        # 恢復執行相關
        self.resume_mode = False  # 是否處於恢復模式
        self.resume_project_index = 0  # 恢復起始專案索引
        self.resume_round = 1  # 恢復起始輪數
        self.resume_line = 1  # 恢復起始行數
        self.resume_phase = 1  # 恢復起始階段（AS Mode: 1=Query, 2=Coding）
        
        # 執行統計
        self.total_projects = 0
        self.processed_projects = 0
        self.successful_projects = 0
        self.failed_projects = 0
        self.skipped_projects = 0
        self.start_time = None
        
        # 檔案處理計數器
        self.total_files_processed = 0  # 已處理的檔案數（累計所有專案的 prompt.txt 行數）
        self.max_files_limit = 0  # 最大處理檔案數限制（0 表示無限制）
        
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
            
            # 檢查是否有可恢復的執行記錄
            resume_info = self._check_for_resumable_execution()
            if resume_info:
                # 使用恢復的設定 - 完全自動化，不需要重新設定
                selected_projects = resume_info['project_list']
                self.use_smart_wait = resume_info['settings'].get('use_smart_wait', True)
                self.max_files_limit = resume_info['settings'].get('max_files', 0)
                artificial_suicide_enabled = resume_info['execution_mode'] == 'as'
                artificial_suicide_rounds = resume_info['settings'].get('artificial_suicide_rounds', 10)
                
                # 恢復已處理的檔案計數
                self.total_files_processed = resume_info.get('total_files_processed', 0)
                
                # 設定恢復參數
                self.resume_mode = True
                self.resume_project_index = resume_info['resume_from']['project_index']
                self.resume_round = resume_info['resume_from']['round']
                self.resume_line = resume_info['resume_from']['line']
                self.resume_phase = resume_info['resume_from'].get('phase', 1)  # AS Mode phase
                
                self.logger.info(f"🔄 恢復模式已啟用")
                self.logger.info(f"   從專案索引 {self.resume_project_index} ({resume_info['resume_from']['project_name']}) 開始")
                self.logger.info(f"   從輪數 {self.resume_round}, Phase {self.resume_phase}, 行數 {self.resume_line} 開始")
                self.logger.info(f"   已處理檔案: {self.total_files_processed}/{self.max_files_limit}")
                self.logger.info(f"   剩餘配額: {resume_info.get('remaining_files_quota', 'N/A')}")
            else:
                # 正常啟動流程
                # 顯示選項對話框（包含專案選擇和 Artificial Suicide 設定）
                (selected_projects, self.use_smart_wait, clean_history, 
                 artificial_suicide_enabled, artificial_suicide_rounds,
                 max_files_to_process) = self.ui_manager.show_options_dialog()
                
                # 設定檔案數量限制
                self.max_files_limit = max_files_to_process
                if self.max_files_limit > 0:
                    self.logger.info(f"📊 檔案數量限制已啟用: 最多處理 {self.max_files_limit} 個檔案")
                else:
                    self.logger.info("📊 檔案數量限制未啟用: 將處理所有選定專案")
                
                # 如果需要清理歷史記錄
                if clean_history and selected_projects:
                    self.logger.info(f"清理 {len(selected_projects)} 個專案的執行記錄")
                    if not self.ui_manager.clean_project_history(selected_projects):
                        self.logger.error("清理執行記錄失敗")
                        return False
            
            # 設定互動模式（恢復模式時從檢查點載入）
            if self.resume_mode and resume_info:
                # 從檢查點恢復設定
                self.interaction_settings = resume_info['settings']
                self.cwe_scan_settings = {
                    'enabled': True,
                    'cwe_type': resume_info['settings'].get('cwe_type', '022'),
                    'output_dir': resume_info['settings'].get('cwe_output_dir', str(config.CWE_RESULT_DIR))
                }
                # 如果啟用 CWE 掃描，初始化掃描管理器
                if self.cwe_scan_settings.get('enabled'):
                    self.cwe_scan_manager = CWEScanManager()
                    self.copilot_handler.cwe_scan_manager = self.cwe_scan_manager
                    self.copilot_handler.cwe_scan_settings = self.cwe_scan_settings
                    self.logger.info(f"✅ CWE 掃描已恢復 (類型: CWE-{self.cwe_scan_settings['cwe_type']})")
                
                # 更新 CopilotHandler
                self.copilot_handler = CopilotHandler(
                    self.error_handler,
                    self.interaction_settings,
                    self.cwe_scan_manager,
                    self.cwe_scan_settings,
                    self.checkpoint_manager  # 傳遞 checkpoint 管理器
                )
                self.logger.info(f"✅ 已從檢查點恢復設定: {self.interaction_settings}")
            elif artificial_suicide_enabled:
                # 如果啟用 Artificial Suicide 模式，跳過互動設定並使用預設設定
                self.logger.info(f"🎯 Artificial Suicide 模式已啟用（輪數: {artificial_suicide_rounds}）")
                self.logger.info("跳過互動設定，使用 Artificial Suicide 專用設定")
                
                # 建立 Artificial Suicide 專用設定
                self.interaction_settings = {
                    "enabled": False,  # 停用一般多輪互動
                    "max_rounds": 1,
                    "include_previous_response": False,
                    "round_delay": config.INTERACTION_ROUND_DELAY,
                    "show_ui_on_startup": False,
                    "copilot_chat_modification_action": "revert",  # Artificial Suicide 會自己處理
                    "prompt_source_mode": "project",  # 強制使用專案專用 prompt
                    "artificial_suicide_mode": True,
                    "artificial_suicide_rounds": artificial_suicide_rounds
                }
                # 顯示 CWE 掃描設定選項
                self._show_cwe_scan_settings_dialog()
            else:
                # 一般模式：顯示互動設定選項
                self._show_interaction_settings_dialog()
                # 顯示 CWE 掃描設定選項
                self._show_cwe_scan_settings_dialog()
            
            self.logger.info(f"使用者選擇{'啟用' if self.use_smart_wait else '停用'}智能等待功能")
            self.logger.info(f"選定處理的專案: {', '.join(selected_projects)}")
            
            # 前置檢查
            if not self._pre_execution_checks():
                return False
            
            # 掃描專案
            projects = self.project_manager.scan_projects()
            if not projects:
                self.logger.error("沒有找到任何專案，結束執行")
                return False
            
            # 過濾出使用者選定的專案
            selected_project_list = [
                p for p in projects if p.name in selected_projects
            ]
            
            if not selected_project_list:
                self.logger.error("選定的專案不存在或無法讀取")
                return False
            
            self.total_projects = len(selected_project_list)
            self.logger.info(f"將處理 {self.total_projects} 個選定的專案")
            
            # 建立或更新檢查點（非恢復模式時）
            if not self.resume_mode:
                checkpoint_settings = {
                    'max_rounds': self.interaction_settings.get('max_rounds', 10) if self.interaction_settings else 10,
                    'max_files': self.max_files_limit,
                    'cwe_type': self.cwe_scan_settings.get('cwe_type', '') if self.cwe_scan_settings else '',
                    'cwe_output_dir': str(config.CWE_RESULT_DIR),
                    'cwe_enabled': self.cwe_scan_settings.get('enabled', False) if self.cwe_scan_settings else False,
                    'copilot_chat_modification_action': self.interaction_settings.get('copilot_chat_modification_action', 'revert') if self.interaction_settings else 'revert',
                    'use_coding_instruction': self.interaction_settings.get('use_coding_instruction', False) if self.interaction_settings else False,
                    'use_smart_wait': self.use_smart_wait,
                    'prompt_source_mode': self.interaction_settings.get('prompt_source_mode', 'project') if self.interaction_settings else 'project',
                    'artificial_suicide_mode': self.interaction_settings.get('artificial_suicide_mode', False) if self.interaction_settings else False,
                    'artificial_suicide_rounds': self.interaction_settings.get('artificial_suicide_rounds', 10) if self.interaction_settings else 10,
                    'interaction_enabled': self.interaction_settings.get('interaction_enabled', True) if self.interaction_settings else True,
                    'include_previous_response': self.interaction_settings.get('include_previous_response', False) if self.interaction_settings else False,
                    'round_delay': self.interaction_settings.get('round_delay', 2) if self.interaction_settings else 2
                }
                execution_mode = 'as' if checkpoint_settings.get('artificial_suicide_mode') else 'non_as'
                self.checkpoint_manager.create_checkpoint(
                    execution_mode=execution_mode,
                    project_list=[p.name for p in selected_project_list],
                    settings=checkpoint_settings
                )
                self.logger.info("✅ 已建立執行檢查點")
            
            # 執行所有選定的專案
            if not self._process_all_projects(selected_project_list):
                self.logger.warning("專案處理過程中發生錯誤")
            
            # 檢查是否收到中斷請求
            if self.error_handler.emergency_stop_requested:
                self.logger.warning("收到中斷請求，停止處理")
            
            self.logger.info("所有專案處理完成")
            
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
    
    def _show_interaction_settings_dialog(self):
        """顯示互動設定對話框"""
        try:
            from src.interaction_settings_ui import show_interaction_settings
            self.logger.info("顯示多輪互動設定介面")
            settings = show_interaction_settings()
            
            if settings is None:
                # 使用者取消了設定
                self.logger.info("使用者取消了互動設定，結束腳本執行")
                sys.exit(0)  # 直接退出腳本
            else:
                # 儲存設定並重新初始化 CopilotHandler（加入 CWE 掃描參數）
                self.interaction_settings = settings
                self.copilot_handler = CopilotHandler(
                    self.error_handler, 
                    settings,
                    self.cwe_scan_manager,
                    self.cwe_scan_settings,
                    self.checkpoint_manager  # 傳遞 checkpoint 管理器
                )
                self.logger.info(f"本次執行的互動設定: {settings}")
                
        except Exception as e:
            self.logger.error(f"顯示互動設定時發生錯誤: {e}")
            # 發生錯誤時也退出腳本
            sys.exit(1)
    
    def _show_cwe_scan_settings_dialog(self):
        """顯示 CWE 掃描設定對話框"""
        try:
            self.logger.info("顯示 CWE 掃描設定介面")
            
            # 載入預設設定
            default_settings = {
                "enabled": False,
                "cwe_type": "022",  # 預設為 CWE-022
                "output_dir": str(Path("./CWE_Result").absolute())
            }
            
            settings = show_cwe_scan_settings(default_settings)
            
            if settings is None:
                # 使用者取消了設定
                self.logger.info("使用者取消了 CWE 掃描設定，結束腳本執行")
                sys.exit(0)
            else:
                # 儲存設定
                self.cwe_scan_settings = settings
                
                # 如果啟用了掃描，初始化掃描管理器
                if settings["enabled"]:
                    # 使用 config 中定義的輸出目錄（忽略 UI 中的設定，確保一致性）
                    self.cwe_scan_manager = CWEScanManager()  # 自動使用 config.CWE_RESULT_DIR
                    self.logger.info(f"✅ CWE 掃描已啟用 (類型: CWE-{settings['cwe_type']})")
                    self.logger.info(f"   輸出目錄: {self.cwe_scan_manager.output_dir}")
                    
                    # 更新 CopilotHandler 的 CWE 掃描設定
                    self.copilot_handler.cwe_scan_manager = self.cwe_scan_manager
                    self.copilot_handler.cwe_scan_settings = self.cwe_scan_settings
                    self.logger.info("✅ CopilotHandler 已更新 CWE 掃描設定")
                else:
                    self.logger.info("ℹ️ CWE 掃描未啟用")
                
        except Exception as e:
            self.logger.error(f"顯示 CWE 掃描設定時發生錯誤: {e}")
            sys.exit(1)
    
    def _check_for_resumable_execution(self) -> Optional[Dict]:
        """
        檢查是否有可恢復的執行記錄
        
        Returns:
            Optional[Dict]: 恢復資訊字典，如果沒有可恢復的記錄則返回 None
        """
        try:
            resume_info = self.checkpoint_manager.get_resume_info()
            
            if resume_info is None:
                return None
            
            # 顯示恢復資訊並詢問使用者
            self.logger.info("=" * 60)
            self.logger.info("發現未完成的執行記錄")
            self.logger.info("=" * 60)
            print(self.checkpoint_manager.format_resume_summary(resume_info))
            
            # 使用 tkinter 顯示對話框
            import tkinter as tk
            from tkinter import messagebox
            
            root = tk.Tk()
            root.withdraw()  # 隱藏主視窗
            
            # 準備顯示資訊
            progress_str = f"{len(resume_info['completed_projects'])}/{resume_info['total_projects']}"
            resume_from_str = f"{resume_info['resume_from']['project_name']}"
            files_str = f"{resume_info.get('total_files_processed', 0)}/{resume_info.get('max_files_limit', 'N/A')}"
            remaining_str = f"{resume_info.get('remaining_files_quota', 'N/A')}"
            mode_str = "AS Mode" if resume_info['execution_mode'] == 'as' else "標準模式"
            max_rounds = resume_info['settings'].get('max_rounds', 10)
            
            # AS Mode 需要顯示 phase 資訊
            phase_str = ""
            if resume_info['execution_mode'] == 'as':
                phase = resume_info['resume_from'].get('phase', 1)
                phase_name = "Query" if phase == 1 else "Coding"
                phase_str = f", Phase: {phase} ({phase_name})"
            
            result = messagebox.askyesnocancel(
                "發現未完成的執行",
                f"發現未完成的執行記錄:\n\n"
                f"【執行設定】\n"
                f"  模式: {mode_str}\n"
                f"  CWE 類型: CWE-{resume_info['settings'].get('cwe_type', 'N/A')}\n"
                f"  最大輪數: {max_rounds}\n"
                f"  檔案限制: {resume_info.get('max_files_limit', 0)}\n\n"
                f"【執行進度】\n"
                f"  專案進度: {progress_str}\n"
                f"  檔案進度: {files_str}\n"
                f"  剩餘配額: {remaining_str}\n\n"
                f"【中斷位置】\n"
                f"  專案: {resume_from_str}\n"
                f"  輪數: {resume_info['resume_from']['round']}, 行數: {resume_info['resume_from']['line']}{phase_str}\n\n"
                f"是否要從中斷點繼續執行?\n"
                f"（將自動套用上次的所有設定）\n\n"
                f"• 是: 繼續執行剩餘 {remaining_str} 個檔案\n"
                f"• 否: 開始新的執行\n"
                f"• 取消: 退出程式",
                icon='question'
            )
            
            root.destroy()
            
            if result is None:
                # 使用者選擇取消
                self.logger.info("使用者選擇取消，退出程式")
                sys.exit(0)
            elif result:
                # 使用者選擇恢復
                self.logger.info("✅ 使用者選擇從中斷點繼續執行（自動套用上次設定）")
                return resume_info
            else:
                # 使用者選擇重新開始
                self.logger.info("使用者選擇開始新的執行，清除舊的檢查點")
                self.checkpoint_manager.clear_checkpoint()
                return None
                
        except Exception as e:
            self.logger.warning(f"檢查恢復記錄時發生錯誤: {e}")
            return None

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
            
            # 跳過初始環境清理，直接開始處理專案
            self.logger.info("✅ 跳過初始環境清理，直接開始處理")
            
            self.logger.info("✅ 前置檢查完成")
            return True
            
        except Exception as e:
            self.logger.error(f"前置檢查失敗: {str(e)}")
            return False
    
    def _process_all_projects(self, projects: List[ProjectInfo]) -> bool:
        """
        處理所有專案
        
        Args:
            projects: 專案列表
            
        Returns:
            bool: 處理是否成功
        """
        try:
            start_time = time.time()
            total_success = 0
            total_failed = 0
            
            # 處理恢復模式：跳過已完成的專案
            start_index = 0
            if self.resume_mode and self.resume_project_index > 0:
                start_index = self.resume_project_index
                self.logger.info(f"🔄 恢復模式: 跳過前 {start_index} 個已完成的專案")
            
            for i, project in enumerate(projects):
                # 跳過已完成的專案（恢復模式）
                if i < start_index:
                    self.logger.debug(f"跳過已完成專案 {i+1}/{len(projects)}: {project.name}")
                    continue
                    
                self.logger.info(f"處理專案 {i+1}/{len(projects)}: {project.name}")
                
                # 更新檢查點：記錄當前專案
                self.checkpoint_manager.update_progress(
                    project_index=i,
                    project_name=project.name
                )
                
                # 檢查是否需要緊急停止
                if self.error_handler.emergency_stop_requested:
                    self.logger.warning("收到緊急停止請求，中止專案處理")
                    self.checkpoint_manager.mark_interrupted()
                    break
                
                # 檢查檔案數量限制（在處理專案前）
                max_lines_for_project = None  # None 表示無限制
                if self.max_files_limit > 0:
                    # 計算此專案的檔案數量（prompt.txt 行數）
                    project_file_count = config.count_project_prompt_lines(project.path)
                    
                    if project_file_count == 0:
                        self.logger.warning(f"專案 {project.name} 沒有 prompt.txt 或檔案為空，跳過")
                        self.skipped_projects += 1
                        continue
                    
                    # 檢查是否會超過限制
                    if self.total_files_processed >= self.max_files_limit:
                        self.logger.warning(
                            f"⚠️  已達到檔案數量限制 ({self.total_files_processed}/{self.max_files_limit})，"
                            f"停止處理剩餘 {len(projects) - i} 個專案"
                        )
                        self.skipped_projects += (len(projects) - i)
                        break
                    
                    # 如果處理此專案會超過限制，則部分處理
                    remaining_quota = self.max_files_limit - self.total_files_processed
                    max_lines_for_project = min(remaining_quota, project_file_count)
                    
                    if project_file_count > remaining_quota:
                        self.logger.info(
                            f"📊 專案 {project.name} 有 {project_file_count} 個檔案，"
                            f"但只剩 {remaining_quota} 個配額，將只處理前 {remaining_quota} 個檔案"
                        )
                    else:
                        self.logger.info(
                            f"📊 專案 {project.name} 有 {project_file_count} 個檔案"
                            f"（已處理: {self.total_files_processed}/{self.max_files_limit}）"
                        )
                
                # 處理單一專案（傳遞檔案數量限制）
                success = self._process_single_project(project, max_lines=max_lines_for_project)
                
                if success:
                    total_success += 1
                    self.successful_projects += 1
                    # 更新檢查點：記錄專案完成、已處理檔案數，並重置 round/line/phase 為初始值
                    # 這樣如果下一個專案中斷，checkpoint 會有正確的初始狀態
                    self.checkpoint_manager.update_progress(
                        completed_project=project.name,
                        total_files_processed=self.total_files_processed,
                        current_round=1,
                        current_line=1,
                        current_phase=1
                    )
                else:
                    total_failed += 1
                    self.failed_projects += 1
                    # 即使失敗也更新已處理檔案數，並重置 round/line/phase
                    self.checkpoint_manager.update_progress(
                        total_files_processed=self.total_files_processed,
                        current_round=1,
                        current_line=1,
                        current_phase=1
                    )
                
                self.processed_projects += 1
                
                # 重置恢復模式的輪數、行數和階段（當前恢復專案處理完成後，下一個專案從頭開始）
                if self.resume_mode and i == self.resume_project_index:
                    self.resume_round = 1
                    self.resume_line = 1
                    self.resume_phase = 1
                    self.logger.info("🔄 恢復專案處理完成，後續專案將從頭開始")
                
                # 項目間短暫休息
                time.sleep(2)
            
            # 處理摘要
            elapsed = time.time() - start_time
            self.logger.info(f"專案處理完成: 成功 {total_success}, 失敗 {total_failed}, 耗時 {elapsed:.1f}秒")
            
            if self.max_files_limit > 0:
                self.logger.info(f"📊 檔案處理統計: {self.total_files_processed}/{self.max_files_limit}")
            
            # 標記檢查點為完成（如果沒有被中斷）
            if not self.error_handler.emergency_stop_requested:
                self.checkpoint_manager.mark_completed()
                self.logger.info("✅ 所有專案處理完成，檢查點已標記為完成")
            
            return True
            
        except Exception as e:
            self.logger.error(f"處理專案時發生錯誤: {str(e)}")
            self.checkpoint_manager.mark_interrupted()
            return False
    
    def _process_single_project(self, project: ProjectInfo, max_lines: int = None) -> bool:
        """
        處理單一專案
        
        Args:
            project: 專案資訊
            max_lines: 最大處理行數限制（None 表示無限制）
            
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
            
            # 直接執行專案自動化（移除重試機制，傳遞行數限制）
            success = self._execute_project_automation(project, project_logger, max_lines=max_lines)
            
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
                error_msg = "處理失敗"
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
    
    def _execute_project_automation(self, project: ProjectInfo, project_logger, max_lines: int = None) -> bool:
        """
        執行專案自動化的核心邏輯
        
        Args:
            project: 專案資訊
            project_logger: 專案日誌記錄器
            max_lines: 最大處理行數限制（None 表示無限制）
            
        Returns:
            bool: 執行是否成功
        """
        try:
            # 檢查中斷請求
            if self.error_handler.emergency_stop_requested:
                raise AutomationError("收到中斷請求", ErrorType.USER_INTERRUPT)
            
            # 判斷是否使用 Artificial Suicide 模式（需要提前判斷以決定是否在這裡開啟專案）
            artificial_suicide_mode = self.interaction_settings.get("artificial_suicide_mode", False) if self.interaction_settings else False
            artificial_suicide_rounds = self.interaction_settings.get("artificial_suicide_rounds", 3) if self.interaction_settings else 3
            
            # AS Mode 由 artificial_suicide_mode.py 自行管理專案開啟和記憶清除
            # 非 AS Mode 則在這裡處理
            if not artificial_suicide_mode:
                # 步驟1: 開啟專案（僅非 AS Mode）
                project_logger.log("開啟 VS Code 專案")
                if not self.vscode_controller.open_project(project.path):
                    raise AutomationError("無法開啟專案", ErrorType.VSCODE_ERROR)
                
                # 檢查中斷請求
                if self.error_handler.emergency_stop_requested:
                    raise AutomationError("收到中斷請求", ErrorType.USER_INTERRUPT)
                
                # 注意：不在專案開始時執行 clear_copilot_memory
                # clear_copilot_memory 會在每輪結束後執行（由 copilot_handler 負責）
            
            # 檢查中斷請求
            if self.error_handler.emergency_stop_requested:
                raise AutomationError("收到中斷請求", ErrorType.USER_INTERRUPT)
            
            # 步驟3: 處理 Copilot Chat（根據設定判斷是否使用反覆互動或 Artificial Suicide 模式）
            # 使用互動設定或預設值
            interaction_enabled = self.interaction_settings.get("interaction_enabled", config.INTERACTION_ENABLED) if self.interaction_settings else config.INTERACTION_ENABLED
            max_rounds = self.interaction_settings.get("max_rounds", config.INTERACTION_MAX_ROUNDS) if self.interaction_settings else config.INTERACTION_MAX_ROUNDS
            
            if artificial_suicide_mode:
                # 使用 Artificial Suicide 攻擊模式
                project_logger.log(f"處理 Copilot Chat (Artificial Suicide 攻擊模式，輪數: {artificial_suicide_rounds})")
                
                # 確定是否為恢復專案（需要傳遞 resume 參數）
                is_resume_project = self.resume_mode and project.name == self.checkpoint_manager._current_checkpoint['progress'].get('current_project_name')
                resume_round = self.resume_round if is_resume_project else 1
                resume_line = self.resume_line if is_resume_project else 1
                resume_phase = self.resume_phase if is_resume_project else 1
                
                success, files_processed = self._execute_artificial_suicide_mode(
                    project, artificial_suicide_rounds, project_logger, max_lines=max_lines,
                    resume_round=resume_round, resume_line=resume_line, resume_phase=resume_phase
                )
                
                # 更新檔案計數器（使用實際處理數量）
                self.total_files_processed += files_processed
                self.logger.info(f"📊 已處理 {files_processed} 個檔案（總計: {self.total_files_processed}）")
                
                if not success:
                    raise AutomationError("Artificial Suicide 模式執行失敗", ErrorType.COPILOT_ERROR)
            elif interaction_enabled:
                # 使用反覆互動功能
                project_logger.log(f"處理 Copilot Chat (啟用反覆互動功能，最大輪數: {max_rounds})")
                
                # 確定是否為恢復專案（需要傳遞 resume 參數）
                is_resume_project = self.resume_mode and project.name == self.checkpoint_manager._current_checkpoint['progress'].get('current_project_name')
                if is_resume_project:
                    self.copilot_handler.set_resume_state(
                        resume_round=self.resume_round,
                        resume_line=self.resume_line
                    )
                else:
                    # 非恢復專案，重置 resume 狀態
                    self.copilot_handler.set_resume_state(resume_round=1, resume_line=1)
                
                success, files_processed = self.copilot_handler.process_project_with_iterations(project.path, max_rounds, max_lines=max_lines)
                
                # 更新檔案計數器（使用實際處理數量）
                self.total_files_processed += files_processed
                self.logger.info(f"📊 已處理 {files_processed} 個檔案（總計: {self.total_files_processed}）")
                
                if not success:
                    raise AutomationError("Copilot 反覆互動處理失敗", ErrorType.COPILOT_ERROR)
            else:
                # 使用一般互動模式
                project_logger.log(f"處理 Copilot Chat (智能等待: {'開啟' if self.use_smart_wait else '關閉'})")
                success, files_processed = self.copilot_handler.process_project_complete(
                    project.path, use_smart_wait=self.use_smart_wait, max_lines=max_lines
                )
                
                # 更新檔案計數器（使用實際處理數量）
                self.total_files_processed += files_processed
                self.logger.info(f"📊 已處理 {files_processed} 個檔案（總計: {self.total_files_processed}）")
                
                if not success:
                    raise AutomationError(
                        "Copilot 處理失敗", 
                        ErrorType.COPILOT_ERROR
                    )
            
            # 檢查中斷請求
            if self.error_handler.emergency_stop_requested:
                raise AutomationError("收到中斷請求", ErrorType.USER_INTERRUPT)
            
            # 步驟3.5: CWE 掃描已在 Copilot 互動期間執行（copilot_handler.py 中的 _perform_cwe_scan_for_prompt）
            # 不需要在此處再次執行掃描，避免重複和誤導
            
            # 步驟4: 驗證結果
            project_logger.log("驗證處理結果")
            execution_result_dir = config.EXECUTION_RESULT_DIR / "Success"
            project_name = Path(project.path).name
            project_result_dir = execution_result_dir / project_name
            
            # 檢查新的輪數資料夾結構（AS 模式：第N輪/第N道/）
            has_success_file = False
            total_files = 0
            round_dirs = []
            
            if project_result_dir.exists():
                # 查找輪數資料夾 (第1輪, 第2輪, etc.)
                round_dirs = [d for d in project_result_dir.iterdir() 
                             if d.is_dir() and d.name.startswith('第') and d.name.endswith('輪')]
                
                # 統計所有輪數資料夾中的檔案（包含道程序子資料夾）
                for round_dir in round_dirs:
                    # 檢查道程序資料夾 (第1道, 第2道, etc.)
                    phase_dirs = [d for d in round_dir.iterdir() 
                                 if d.is_dir() and d.name.startswith('第') and d.name.endswith('道')]
                    
                    if phase_dirs:
                        # AS 模式：檔案在道程序資料夾中
                        for phase_dir in phase_dirs:
                            files_in_phase = list(phase_dir.glob("*.md"))
                            total_files += len(files_in_phase)
                    else:
                        # 一般模式：檔案直接在輪數資料夾中
                        files_in_round = list(round_dir.glob("*.md"))
                        total_files += len(files_in_round)
                
                # 如果有輪數資料夾且包含檔案，則認為成功
                has_success_file = len(round_dirs) > 0 and total_files > 0
            
            # 調試信息
            self.logger.info(f"結果檔案驗證 - 目錄存在: {project_result_dir.exists()}, "
                            f"輪數資料夾: {len(round_dirs)}, 總檔案數: {total_files}, "
                            f"驗證結果: {has_success_file}")
            
            if round_dirs:
                for round_dir in sorted(round_dirs):
                    # 檢查道程序資料夾
                    phase_dirs = [d for d in round_dir.iterdir() 
                                 if d.is_dir() and d.name.startswith('第') and d.name.endswith('道')]
                    if phase_dirs:
                        # AS 模式：顯示每道的檔案數
                        for phase_dir in sorted(phase_dirs):
                            files_count = len(list(phase_dir.glob("*.md")))
                            self.logger.info(f"  {round_dir.name}/{phase_dir.name}: {files_count} 個檔案")
                    else:
                        # 一般模式：顯示輪數的檔案數
                        files_count = len(list(round_dir.glob("*.md")))
                        self.logger.info(f"  {round_dir.name}: {files_count} 個檔案")
            
            # 驗證結果（先驗證，再決定是否關閉）
            if not has_success_file:
                raise AutomationError("缺少成功執行結果檔案", ErrorType.PROJECT_ERROR)
            
            # 步驟5: 關閉專案（只在驗證成功後才關閉）
            project_logger.log("關閉 VS Code 專案")
            if not self.vscode_controller.close_current_project():
                self.logger.warning("專案關閉失敗")
            else:
                self.logger.info("✅ 專案關閉成功")
            
            project_logger.log("專案處理完成")
            return True
            
        except AutomationError:
            # 確保在異常情況下也關閉 VS Code
            try:
                project_logger.log("異常情況下關閉 VS Code 專案")
                self.vscode_controller.close_current_project()
            except:
                pass
            raise
        except Exception as e:
            # 確保在異常情況下也關閉 VS Code
            try:
                project_logger.log("異常情況下關閉 VS Code 專案")
                self.vscode_controller.close_current_project()
            except:
                pass
            raise AutomationError(str(e), ErrorType.UNKNOWN_ERROR)
    
    def _execute_artificial_suicide_mode(
        self, 
        project: ProjectInfo, 
        num_rounds: int,
        project_logger,
        max_lines: int = None,
        resume_round: int = 1,
        resume_line: int = 1,
        resume_phase: int = 1
    ) -> Tuple[bool, int]:
        """
        執行 Artificial Suicide 攻擊模式
        
        Args:
            project: 專案資訊
            num_rounds: 攻擊輪數
            project_logger: 專案日誌記錄器
            max_lines: 最大處理行數限制（None 表示無限制）
            resume_round: 恢復起始輪數（1-based，預設為 1）
            resume_line: 恢復起始行數（1-based，預設為 1）
            resume_phase: 恢復起始階段（1=Query, 2=Coding，預設為 1）
            
        Returns:
            Tuple[bool, int]: (執行是否成功, 實際處理的檔案數)
        """
        try:
            # 導入 ArtificialSuicideMode（輕量級控制器）
            try:
                from src.artificial_suicide_mode import ArtificialSuicideMode
            except ImportError:
                from artificial_suicide_mode import ArtificialSuicideMode
            
            # 提取專案名稱和 CWE 類型
            project_name = Path(project.path).name
            
            # 從專案名稱中提取 CWE 類型（假設格式為 xxx__CWE-XXX__xxx）
            target_cwe = "327"  # 預設值（只取數字）
            if "__CWE-" in project_name:
                parts = project_name.split("__")
                for part in parts:
                    if part.startswith("CWE-"):
                        target_cwe = part.replace("CWE-", "")
                        break
            
            self.logger.info(f"初始化 Artificial Suicide Mode: 專案={project_name}, CWE-{target_cwe}, 輪數={num_rounds}")
            if resume_round > 1 or resume_line > 1 or resume_phase > 1:
                self.logger.info(f"🔄 恢復模式: 從第 {resume_round} 輪 Phase {resume_phase} 第 {resume_line} 行繼續")
            
            # 初始化 ArtificialSuicideMode（直接利用現有模組，並傳遞檔案限制和 resume 參數）
            as_mode = ArtificialSuicideMode(
                copilot_handler=self.copilot_handler,
                vscode_controller=self.vscode_controller,
                cwe_scan_manager=self.cwe_scan_manager,
                error_handler=self.error_handler,
                project_path=str(project.path),
                target_cwe=target_cwe,
                total_rounds=num_rounds,
                max_files_limit=self.max_files_limit,
                files_processed_so_far=self.total_files_processed,
                checkpoint_manager=self.checkpoint_manager,
                resume_round=resume_round,
                resume_line=resume_line,
                resume_phase=resume_phase
            )
            
            # 執行攻擊流程
            self.logger.info("開始執行 Artificial Suicide 攻擊流程...")
            success, files_processed = as_mode.execute()
            
            if success:
                project_logger.log(f"✅ Artificial Suicide 攻擊模式執行成功（處理了 {files_processed} 個檔案）")
                self.logger.info(f"Artificial Suicide 攻擊模式執行成功（處理了 {files_processed} 個檔案）")
            else:
                project_logger.log(f"❌ Artificial Suicide 攻擊模式執行失敗（已處理 {files_processed} 個檔案）")
                self.logger.error(f"Artificial Suicide 攻擊模式執行失敗（已處理 {files_processed} 個檔案）")
            
            return success, files_processed
            
        except Exception as e:
            error_msg = f"Artificial Suicide 模式執行時發生錯誤: {e}"
            self.logger.error(error_msg)
            project_logger.log(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return False, 0
    
    def _execute_cwe_scan(self, project: ProjectInfo, project_logger) -> bool:
        """
        執行 CWE 函式級別掃描（逐行模式）
        
        ⚠️ DEPRECATED: 此方法已不再被使用。
        CWE 掃描現在在 Copilot 互動期間執行（copilot_handler.py 中的 _perform_cwe_scan_for_prompt）。
        保留此方法僅作為參考，未來版本可能會移除。
        
        Args:
            project: 專案資訊
            project_logger: 專案日誌記錄器
            
        Returns:
            bool: 掃描是否成功
        """
        import warnings
        warnings.warn(
            "_execute_cwe_scan() is deprecated. CWE scanning is now performed during Copilot interaction.",
            DeprecationWarning,
            stacklevel=2
        )
        
        try:
            if not self.cwe_scan_manager:
                self.logger.warning("CWE 掃描管理器未初始化")
                return False
            
            project_name = Path(project.path).name
            cwe_type = self.cwe_scan_settings["cwe_type"]
            
            self.logger.info(f"開始執行 CWE-{cwe_type} 函式級別掃描（逐行模式）...")
            
            # 讀取專案的 prompt 檔案
            prompt_source_mode = self.interaction_settings.get(
                "prompt_source_mode", 
                config.PROMPT_SOURCE_MODE
            ) if self.interaction_settings else config.PROMPT_SOURCE_MODE
            
            # 根據 prompt 來源模式讀取 prompt
            if prompt_source_mode == "project":
                # 專案專用提示詞模式：讀取專案目錄下的 prompt.txt
                prompt_file = Path(project.path) / config.PROJECT_PROMPT_FILENAME
                if not prompt_file.exists():
                    self.logger.warning(f"專案提示詞檔案不存在: {prompt_file}")
                    return False
            else:
                # 全域提示詞模式：讀取 prompts/prompt1.txt
                prompt_file = config.PROMPT1_FILE_PATH
                if not prompt_file.exists():
                    self.logger.warning(f"全域提示詞檔案不存在: {prompt_file}")
                    return False
            
            # 逐行讀取 prompt 內容
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_lines = [line.strip() for line in f.readlines() if line.strip()]
            
            if not prompt_lines:
                self.logger.warning(f"提示詞檔案為空: {prompt_file}")
                return False
            
            total_lines = len(prompt_lines)
            self.logger.info(f"提示詞檔案共 {total_lines} 行，將逐行掃描...")
            
            # 逐行執行函式級別掃描
            successful_scans = 0
            failed_scans = 0
            
            for line_number, prompt_line in enumerate(prompt_lines, 1):
                try:
                    self.logger.info(f"掃描第 {line_number}/{total_lines} 行...")
                    
                    # 執行函式級別掃描（返回值增加了 vuln_info）
                    success, result_file, vuln_info = self.cwe_scan_manager.scan_from_prompt_function_level(
                        project_path=Path(project.path),
                        project_name=project_name,
                        prompt_content=prompt_line,
                        cwe_type=cwe_type,
                        round_number=1,
                        line_number=line_number
                    )
                    
                    if success:
                        self.logger.info(f"✅ 第 {line_number} 行掃描完成")
                        successful_scans += 1
                    else:
                        self.logger.warning(f"⚠️  第 {line_number} 行掃描失敗")
                        failed_scans += 1
                        
                except Exception as e:
                    self.logger.error(f"第 {line_number} 行掃描時發生錯誤: {e}")
                    failed_scans += 1
            
            # 輸出掃描摘要
            self.logger.create_separator(f"CWE-{cwe_type} 掃描摘要")
            self.logger.info(f"總計: {total_lines} 行")
            self.logger.info(f"成功: {successful_scans} 行")
            self.logger.info(f"失敗: {failed_scans} 行")
            
            if successful_scans > 0:
                project_logger.log(f"CWE-{cwe_type} 函式級別掃描完成 ({successful_scans}/{total_lines} 行)")
                return True
            else:
                self.logger.warning("所有行掃描都失敗")
                return False
                
        except Exception as e:
            self.logger.error(f"執行 CWE 掃描時發生錯誤: {e}")
            return False

    

    
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
            
            # 保存專案摘要報告（傳遞函數處理統計）
            report_file = self.project_manager.save_summary_report(
                total_files_processed=self.total_files_processed,
                max_files_limit=self.max_files_limit
            )
            if report_file:
                self.logger.info(f"詳細報告已儲存: {report_file}")
            
        except Exception as e:
            self.logger.error(f"生成最終報告時發生錯誤: {str(e)}")
    
    def _cleanup(self):
        """清理環境"""
        try:
            self.logger.info("清理執行環境...")
            
            # 程式結束時不主動關閉 VS Code
            # self.vscode_controller.ensure_clean_environment()
            
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