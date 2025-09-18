# -*- coding: utf-8 -*-
"""
Hybrid UI Automation Script - Copilot Chat 操作模組
處理開啟 Chat、發送提示、等待回應、複製結果等操作
完全使用鍵盤操作，無需圖像識別
"""

import pyautogui
import pyperclip
import psutil
import time
from pathlib import Path
from typing import Optional, Tuple
import sys

# 導入配置和日誌
sys.path.append(str(Path(__file__).parent.parent))
from config.config import config
from src.logger import get_logger
from src.image_recognition import image_recognition

class CopilotHandler:
    """Copilot Chat 操作處理器"""
    
    def __init__(self, error_handler=None, interaction_settings=None):
        """初始化 Copilot 處理器"""
        self.logger = get_logger("CopilotHandler")
        self.is_chat_open = False
        self.last_response = ""
        self.error_handler = error_handler  # 添加 error_handler 引用
        self.image_recognition = image_recognition  # 添加圖像識別引用
        self.interaction_settings = interaction_settings  # 添加外部設定支援
        self.logger.info("Copilot Chat 處理器初始化完成")
    
    def open_copilot_chat(self) -> bool:
        """
        開啟 Copilot Chat (使用 Ctrl+Shift+I)
        
        Returns:
            bool: 開啟是否成功
        """
        try:
            self.logger.info("開啟 Copilot Chat...")
            
            # 使用 Ctrl+Shift+I 聚焦到 Copilot Chat 輸入框
            pyautogui.hotkey('ctrl', 'shift', 'i')
            time.sleep(config.VSCODE_COMMAND_DELAY)
            
            # 等待面板開啟和聚焦
            time.sleep(2)
            
            self.is_chat_open = True
            self.logger.copilot_interaction("開啟 Chat 面板", "SUCCESS")
            return True
            
        except Exception as e:
            self.logger.copilot_interaction("開啟 Chat 面板", "ERROR", str(e))
            return False
    
    def send_prompt(self, prompt: str = None) -> bool:
        """
        發送提示詞到 Copilot Chat (使用鍵盤操作)
        
        Args:
            prompt: 自定義提示詞，若為 None 則從 prompt.txt 讀取
            
        Returns:
            bool: 發送是否成功
        """
        try:
            # 讀取提示詞
            if prompt is None:
                prompt = self._load_prompt_from_file()
                if not prompt:
                    self.logger.error("無法讀取提示詞檔案")
                    return False
            
            self.logger.info("發送提示詞到 Copilot Chat...")
            self.logger.debug(f"提示詞內容: {prompt[:100]}...")
            
            # 將提示詞複製到剪貼簿
            pyperclip.copy(prompt)
            time.sleep(0.5)
            
            # 使用 Ctrl+Shift+I 聚焦到輸入框
            pyautogui.hotkey('ctrl', 'shift', 'i')
            time.sleep(1)
            
            # 清空現有內容並貼上提示詞
            pyautogui.hotkey('ctrl', 'a')  # 全選
            time.sleep(0.2)
            pyautogui.hotkey('ctrl', 'v')  # 貼上
            time.sleep(1)
            
            # 發送提示詞
            pyautogui.press('enter')
            time.sleep(1)
            
            self.is_chat_open = True
            self.logger.copilot_interaction("發送提示詞", "SUCCESS", f"長度: {len(prompt)} 字元")
            return True
            
        except Exception as e:
            self.logger.copilot_interaction("發送提示詞", "ERROR", str(e))
            return False
    
    def _load_prompt_from_file(self) -> Optional[str]:
        """
        從 prompt.txt 檔案讀取提示詞
        
        Returns:
            Optional[str]: 提示詞內容，讀取失敗則返回 None
        """
        try:
            prompt_file = Path(config.PROMPT_FILE_PATH)
            if not prompt_file.exists():
                self.logger.error(f"提示詞檔案不存在: {prompt_file}")
                return None
            
            with open(prompt_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content:
                self.logger.error("提示詞檔案為空")
                return None
            
            self.logger.debug(f"成功讀取提示詞檔案: {len(content)} 字元")
            return content
            
        except Exception as e:
            self.logger.error(f"讀取提示詞檔案失敗: {str(e)}")
            return None
    
    def wait_for_response(self, timeout: int = None, use_smart_wait: bool = None) -> bool:
        """
        等待 Copilot 回應完成
        
        Args:
            timeout: 超時時間（秒），若為 None 則使用配置值
            use_smart_wait: 是否使用智能等待，若為 None 則使用配置值
            
        Returns:
            bool: 是否成功等到回應
        """
        try:
            if timeout is None:
                timeout = config.COPILOT_RESPONSE_TIMEOUT
                
            if use_smart_wait is None:
                use_smart_wait = config.SMART_WAIT_ENABLED
            
            self.logger.info(f"等待 Copilot 回應 (超時: {timeout}秒, 智能等待: {'開啟' if use_smart_wait else '關閉'})...")
            
            if use_smart_wait:
                return self._smart_wait_for_response(timeout)
            else:
                # 使用固定等待時間，避免圖像識別複雜度
                wait_time = min(timeout, 60)  # 最多等待60秒
                
                # 分段睡眠，每秒檢查一次中斷請求
                for i in range(wait_time):
                    # 檢查是否有緊急停止請求
                    if self.error_handler and self.error_handler.emergency_stop_requested:
                        self.logger.warning("收到中斷請求，停止等待 Copilot 回應")
                        return False
                    time.sleep(1)
                
                self.logger.copilot_interaction("回應等待完成", "SUCCESS", f"等待時間: {wait_time}秒")
                return True
            
        except Exception as e:
            self.logger.copilot_interaction("等待回應", "ERROR", str(e))
            return False
    
    def _smart_wait_for_response(self, timeout: int) -> bool:
        """
        簡化的智能等待 Copilot 回應完成 (只使用圖像辨識和穩定性檢查)
        
        Args:
            timeout: 超時時間（秒）
            
        Returns:
            bool: 是否成功等到回應
        """
        try:
            self.logger.info(f"智能等待 Copilot 回應，最長等待 {timeout} 秒...")
            
            start_time = time.time()
            check_interval = 1.5  # 檢查間隔
            
            # 簡化的穩定性追蹤
            last_response = ""
            stable_count = 0
            required_stable_count = 3  # 減少穩定檢查次數
            min_response_length = 100  # 降低最小回應長度要求
            
            # 狀態追蹤
            first_content_detected = False
            last_change_time = start_time
            
            # 初始等待時間
            initial_wait = 2
            self.logger.info(f"初始等待 {initial_wait} 秒...")
            time.sleep(initial_wait)
            
            # 持續監控直到回應穩定
            while (time.time() - start_time) < timeout:
                # 檢查是否有緊急停止請求
                if self.error_handler and self.error_handler.emergency_stop_requested:
                    self.logger.warning("收到中斷請求，停止等待 Copilot 回應")
                    return False
                
                # 使用新的自動清除通知的狀態檢查
                try:
                    copilot_status = self.image_recognition.check_copilot_response_status_with_auto_clear()
                    
                    # 如果清除了通知，記錄相關信息
                    if copilot_status.get('notifications_cleared', False):
                        self.logger.info("🔄 已清除 VS Code 通知，繼續檢測...")
                    
                    # 圖像檢測優先判斷
                    if copilot_status['has_send_button'] and not copilot_status['has_stop_button']:
                        # 檢測到 send 按鈕且沒有 stop 按鈕，認為回應完成
                        self.logger.info("✅ 圖像檢測確認：Copilot 回應已完成（檢測到 send 按鈕）")
                        
                        # 嘗試獲取回應內容
                        current_response = self._try_copy_response_without_logging()
                        if current_response and len(current_response.strip()) >= min_response_length:
                            self.last_response = current_response
                            elapsed_time = time.time() - start_time
                            self.logger.info(f"🎉 完成等待！(圖像檢測, {elapsed_time:.1f}秒, {len(current_response)}字元)")
                            return True
                        else:
                            self.logger.debug("圖像檢測顯示完成，但內容長度不足，繼續等待...")
                    
                    elif copilot_status['has_stop_button']:
                        self.logger.debug("🔄 檢測到 stop 按鈕，Copilot 正在回應中...")
                    
                    # 記錄詳細狀態
                    self.logger.debug(f"狀態: {copilot_status['status_message']}")
                    
                except Exception as e:
                    self.logger.debug(f"圖像檢測錯誤: {e}")
                
                # 獲取並檢查回應內容穩定性
                current_response = self._try_copy_response_without_logging()
                elapsed_time = time.time() - start_time
                
                if current_response and len(current_response.strip()) > 0:
                    if not first_content_detected:
                        self.logger.info("✅ 檢測到 Copilot 開始回應")
                        first_content_detected = True
                    
                    # 檢查內容穩定性
                    if current_response == last_response:
                        stable_count += 1
                        time_since_change = time.time() - last_change_time
                        
                        self.logger.debug(f"回應穩定: {stable_count}/{required_stable_count} 次, "
                                        f"穩定時間: {time_since_change:.1f}秒, "
                                        f"長度: {len(current_response)} 字元")
                        
                        # 簡化的完成條件：穩定次數 + 基本長度檢查
                        if (stable_count >= required_stable_count and 
                            len(current_response) >= min_response_length and
                            time_since_change >= 3):  # 至少穩定3秒
                            
                            self.logger.info(f"🎉 內容穩定確認完成！")
                            self.logger.info(f"  - 等待時間: {elapsed_time:.1f}秒")
                            self.logger.info(f"  - 穩定檢查: {stable_count} 次")
                            self.logger.info(f"  - 穩定時間: {time_since_change:.1f}秒")
                            self.logger.info(f"  - 回應長度: {len(current_response)} 字元")
                            
                            self.last_response = current_response
                            return True
                            
                    else:
                        # 內容有變化
                        if last_response:
                            self.logger.debug("📝 回應內容更新中...")
                        stable_count = 0
                        last_change_time = time.time()
                    
                    last_response = current_response
                    
                elif first_content_detected:
                    self.logger.warning("⚠️ 無法複製到內容，可能是複製操作失敗")
                else:
                    self.logger.debug(f"等待 Copilot 開始回應... ({elapsed_time:.1f}秒)")
                
                # 暫停後繼續檢查
                time.sleep(check_interval)
                
                # 定期報告狀態（每10秒）
                if int(elapsed_time) % 10 == 0 and int(elapsed_time) > 0:
                    status = "有內容" if current_response else "無內容"
                    
                    # 加入圖像檢測狀態
                    image_status = ""
                    try:
                        if copilot_status['has_stop_button']:
                            image_status = ", UI狀態: 回應中(stop)"
                        elif copilot_status['has_send_button']:
                            image_status = ", UI狀態: 完成(send)"
                        else:
                            image_status = ", UI狀態: 不明"
                        
                        if copilot_status.get('notifications_cleared', False):
                            image_status += " (已清除通知)"
                            
                    except:
                        image_status = ", UI狀態: 檢測失敗"
                    
                    self.logger.info(f"⏱️ 已等待 {int(elapsed_time)} 秒 ({status}, 長度: {len(current_response) if current_response else 0}{image_status})")
            
            # 超時處理
            self.logger.warning(f"⏰ 智能等待超時 ({timeout}秒)")
            
            # 超時時，如果有回應內容就使用，否則返回失敗
            if last_response and len(last_response.strip()) > 50:
                self.logger.warning("💾 超時但有部分內容，嘗試使用現有回應")
                self.last_response = last_response
                return True
            else:
                self.logger.error("❌ 超時且無有效回應內容")
                return False
            
        except Exception as e:
            self.logger.error(f"智能等待時發生錯誤: {str(e)}")
            return False
            
    def _is_response_basic_complete(self, response: str) -> bool:
        """
        基本的回應完整性檢查（極簡版本）
        
        Args:
            response: Copilot 回應內容
            
        Returns:
            bool: 回應是否基本完整
        """
        # 基本長度檢查（降低要求）
        if not response or len(response.strip()) < 10:
            return False
            
        # 只檢查最明顯的未完成標記
        if '```' in response and response.count('```') % 2 != 0:
            return False  # 未閉合的程式碼區塊
        
        # 簡單的截斷檢查
        if response.rstrip().endswith(('...', '。。。')):
            return False
                
        return True
    
    def _try_copy_response_without_logging(self) -> str:
        """
        嘗試複製 Copilot 的回應內容 (用於智能等待，簡化版本)
        
        Returns:
            str: 回應內容，若複製失敗則返回空字串
        """
        try:
            # 保存當前剪貼簿內容
            original_clipboard = ""
            try:
                original_clipboard = pyperclip.paste()
            except:
                pass
            
            # 設置測試標記
            test_marker = f"__COPILOT_TEST_{int(time.time())}__"
            pyperclip.copy(test_marker)
            time.sleep(0.5)
            
            # 使用統一的複製方法
            # 1. Ctrl+Shift+I 聚焦到 Copilot Chat 輸入框
            pyautogui.hotkey('ctrl', 'shift', 'i')
            time.sleep(1)
            
            # 2. Ctrl+↑ 聚焦到 Copilot 回應
            pyautogui.hotkey('ctrl', 'up')
            time.sleep(1)
            
            # 3. Shift+F10 開啟右鍵選單
            pyautogui.hotkey('shift', 'f10')
            time.sleep(1)
            
            # 4. 一次方向鍵下，定位到"複製"
            pyautogui.press('down')
            time.sleep(0.3)
            
            # 5. Enter 執行複製
            pyautogui.press('enter')
            time.sleep(2)
            
            response = pyperclip.paste()
            
            if response and response != test_marker and len(response.strip()) > 20:
                # 驗證內容是否像是 Copilot 回應
                if self._validate_response_content(response):
                    return response
            
            return ""
            
        except Exception as e:
            return ""
        finally:
            # 嘗試恢復原始剪貼簿內容
            try:
                if original_clipboard and test_marker not in original_clipboard:
                    pyperclip.copy(original_clipboard)
            except:
                pass
    
    def _validate_response_content(self, response: str) -> bool:
        """驗證複製的內容是否是有效的 Copilot 回應"""
        if not response or len(response.strip()) < 30:
            return False
            
        # 檢查是否包含典型的 Copilot 回應特徵
        copilot_indicators = [
            '分析', '建議', '程式', '代碼', 'code', 'function', 'class',
            'import', 'def', 'var', 'let', 'const', '結構', '改進',
            '範例', 'example', '可以', '建議', '應該', '可能', '需要',
            '讓我', '我會', '以下', '首先', '接下來', '最後',
            '```', 'python', 'javascript', 'typescript', 'html', 'css'
        ]
        
        response_lower = response.lower()
        matches = sum(1 for indicator in copilot_indicators if indicator in response_lower)
        
        # 如果匹配多個指標，可能是有效回應
        return matches >= 2
    
    def copy_response(self) -> Optional[str]:
        """
        複製 Copilot 的回應內容 (使用鍵盤操作，支援重試)
        
        Returns:
            Optional[str]: 回應內容，若複製失敗則返回 None
        """
        for attempt in range(config.COPILOT_COPY_RETRY_MAX):
            try:
                self.logger.info(f"複製 Copilot 回應 (第 {attempt + 1}/{config.COPILOT_COPY_RETRY_MAX} 次)...")
                
                # 清空剪貼簿
                pyperclip.copy("")
                time.sleep(0.5)
                
                # 使用鍵盤操作複製回應
                # 1. Ctrl+Shift+I 聚焦到 Copilot Chat 輸入框
                pyautogui.hotkey('ctrl', 'shift', 'i')
                time.sleep(1)
                
                # 2. Ctrl+↑ 聚焦到 Copilot 回應
                pyautogui.hotkey('ctrl', 'up')
                time.sleep(1)
                
                # 3. Shift+F10 開啟右鍵選單
                pyautogui.hotkey('shift', 'f10')
                time.sleep(1)
                
                # 4. 一次方向鍵下，定位到"複製"
                pyautogui.press('down')
                time.sleep(0.3)
                
                # 5. Enter 執行複製
                pyautogui.press('enter')
                time.sleep(2)  # 增加等待時間確保複製完成
                
                # 取得剪貼簿內容
                response = pyperclip.paste()
                if response and len(response.strip()) > 0:
                    self.last_response = response
                    self.logger.copilot_interaction("複製回應", "SUCCESS", f"長度: {len(response)} 字元")
                    return response
                else:
                    self.logger.warning(f"第 {attempt + 1} 次複製失敗，剪貼簿內容為空")
                    if attempt < config.COPILOT_COPY_RETRY_MAX - 1:
                        self.logger.info(f"等待 {config.COPILOT_COPY_RETRY_DELAY} 秒後重試...")
                        time.sleep(config.COPILOT_COPY_RETRY_DELAY)
                        continue
                
            except Exception as e:
                self.logger.error(f"第 {attempt + 1} 次複製時發生錯誤: {str(e)}")
                if attempt < config.COPILOT_COPY_RETRY_MAX - 1:
                    self.logger.info(f"等待 {config.COPILOT_COPY_RETRY_DELAY} 秒後重試...")
                    time.sleep(config.COPILOT_COPY_RETRY_DELAY)
                    continue
        
        self.logger.copilot_interaction("複製回應", "ERROR", f"重試 {config.COPILOT_COPY_RETRY_MAX} 次後仍然失敗")
        return None
    
    def test_vscode_close_ready(self) -> bool:
        """
        測試 VS Code 是否可以關閉（檢測 Copilot 是否已完成回應）
        
        Returns:
            bool: 如果可以關閉返回 True，否則返回 False
        """
        try:
            self.logger.debug("測試 VS Code 是否可以關閉...")
            
            # 嘗試使用 Alt+F4 關閉視窗
            pyautogui.hotkey('alt', 'f4')
            time.sleep(1)
            
            # 檢查是否還有 VS Code 進程在運行（只檢查自動開啟的）
            from src.vscode_controller import vscode_controller
            
            still_running = []
            for proc in psutil.process_iter(['pid', 'name']):
                if ('code' in proc.info['name'].lower() and 
                    proc.info['pid'] not in vscode_controller.pre_existing_vscode_pids):
                    still_running.append(proc.info['pid'])
            
            if not still_running:
                self.logger.debug("✅ VS Code 已成功關閉，Copilot 回應應該已完成")
                return True
            else:
                self.logger.debug(f"⚠️ VS Code 仍在運行 (PID: {still_running})，可能 Copilot 仍在回應中")
                return False
                
        except Exception as e:
            self.logger.error(f"測試 VS Code 關閉狀態時發生錯誤: {str(e)}")
            return False
    
    def save_response_to_file(self, project_path: str, response: str = None, is_success: bool = True, **kwargs) -> bool:
        """
        將回應儲存到統一的 ExecutionResult 資料夾
        
        Args:
            project_path: 專案路徑
            response: 回應內容，若為 None 則使用最後一次的回應
            is_success: 是否成功執行
            **kwargs: 額外參數，如 round_number（互動輪數）
        
        Returns:
            bool: 儲存是否成功
        """
        try:
            if response is None:
                response = self.last_response
            
            if not response:
                self.logger.error("沒有可儲存的回應內容")
                return False
            
            project_dir = Path(project_path)
            project_name = project_dir.name
            
            # 建立統一的 ExecutionResult 資料夾結構（在腳本根目錄）
            script_root = Path(__file__).parent.parent  # 腳本根目錄
            execution_result_dir = script_root / "ExecutionResult"
            result_subdir = execution_result_dir / ("Success" if is_success else "Fail")
            
            # 建立專案專屬資料夾
            project_subdir = result_subdir / project_name
            project_subdir.mkdir(parents=True, exist_ok=True)
            
            # 生成檔名（包含時間戳記和輪數，用於反覆互動的版本控制）
            timestamp = time.strftime('%Y%m%d_%H%M')
            round_number = kwargs.get('round_number', 1)
            output_file = project_subdir / f"{timestamp}_第{round_number}輪.md"
            
            self.logger.info(f"儲存回應到: {output_file}")
            
            # 創建檔案並寫入內容
            round_number = kwargs.get('round_number', 1)
            prompt_text = kwargs.get('prompt_text', "使用預設提示詞")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# Copilot 自動補全記錄\n")
                f.write(f"# 生成時間: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# 專案: {project_name}\n")
                f.write(f"# 專案路徑: {project_path}\n")
                f.write(f"# 互動輪數: 第 {round_number} 輪\n")
                f.write(f"# 執行狀態: {'成功' if is_success else '失敗'}\n")
                f.write("=" * 50 + "\n\n")
                
                # 添加使用的提示詞
                f.write("## 本輪提示詞\n\n")
                f.write(prompt_text)
                f.write("\n\n")
                
                # 添加回應內容
                f.write("## Copilot 回應\n\n")
                f.write(response)
            
            self.logger.copilot_interaction("儲存回應", "SUCCESS", f"檔案: {output_file.name}")
            
            # 等待短暫時間確保檔案完全寫入
            time.sleep(0.5)
            return True
            
        except Exception as e:
            self.logger.copilot_interaction("儲存回應", "ERROR", str(e))
            return False
    
    def process_project_complete(self, project_path: str, use_smart_wait: bool = None, 
                               round_number: int = 1, custom_prompt: str = None) -> Tuple[bool, Optional[str]]:
        """
        完整處理一個專案（發送提示 -> 等待回應 -> 複製並儲存）
        
        Args:
            project_path: 專案路徑
            use_smart_wait: 是否使用智能等待，若為 None 則使用配置值
            round_number: 當前互動輪數
            custom_prompt: 自定義提示詞，若為 None 則使用預設提示詞
            
        Returns:
            Tuple[bool, Optional[str]]: (是否成功, 錯誤訊息)
        """
        try:
            project_name = Path(project_path).name
            self.logger.create_separator(f"處理專案: {project_name} (第 {round_number} 輪)")
            
            # 步驟1: 開啟 Copilot Chat
            if not self.open_copilot_chat():
                return False, "無法開啟 Copilot Chat"
            
            # 步驟2: 發送提示詞
            if not self.send_prompt(prompt=custom_prompt):
                return False, "無法發送提示詞"
                
            # 保存實際使用的提示詞，用於記錄
            actual_prompt = custom_prompt or self._load_prompt_from_file()
            
            # 步驟3: 等待回應 (使用指定的等待模式)
            if not self.wait_for_response(use_smart_wait=use_smart_wait):
                return False, "等待回應超時"
            
            # 步驟4: 複製回應
            response = self.copy_response()
            if not response:
                return False, "無法複製回應內容"
            
            # 步驟5: 儲存到檔案
            if not self.save_response_to_file(
                project_path, 
                response, 
                is_success=True, 
                round_number=round_number,
                prompt_text=actual_prompt
            ):
                return False, "無法儲存回應到檔案"
            
            # 確保檔案寫入完成後再繼續（避免競爭條件）
            time.sleep(1)
            
            self.logger.copilot_interaction(f"第 {round_number} 輪處理完成", "SUCCESS", project_name)
            return True, response  # 返回成功狀態和回應內容，供後續輪次使用
            
        except Exception as e:
            error_msg = f"處理專案時發生錯誤: {str(e)}"
            self.logger.copilot_interaction("專案處理", "ERROR", error_msg)
            
            # 儲存失敗記錄到 Fail 資料夾
            try:
                self.save_response_to_file(project_path, error_msg, is_success=False)
            except:
                pass  # 如果連錯誤日誌都無法儲存，就忽略
                
            return False, error_msg
    
    def clear_chat_history(self) -> bool:
        """
        清除聊天記錄（透過重新開啟專案來達到記憶隔離的效果）
        
        Returns:
            bool: 清除是否成功
        """
        try:
            self.logger.info("清除 Copilot Chat 記錄...")
            # 使用控制器進行記憶清除
            from src.vscode_controller import vscode_controller
            result = vscode_controller.clear_copilot_memory()
            return result
        except Exception as e:
            self.logger.error(f"清除聊天記錄失敗: {str(e)}")
            return False
            
    def create_next_round_prompt(self, base_prompt: str, previous_response: str) -> str:
        """
        根據上一輪回應和原始提示詞組合成下一輪提示詞
        
        Args:
            base_prompt: 基礎提示詞
            previous_response: 上一輪的回應內容
            
        Returns:
            str: 新的提示詞
        """
        # 確保 previous_response 不為空且有實際內容
        if not previous_response or len(previous_response.strip()) < 10:
            self.logger.warning("上一輪回應內容過短或為空，使用基礎提示詞")
            return base_prompt
        
        # 清理 previous_response，移除可能的格式問題
        cleaned_response = previous_response.strip()
        
        # 使用配置中的前綴和後綴
        prefix = config.INTERACTION_RESPONSE_CHAINING_PREFIX
        suffix = config.INTERACTION_RESPONSE_CHAINING_SUFFIX
        continuation_text = "\n請記住前面的對話脈絡，繼續深入探討或回答問題。"
        
        # 組合新的提示詞
        next_prompt = f"{prefix}{cleaned_response}{suffix}{base_prompt}{continuation_text}"
        
        return next_prompt
    
    def _read_previous_round_response(self, project_path: str, round_number: int) -> Optional[str]:
        """
        讀取指定輪數的 Copilot 回應內容
        
        Args:
            project_path: 專案路徑
            round_number: 要讀取的輪數
            
        Returns:
            Optional[str]: Copilot 回應內容，如果讀取失敗則返回 None
        """
        try:
            project_name = Path(project_path).name
            script_root = Path(__file__).parent.parent
            execution_result_dir = script_root / "ExecutionResult" / "Success" / project_name
            
            # 尋找該輪次的檔案（使用萬用字元匹配時間戳記）
            pattern = f"*_第{round_number}輪.md"
            matching_files = list(execution_result_dir.glob(pattern))
            
            if not matching_files:
                self.logger.warning(f"找不到第 {round_number} 輪的回應檔案")
                return None
            
            # 取最新的檔案（如果有多個）
            latest_file = max(matching_files, key=lambda x: x.stat().st_mtime)
            
            # 讀取檔案內容並提取 Copilot 回應部分
            with open(latest_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取 "## Copilot 回應" 之後的內容
            response_marker = "## Copilot 回應\n\n"
            if response_marker in content:
                response_content = content.split(response_marker, 1)[1]
                self.logger.debug(f"成功讀取第 {round_number} 輪回應內容 (長度: {len(response_content)} 字元)")
                return response_content.strip()
            else:
                self.logger.warning(f"在第 {round_number} 輪檔案中找不到回應標記")
                return None
                
        except Exception as e:
            self.logger.error(f"讀取第 {round_number} 輪回應時發生錯誤: {str(e)}")
            return None
    
    def get_latest_response_file(self, project_path: str) -> Optional[Path]:
        """
        獲取指定專案的最新回應檔案
        
        Args:
            project_path: 專案路徑
            
        Returns:
            Optional[Path]: 檔案路徑，若無檔案則返回 None
        """
        try:
            project_name = Path(project_path).name
            script_root = Path(__file__).parent.parent  # 腳本根目錄
            project_result_dir = script_root / "ExecutionResult" / "Success" / project_name
            
            if not project_result_dir.exists():
                return None
            
            # 找出所有回應檔案
            response_files = list(project_result_dir.glob("*_第*輪.md"))
            
            if not response_files:
                return None
                
            # 根據修改時間排序，取最新的
            latest_file = max(response_files, key=lambda f: f.stat().st_mtime)
            return latest_file
            
        except Exception as e:
            self.logger.error(f"獲取最新回應檔案失敗: {str(e)}")
            return None
            
    def read_previous_response(self, project_path: str) -> Optional[str]:
        """
        讀取上一輪的回應內容
        
        Args:
            project_path: 專案路徑
            
        Returns:
            Optional[str]: 上一輪的回應內容，若無法讀取則返回 None
        """
        try:
            latest_file = self.get_latest_response_file(project_path)
            if not latest_file:
                return None
                
            # 讀取檔案內容
            with open(latest_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 提取 Copilot 回應部分
            response_marker = "## Copilot 回應\n\n"
            if response_marker in content:
                response = content.split(response_marker)[1]
                return response
                
            # 舊格式檔案處理
            separator = "=" * 50 + "\n\n"
            if separator in content:
                response = content.split(separator)[1]
                return response
                
            return None
            
        except Exception as e:
            self.logger.error(f"讀取上一輪回應失敗: {str(e)}")
            return None
    
    def _load_interaction_settings(self) -> dict:
        """
        載入互動設定
        
        Returns:
            dict: 互動設定字典
        """
        # 優先使用外部設定（來自 UI）
        if self.interaction_settings is not None:
            self.logger.info(f"使用外部提供的互動設定: {self.interaction_settings}")
            return self.interaction_settings
        
        # 如果沒有外部設定，使用檔案或預設值
        settings_file = config.PROJECT_ROOT / "config" / "interaction_settings.json"
        default_settings = {
            "interaction_enabled": config.INTERACTION_ENABLED,
            "max_rounds": config.INTERACTION_MAX_ROUNDS,
            "include_previous_response": config.INTERACTION_INCLUDE_PREVIOUS_RESPONSE,
            "round_delay": config.INTERACTION_ROUND_DELAY
        }
        
        if settings_file.exists():
            try:
                import json
                with open(settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    default_settings.update(loaded_settings)
                    self.logger.info(f"已載入互動設定檔案: {loaded_settings}")
            except Exception as e:
                self.logger.warning(f"載入互動設定時發生錯誤，使用預設值: {e}")
        else:
            self.logger.info("未找到互動設定檔案，使用預設值")
        
        return default_settings

    def process_project_with_iterations(self, project_path: str, max_rounds: int = None) -> bool:
        """
        處理一個專案的多輪互動
        
        Args:
            project_path: 專案路徑
            max_rounds: 最大互動輪數
            
        Returns:
            bool: 處理是否成功
        """
        try:
            # 載入互動設定
            interaction_settings = self._load_interaction_settings()
            
            # 檢查是否啟用多輪互動
            if not interaction_settings["interaction_enabled"]:
                self.logger.info("多輪互動功能已停用，執行單輪互動")
                success, result = self.process_project_complete(project_path, round_number=1)
                return success
            
            # 使用設定中的參數
            if max_rounds is None:
                max_rounds = interaction_settings["max_rounds"]
            
            round_delay = interaction_settings["round_delay"]
            include_previous_response = interaction_settings["include_previous_response"]
                
            project_name = Path(project_path).name
            self.logger.create_separator(f"開始處理專案 {project_name}，計劃互動 {max_rounds} 輪")
            self.logger.info(f"回應串接功能: {'啟用' if include_previous_response else '停用'}")
            
            # 讀取基礎提示詞
            base_prompt = self._load_prompt_from_file()
            if not base_prompt:
                self.logger.error("無法讀取基礎提示詞")
                return False
            
            # 追蹤每一輪的成功狀態
            success_count = 0
            last_response = None
            
            # 進行多輪互動
            for round_num in range(1, max_rounds + 1):
                self.logger.create_separator(f"開始第 {round_num} 輪互動")
                
                # 根據設定和上一輪結果準備本輪提示詞
                current_prompt = base_prompt
                if round_num > 1 and include_previous_response:
                    # 從上一輪的檔案中讀取實際的 Copilot 回應內容
                    previous_response_content = self._read_previous_round_response(project_path, round_num - 1)
                    if previous_response_content:
                        current_prompt = self.create_next_round_prompt(base_prompt, previous_response_content)
                        self.logger.info(f"已讀取第 {round_num - 1} 輪回應內容用於組合新提示詞 (內容長度: {len(previous_response_content)} 字元)")
                    else:
                        self.logger.warning(f"無法讀取第 {round_num - 1} 輪回應內容，使用基礎提示詞")
                        current_prompt = base_prompt
                elif round_num > 1 and not include_previous_response:
                    self.logger.info(f"第 {round_num} 輪：根據設定，不包含上一輪回應，使用基礎提示詞")
                    current_prompt = base_prompt
                
                if round_num > 1:
                    # 清除 Copilot 記憶（每輪獨立）
                    from src.vscode_controller import vscode_controller
                    vscode_controller.clear_copilot_memory()
                    time.sleep(1)  # 等待記憶清除完成
                
                # 處理本輪互動
                success, result = self.process_project_complete(
                    project_path, 
                    use_smart_wait=None,
                    round_number=round_num,
                    custom_prompt=current_prompt
                )
                
                if success:
                    success_count += 1
                    last_response = result
                    self.logger.info(f"✅ 第 {round_num} 輪互動成功")
                else:
                    self.logger.error(f"❌ 第 {round_num} 輪互動失敗: {result}")
                    break
                
                # 輪次間暫停
                if round_num < max_rounds:
                    self.logger.info(f"等待 {round_delay} 秒後進行下一輪...")
                    time.sleep(round_delay)
            
            # 處理結束
            total_result = f"完成 {success_count}/{max_rounds} 輪互動"
            
            # 互動完成後的穩定期，確保背景任務完成
            cooldown_time = 5  # 秒
            self.logger.info(f"所有互動輪次完成，進入穩定期 {cooldown_time} 秒...")
            time.sleep(cooldown_time)
            
            # 如果全部成功，記錄成功狀態
            if success_count == max_rounds:
                self.logger.info(f"✅ {project_name} 所有互動輪次成功完成")
                return True
            else:
                self.logger.warning(f"⚠️ {project_name} 只完成部分互動: {total_result}")
                return success_count > 0  # 至少完成一輪即為部分成功
                
        except Exception as e:
            self.logger.error(f"專案互動處理出錯: {str(e)}")
            return False

# 創建全域實例
copilot_handler = CopilotHandler()

# 便捷函數
def process_project_with_copilot(project_path: str, use_smart_wait: bool = None) -> Tuple[bool, Optional[str]]:
    """處理專案的便捷函數"""
    return copilot_handler.process_project_complete(project_path, use_smart_wait)

def send_copilot_prompt(prompt: str = None) -> bool:
    """發送提示詞的便捷函數"""
    return copilot_handler.send_prompt(prompt)

def wait_for_copilot_response(timeout: int = None, use_smart_wait: bool = None) -> bool:
    """等待回應的便捷函數"""
    return copilot_handler.wait_for_response(timeout, use_smart_wait)
    
def process_with_iterations(project_path: str, max_rounds: int = None) -> bool:
    """多輪互動處理的便捷函數"""
    return copilot_handler.process_project_with_iterations(project_path, max_rounds)
    return copilot_handler.process_project_with_iterations(project_path, max_rounds)