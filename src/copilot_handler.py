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
    
    def __init__(self, error_handler=None):
        """初始化 Copilot 處理器"""
        self.logger = get_logger("CopilotHandler")
        self.is_chat_open = False
        self.last_response = ""
        self.error_handler = error_handler  # 添加 error_handler 引用
        self.image_recognition = image_recognition  # 添加圖像識別引用
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
        嘗試複製 Copilot 的回應內容 (用於智能等待，穩定版)
        
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
            
            # 多種方法嘗試複製
            methods = [
                self._try_copy_method_context_menu,
                self._try_copy_method_keyboard_only,
                self._try_copy_method_alternative
            ]
            
            for i, method in enumerate(methods):
                try:
                    self.logger.debug(f"嘗試複製方法 {i + 1}/{len(methods)}")
                    response = method()
                    
                    if response and response != test_marker and len(response.strip()) > 20:
                        # 驗證內容是否像是 Copilot 回應
                        if self._validate_response_content(response):
                            return response
                        
                except Exception as e:
                    self.logger.debug(f"複製方法 {i + 1} 失敗: {e}")
                    continue
            
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
    
    def _try_copy_method_context_menu(self) -> str:
        """使用右鍵選單複製"""
        # 確保 VS Code 處於活動狀態
        pyautogui.click(500, 300)
        time.sleep(0.3)
        
        # 聚焦到 Copilot Chat
        pyautogui.hotkey('ctrl', 'shift', 'i')
        time.sleep(1.0)
        
        # 聚焦到回應區域
        pyautogui.hotkey('ctrl', 'up')
        time.sleep(1.0)
        
        # 選擇所有內容
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)
        
        # 開啟右鍵選單
        pyautogui.hotkey('shift', 'f10')
        time.sleep(0.8)
        
        # 選擇複製選項 (通常是第2個選項)
        pyautogui.press('down')
        time.sleep(0.3)
        pyautogui.press('down')
        time.sleep(0.3)
        pyautogui.press('enter')
        time.sleep(1.5)
        
        return pyperclip.paste()
    
    def _try_copy_method_keyboard_only(self) -> str:
        """使用純鍵盤操作複製"""
        # 確保 VS Code 活動
        pyautogui.hotkey('alt', 'tab')
        time.sleep(0.5)
        
        # 聚焦到 Copilot Chat
        pyautogui.hotkey('ctrl', 'shift', 'i')
        time.sleep(1.0)
        
        # 跳轉到回應區域
        pyautogui.hotkey('ctrl', 'up')
        time.sleep(1.0)
        
        # 全選並複製
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(1.5)
        
        return pyperclip.paste()
    
    def _try_copy_method_alternative(self) -> str:
        """替代複製方法"""
        # 重新聚焦到 VS Code
        pyautogui.hotkey('ctrl', 'shift', 'i')
        time.sleep(0.8)
        
        # 使用 Tab 導航到回應區域
        pyautogui.press('tab')
        time.sleep(0.3)
        pyautogui.press('tab')
        time.sleep(0.3)
        
        # 全選並複製
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(1.2)
        
        return pyperclip.paste()
    
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
                
                # 4. 兩次方向鍵下，定位到"複製全部"
                pyautogui.press('down')
                time.sleep(0.3)
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
    
    def save_response_to_file(self, project_path: str, response: str = None, is_success: bool = True) -> bool:
        """
        將回應儲存到統一的 ExecutionResult 資料夾
        
        Args:
            project_path: 專案路徑
            response: 回應內容，若為 None 則使用最後一次的回應
            is_success: 是否成功執行
        
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
            
            # 生成檔名（包含時間戳記，用於反覆互動的版本控制）
            timestamp = time.strftime('%Y%m%d_%H%M')
            output_file = project_subdir / f"Copilot_AutoComplete_{timestamp}.md"
            
            self.logger.info(f"儲存回應到: {output_file}")
            
            # 創建檔案並寫入內容
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# Copilot 自動補全記錄\n")
                f.write(f"# 生成時間: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# 專案: {project_name}\n")
                f.write(f"# 專案路徑: {project_path}\n")
                f.write(f"# 執行狀態: {'成功' if is_success else '失敗'}\n")
                f.write("=" * 50 + "\n\n")
                f.write(response)
            
            self.logger.copilot_interaction("儲存回應", "SUCCESS", f"檔案: {output_file.name}")
            
            # 等待短暫時間確保檔案完全寫入
            time.sleep(0.5)
            return True
            
        except Exception as e:
            self.logger.copilot_interaction("儲存回應", "ERROR", str(e))
            return False
    
    def process_project_complete(self, project_path: str, use_smart_wait: bool = None) -> Tuple[bool, Optional[str]]:
        """
        完整處理一個專案（發送提示 -> 等待回應 -> 複製並儲存）
        
        Args:
            project_path: 專案路徑
            use_smart_wait: 是否使用智能等待，若為 None 則使用配置值
            
        Returns:
            Tuple[bool, Optional[str]]: (是否成功, 錯誤訊息)
        """
        try:
            project_name = Path(project_path).name
            self.logger.create_separator(f"處理專案: {project_name}")
            
            # 步驟1: 開啟 Copilot Chat
            if not self.open_copilot_chat():
                return False, "無法開啟 Copilot Chat"
            
            # 步驟2: 發送提示詞
            if not self.send_prompt():
                return False, "無法發送提示詞"
            
            # 步驟3: 等待回應 (使用指定的等待模式)
            if not self.wait_for_response(use_smart_wait=use_smart_wait):
                return False, "等待回應超時"
            
            # 步驟4: 複製回應
            response = self.copy_response()
            if not response:
                return False, "無法複製回應內容"
            
            # 步驟5: 儲存到檔案
            if not self.save_response_to_file(project_path, response, is_success=True):
                return False, "無法儲存回應到檔案"
            
            # 確保檔案寫入完成後再繼續（避免競爭條件）
            time.sleep(1)
            
            self.logger.copilot_interaction("專案處理完成", "SUCCESS", project_name)
            return True, None
            
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
            
            # 透過關閉專案來清除記憶，達到記憶隔離的效果
            self.is_chat_open = False
            self.last_response = ""
            
            self.logger.copilot_interaction("清除聊天記錄", "INFO", "透過關閉專案來清除記憶")
            return True
            
        except Exception as e:
            self.logger.copilot_interaction("清除聊天記錄", "ERROR", str(e))
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