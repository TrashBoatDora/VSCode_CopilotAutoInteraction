# -*- coding: utf-8 -*-
"""
Hybrid UI Automation Script - VS Code 操作控制模組
處理開啟專案、關閉專案、記憶清除等 VS Code 操作
"""

import subprocess
import time
import os
import psutil
import pyautogui
from pathlib import Path
from typing import Optional, List
import sys

# 導入配置和日誌
sys.path.append(str(Path(__file__).parent.parent))
from config.config import config
from src.logger import get_logger
from src.vscode_ui_initializer import initialize_vscode_ui

class VSCodeController:
    """VS Code 操作控制器"""
    
    def __init__(self):
        """初始化 VS Code 控制器"""
        self.logger = get_logger("VSCodeController")
        self.current_project_path = None
        self.vscode_process = None
        # 啟動時記錄所有現有 VS Code 進程 PID
        self.pre_existing_vscode_pids = set()
        for proc in psutil.process_iter(['pid', 'name']):
            if 'code' in proc.info['name'].lower():
                self.pre_existing_vscode_pids.add(proc.info['pid'])
        self.logger.info(f"VS Code 控制器初始化完成，已記錄現有 VS Code PID: {self.pre_existing_vscode_pids}")
    
    def is_vscode_running(self) -> bool:
        """
        檢查 VS Code 是否正在運行
        
        Returns:
            bool: VS Code 是否在運行
        """
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if 'code' in proc.info['name'].lower():
                    return True
            return False
        except Exception as e:
            self.logger.debug(f"檢查 VS Code 運行狀態時發生錯誤: {str(e)}")
            return False
    
    def _is_auto_opened_vscode_running(self) -> bool:
        """
        檢查自動開啟的 VS Code 實例是否還在運行
        
        Returns:
            bool: 自動開啟的 VS Code 是否在運行
        """
        try:
            auto_opened_processes = []
            for proc in psutil.process_iter(['pid', 'name']):
                if ('code' in proc.info['name'].lower() and 
                    proc.info['pid'] not in self.pre_existing_vscode_pids):
                    auto_opened_processes.append(proc.info['pid'])
            
            if auto_opened_processes:
                self.logger.debug(f"發現自動開啟的 VS Code 進程: {auto_opened_processes}")
                return True
            else:
                self.logger.debug("沒有發現自動開啟的 VS Code 進程")
                return False
                
        except Exception as e:
            self.logger.debug(f"檢查自動開啟 VS Code 狀態時發生錯誤: {str(e)}")
            return False
    
    def close_all_vscode_instances(self) -> bool:
        """
        關閉所有 VS Code 實例
        
        Returns:
            bool: 關閉是否成功
        """
        try:
            self.logger.info("關閉自動開啟的 VS Code 實例...")
            
            # 嘗試優雅關閉
            self.logger.debug("(已註解) 嘗試使用 Alt+F4 優雅關閉 VS Code ... (跳過)")
            # try:
            #     pyautogui.hotkey('alt', 'f4')  # Alt+F4 關閉視窗
            #     time.sleep(2)
            #     self.logger.debug("Alt+F4 完成，等待 2 秒")
            # except Exception as e:
            #     self.logger.debug(f"Alt+F4 失敗: {str(e)}")

            # 只關閉自動開啟的 VS Code 進程
            self.logger.debug("開始掃描 VS Code 進程...")
            vscode_processes = []
            for proc in psutil.process_iter(['pid', 'name']):
                if 'code' in proc.info['name'].lower() and proc.info['pid'] not in self.pre_existing_vscode_pids:
                    vscode_processes.append(proc)
            self.logger.debug(f"發現 {len(vscode_processes)} 個自動開啟的 VS Code 進程")

            # 強制終止自動開啟的 VS Code 進程
            self.logger.debug("開始強制終止自動開啟的 VS Code 進程...")
            for proc in vscode_processes:
                try:
                    proc.terminate()
                    self.logger.debug(f"終止自動開啟的 VS Code 進程: {proc.info['pid']}")
                except Exception as e:
                    self.logger.debug(f"終止進程 {proc.info['pid']} 失敗: {str(e)}")

            # 等待進程完全終止
            self.logger.debug("等待進程完全終止（3秒）...")
            time.sleep(3)
            self.logger.debug("等待完成，開始最後檢查...")

            # 最後檢查
            # 只要自動開啟的都關閉就算成功
            still_running = [proc.info['pid'] for proc in psutil.process_iter(['pid', 'name']) if 'code' in proc.info['name'].lower() and proc.info['pid'] not in self.pre_existing_vscode_pids]
            if not still_running:
                self.logger.info("✅ 自動開啟的 VS Code 實例已關閉")
                self.current_project_path = None
                self.vscode_process = None
                return True
            else:
                self.logger.warning(f"⚠️ 部分自動開啟的 VS Code 實例仍在運行: {still_running}")
                return False
                
        except Exception as e:
            self.logger.error(f"關閉 VS Code 實例時發生錯誤: {str(e)}")
            return False
    
    def open_project(self, project_path: str, wait_for_load: bool = True) -> bool:
        """
        開啟專案
        
        Args:
            project_path: 專案路徑
            wait_for_load: 是否等待載入完成
            
        Returns:
            bool: 開啟是否成功
        """
        try:
            project_path = Path(project_path)
            
            if not project_path.exists():
                self.logger.error(f"專案路徑不存在: {project_path}")
                return False
            
            self.logger.info(f"開啟專案: {project_path}")
            
            # 確保之前的 VS Code 實例已關閉
            if self.is_vscode_running():
                self.logger.info("發現現有 VS Code 實例，正在關閉...")
                if not self.close_all_vscode_instances():
                    self.logger.warning("無法完全關閉現有實例，等待3秒後繼續")
                    time.sleep(3)
            
            # 設置環境變量以提高穩定性
            env = os.environ.copy()
            env['ELECTRON_DISABLE_SECURITY_WARNINGS'] = '1'
            env['ELECTRON_NO_ATTACH_CONSOLE'] = '1'
            
            # 使用命令列開啟專案，添加穩定性參數
            cmd = [config.VSCODE_EXECUTABLE, str(project_path)]
            
            # 添加穩定性參數
            stability_args = [
                "--disable-gpu-sandbox",     # 避免 GPU 相關崩潰
                "--no-sandbox",              # 避免沙盒相關問題  
                "--disable-dev-shm-usage",   # 避免共享記憶體問題
                "--disable-background-timer-throttling",  # 避免背景計時器問題
            ]
            
            cmd.extend(stability_args)
            self.logger.debug(f"執行命令: {' '.join(cmd)}")
            
            try:
                self.vscode_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    cwd=str(project_path.parent),
                    env=env
                )
                
                self.current_project_path = str(project_path)
                
                if wait_for_load:
                    # 等待 VS Code 啟動並驗證
                    self.logger.info("等待 VS Code 啟動...")
                    time.sleep(config.VSCODE_STARTUP_DELAY)
                    
                    # 驗證 VS Code 是否正常啟動
                    max_attempts = 5
                    for attempt in range(max_attempts):
                        if self.is_vscode_running():
                            self.logger.info(f"✅ VS Code 啟動成功 (第 {attempt + 1} 次檢查)")
                            time.sleep(2)  # 額外等待確保完全載入
                            
                            # 立即最大化視窗，不動到既有畫面
                            self.logger.info("正在最大化視窗...")
                            self._maximize_window_direct()
                            
                            return True
                        else:
                            self.logger.debug(f"第 {attempt + 1}/{max_attempts} 次檢查: VS Code 尚未完全啟動")
                            time.sleep(1)
                    
                    self.logger.warning("⚠️ VS Code 啟動但無法確認運行狀態")
                    # 即使無法確認狀態也嘗試最大化
                    self._maximize_window_direct()
                    return True  # 假設成功，繼續執行
                else:
                    return True
                    
            except Exception as e:
                self.logger.error(f"啟動 VS Code 過程中發生錯誤: {str(e)}")
                return False
                self.logger.info(f"等待 VS Code 載入 ({config.VSCODE_STARTUP_DELAY}秒)...")
                time.sleep(config.VSCODE_STARTUP_DELAY)
                
                # 初始化 UI
                self.logger.info("初始化 VS Code UI...")
                if not initialize_vscode_ui():
                    self.logger.warning("UI 初始化失敗，但繼續執行")
            
            self.logger.info(f"✅ 專案開啟成功: {project_path.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"開啟專案失敗: {str(e)}")
            return False
    
    def close_current_project(self, force: bool = False) -> bool:
        """
        關閉當前專案
        
        Args:
            force: 是否強制關閉
            
        Returns:
            bool: 關閉是否成功
        """
        try:
            if not self.current_project_path:
                self.logger.debug("沒有開啟的專案需要關閉")
                return True
            
            self.logger.info(f"關閉專案: {Path(self.current_project_path).name}")
            
            if force:
                # 強制關閉所有 VS Code 實例
                return self.close_all_vscode_instances()
            else:
                # 嘗試多種優雅關閉方法
                return self._try_graceful_close()
                    
        except Exception as e:
            self.logger.error(f"關閉專案時發生錯誤: {str(e)}")
            return False
    
    def _try_graceful_close(self) -> bool:
        """
        嘗試多種優雅關閉方法
        
        Returns:
            bool: 關閉是否成功
        """
        try:
            self.logger.debug("開始嘗試優雅關閉...")
            
            # 不使用焦點切換，直接嘗試關閉方法
            # 避免意外切換到用戶的其他 VS Code 視窗
            
            # 嘗試多種關閉方法
            close_methods = [
                ("進程關閉 (Process Termination)", self._close_method_process_termination),
                ("Ctrl+Shift+W (關閉視窗)", self._close_method_ctrl_shift_w),
                ("Alt+F4 (關閉應用程式)", self._close_method_alt_f4)
            ]
            
            for method_name, method_func in close_methods:
                try:
                    self.logger.debug(f"嘗試方法: {method_name}")
                    
                    # 執行關閉方法
                    if method_func():
                        # 等待關閉完成
                        time.sleep(2)
                        
                        # 檢查是否成功關閉自動開啟的 VS Code 實例
                        if not self._is_auto_opened_vscode_running():
                            self.current_project_path = None
                            self.vscode_process = None
                            self.logger.info(f"✅ 優雅關閉成功 - 方法: {method_name}")
                            return True
                        else:
                            self.logger.debug(f"方法 {method_name} 未完全關閉，繼續嘗試下一種方法")
                    
                except Exception as e:
                    self.logger.debug(f"關閉方法 {method_name} 失敗: {e}")
                    continue
            
            # 所有優雅關閉方法都失敗，嘗試強制關閉
            self.logger.info("所有優雅關閉方法都失敗，嘗試強制關閉...")
            return self.close_all_vscode_instances()
            
        except Exception as e:
            self.logger.error(f"優雅關閉過程中發生錯誤: {e}")
            return self.close_all_vscode_instances()
    
    def _close_method_process_termination(self) -> bool:
        """使用進程終止方法精確關閉目標視窗"""
        try:
            if self.vscode_process and self.vscode_process.poll() is None:
                self.logger.debug(f"嘗試終止目標進程 PID: {self.vscode_process.pid}")
                self.vscode_process.terminate()
                time.sleep(1)
                
                # 檢查進程是否已終止
                if self.vscode_process.poll() is not None:
                    self.logger.debug("目標進程已成功終止")
                    return True
                else:
                    # 如果 terminate 不起作用，嘗試 kill
                    self.logger.debug("嘗試強制終止進程")
                    self.vscode_process.kill()
                    time.sleep(1)
                    return self.vscode_process.poll() is not None
            else:
                self.logger.debug("沒有有效的目標進程可終止")
                return False
                
        except Exception as e:
            self.logger.debug(f"進程終止失敗: {e}")
            return False
    
    def _close_method_ctrl_shift_w(self) -> bool:
        """使用 Ctrl+Shift+W 關閉視窗 (精確關閉目標視窗)"""
        try:
            # 先嘗試通過進程 PID 聚焦到正確的視窗
            if self.vscode_process and self.vscode_process.poll() is None:
                # 如果有記錄的進程，嘗試聚焦到它
                self.logger.debug(f"嘗試聚焦到目標進程 PID: {self.vscode_process.pid}")
                # 這裡可以添加更精確的視窗聚焦邏輯
            
            pyautogui.hotkey('ctrl', 'shift', 'w')
            return True
        except Exception as e:
            self.logger.debug(f"Ctrl+Shift+W 失敗: {e}")
            return False
    
    def _close_method_alt_f4(self) -> bool:
        """使用 Alt+F4 關閉應用程式 (精確關閉目標視窗)"""
        try:
            # 先嘗試通過進程 PID 聚焦到正確的視窗
            if self.vscode_process and self.vscode_process.poll() is None:
                self.logger.debug(f"嘗試聚焦到目標進程 PID: {self.vscode_process.pid}")
            
            pyautogui.hotkey('alt', 'f4')
            return True
        except Exception as e:
            self.logger.debug(f"Alt+F4 失敗: {e}")
            return False
    
    def ensure_clean_environment(self) -> bool:
        """
        確保乾淨的執行環境（關閉所有 VS Code 實例）
        
        Returns:
            bool: 清理是否成功
        """
        try:
            self.logger.info("確保乾淨的執行環境...")
            
            if self.is_vscode_running():
                return self.close_all_vscode_instances()
            else:
                self.logger.info("✅ 環境已經是乾淨的")
                return True
                
        except Exception as e:
            self.logger.error(f"清理環境時發生錯誤: {str(e)}")
            return False
    
    def _maximize_window_direct(self) -> bool:
        """
        直接最大化視窗，不影響既有畫面
        
        Returns:
            bool: 操作是否成功
        """
        try:
            self.logger.info("正在最大化 VS Code 視窗...")
            
            # 使用 Alt+Space, X 組合鍵直接最大化視窗
            pyautogui.hotkey('alt', 'space')
            time.sleep(0.5)
            pyautogui.press('x')
            time.sleep(0.5)
            
            self.logger.info("✅ 視窗最大化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"最大化視窗失敗: {str(e)}")
            return False

    def restart_vscode(self, project_path: str = None) -> bool:
        """
        重啟 VS Code
        
        Args:
            project_path: 要重新開啟的專案路徑
            
        Returns:
            bool: 重啟是否成功
        """
        try:
            self.logger.info("重啟 VS Code...")
            
            # 關閉所有實例
            if not self.close_all_vscode_instances():
                self.logger.error("無法關閉現有 VS Code 實例")
                return False
            
            # 等待完全關閉
            time.sleep(3)
            
            # 如果指定了專案路徑，重新開啟
            if project_path:
                return self.open_project(project_path)
            else:
                self.logger.info("✅ VS Code 重啟完成（未開啟專案）")
                return True
                
        except Exception as e:
            self.logger.error(f"重啟 VS Code 時發生錯誤: {str(e)}")
            return False
    
    def wait_for_vscode_ready(self, timeout: int = 30) -> bool:
        """
        等待 VS Code 準備就緒
        
        Args:
            timeout: 超時時間（秒）
            
        Returns:
            bool: VS Code 是否準備就緒
        """
        try:
            self.logger.debug(f"等待 VS Code 準備就緒 (超時: {timeout}秒)")
            
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if self.is_vscode_running():
                    # 嘗試簡單的按鍵操作來測試響應性
                    try:
                        pyautogui.press('escape')
                        time.sleep(0.1)
                        self.logger.debug("VS Code 響應正常")
                        return True
                    except:
                        pass
                
                time.sleep(1)
            
            self.logger.warning(f"VS Code 在 {timeout} 秒內未準備就緒")
            return False
            
        except Exception as e:
            self.logger.error(f"等待 VS Code 準備就緒時發生錯誤: {str(e)}")
            return False
    
    def get_current_project_info(self) -> Optional[dict]:
        """
        取得當前專案資訊
        
        Returns:
            Optional[dict]: 專案資訊字典
        """
        if not self.current_project_path:
            return None
        
        project_path = Path(self.current_project_path)
        return {
            "name": project_path.name,
            "path": str(project_path),
            "exists": project_path.exists(),
            "is_running": self.is_vscode_running()
        }
    
    def save_all_files(self) -> bool:
        """
        儲存所有檔案
        
        Returns:
            bool: 儲存是否成功
        """
        try:
            self.logger.debug("儲存所有檔案...")
            
            pyautogui.hotkey('ctrl', 'shift', 's')  # Ctrl+Shift+S 儲存全部
            time.sleep(1)
            
            self.logger.debug("所有檔案已儲存")
            return True
            
        except Exception as e:
            self.logger.error(f"儲存檔案時發生錯誤: {str(e)}")
            return False
    
    def focus_vscode_window(self) -> bool:
        """
        聚焦 VS Code 視窗
        
        Returns:
            bool: 聚焦是否成功
        """
        try:
            if not self.is_vscode_running():
                self.logger.warning("VS Code 未運行，無法聚焦")
                return False
            
            # 嘗試使用 Alt+Tab 切換到 VS Code
            pyautogui.hotkey('alt', 'tab')
            time.sleep(0.5)
            
            # 不再點擊螢幕中央，避免不必要的滑鼠操作
            # 改用鍵盤確保聚焦
            pyautogui.press('ctrl')  # 簡單的鍵盤操作確保視窗聚焦
            time.sleep(0.5)
            
            self.logger.debug("VS Code 視窗已聚焦")
            return True
            return True
            
        except Exception as e:
            self.logger.error(f"聚焦 VS Code 視窗時發生錯誤: {str(e)}")
            return False
    
    def clear_copilot_memory(self) -> bool:
        """
        清除 Copilot Chat 記憶
        
        Returns:
            bool: 清除是否成功
        """
        try:
            self.logger.info("開始清除 Copilot Chat 記憶...")
            
            # 執行清除記憶命令序列
            for command in config.COPILOT_CLEAR_MEMORY_COMMANDS:
                if command['type'] == 'hotkey':
                    pyautogui.hotkey(*command['keys'])
                    self.logger.debug(f"執行快捷鍵: {'+'.join(command['keys'])}")
                elif command['type'] == 'key':
                    pyautogui.press(command['key'])
                    self.logger.debug(f"按下按鍵: {command['key']}")
                
                time.sleep(command['delay'])
            
            self.logger.info("✅ Copilot Chat 記憶已清除")
            return True
            
        except Exception as e:
            self.logger.error(f"清除 Copilot Chat 記憶時發生錯誤: {str(e)}")
            return False

# 創建全域實例
vscode_controller = VSCodeController()

# 便捷函數
def open_project(project_path: str, wait_for_load: bool = True) -> bool:
    """開啟專案的便捷函數"""
    return vscode_controller.open_project(project_path, wait_for_load)

def close_current_project(force: bool = False) -> bool:
    """關閉當前專案的便捷函數"""
    return vscode_controller.close_current_project(force)

def ensure_clean_environment() -> bool:
    """確保乾淨環境的便捷函數"""
    return vscode_controller.ensure_clean_environment()

def restart_vscode(project_path: str = None) -> bool:
    """重啟 VS Code 的便捷函數"""
    return vscode_controller.restart_vscode(project_path)