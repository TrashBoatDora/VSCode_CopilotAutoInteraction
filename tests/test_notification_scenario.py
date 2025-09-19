# -*- coding: utf-8 -*-
"""
模擬通知干擾場景測試
測試當按鈕被通知遮擋時的自動清除機制
"""

import sys
import time
from pathlib import Path

# 添加項目根目錄到路徑
sys.path.append(str(Path(__file__).parent))

from src.image_recognition import ImageRecognition
from src.logger import get_logger

class MockImageRecognition(ImageRecognition):
    """模擬的圖像識別類，用於測試通知清除場景"""
    
    def __init__(self):
        super().__init__()
        self.call_count = 0
        self.simulate_notification_interference = True
    
    def find_image_on_screen(self, template_path: str, confidence: float = None, region=None):
        """模擬圖像檢測，第一次調用時模擬按鈕被遮擋"""
        self.call_count += 1
        
        # 模擬第一次檢測時按鈕被通知遮擋
        if self.simulate_notification_interference and self.call_count <= 2:
            self.logger.debug(f"模擬通知遮擋：無法檢測到按鈕 {Path(template_path).name}")
            return None
        
        # 模擬清除通知後能正常檢測
        if "send_button" in template_path:
            self.logger.debug("模擬清除通知後檢測到 send 按鈕")
            return (100, 100, 50, 30)  # 模擬按鈕位置
        
        return None

def test_notification_interference_scenario():
    """測試通知干擾場景"""
    logger = get_logger("NotificationInterferenceTest")
    
    logger.info("=" * 60)
    logger.info("測試通知干擾場景")
    logger.info("=" * 60)
    
    try:
        # 使用模擬的圖像識別器
        mock_image_recognition = MockImageRecognition()
        
        logger.info("場景: 模擬通知遮擋 UI 按鈕")
        logger.info("預期行為: 系統應檢測到按鈕被遮擋並自動清除通知")
        
        # 第一次檢查 - 模擬按鈕被遮擋
        logger.info("第一次狀態檢查（模擬按鈕被遮擋）...")
        status1 = mock_image_recognition.check_copilot_response_status()
        
        logger.info("第一次檢查結果:")
        logger.info(f"  - 有 stop 按鈕: {status1['has_stop_button']}")
        logger.info(f"  - 有 send 按鈕: {status1['has_send_button']}")
        logger.info(f"  - 狀態訊息: {status1['status_message']}")
        logger.info(f"  - 通知已清除: {status1.get('notifications_cleared', False)}")
        
        # 驗證是否觸發了通知清除
        if status1.get('notifications_cleared', False):
            logger.info("✅ 成功觸發通知清除機制")
        else:
            logger.warning("⚠️ 未觸發通知清除機制")
        
        # 第二次檢查 - 模擬清除通知後的狀態
        logger.info("第二次狀態檢查（模擬清除通知後）...")
        mock_image_recognition.simulate_notification_interference = False
        mock_image_recognition.call_count = 0  # 重置計數器
        
        status2 = mock_image_recognition.check_copilot_response_status()
        
        logger.info("第二次檢查結果:")
        logger.info(f"  - 有 stop 按鈕: {status2['has_stop_button']}")
        logger.info(f"  - 有 send 按鈕: {status2['has_send_button']}")
        logger.info(f"  - 狀態訊息: {status2['status_message']}")
        logger.info(f"  - 通知已清除: {status2.get('notifications_cleared', False)}")
        
        logger.info("=" * 60)
        logger.info("測試完成")
        
        # 總結
        if status1.get('notifications_cleared', False) and status2['has_send_button']:
            logger.info("✅ 通知干擾處理機制運行正常")
            return True
        else:
            logger.warning("⚠️ 通知干擾處理機制可能有問題")
            return False
        
    except Exception as e:
        logger.error(f"測試過程中發生錯誤: {str(e)}")
        return False

def test_real_scenario_guide():
    """真實場景測試指南"""
    logger = get_logger("RealScenarioGuide")
    
    logger.info("=" * 60)
    logger.info("真實場景測試指南")
    logger.info("=" * 60)
    
    logger.info("要在真實環境中測試通知清除功能，請按照以下步驟:")
    logger.info("")
    logger.info("準備步驟:")
    logger.info("1. 開啟 VS Code")
    logger.info("2. 確保 Copilot Chat 擴展已安裝並啟用")
    logger.info("3. 開啟一個項目")
    logger.info("")
    logger.info("觸發通知:")
    logger.info("1. 安裝一個新的 VS Code 擴展（會產生通知）")
    logger.info("2. 或者故意在程式碼中製造語法錯誤（會產生錯誤通知）")
    logger.info("3. 或者使用 Ctrl+Shift+P 然後輸入 'Developer: Reload Window'")
    logger.info("4. 確保右下角有通知彈出")
    logger.info("")
    logger.info("執行測試:")
    logger.info("1. 運行主自動化腳本: python main.py")
    logger.info("2. 選擇一個項目進行處理")
    logger.info("3. 啟用智能等待功能")
    logger.info("4. 觀察智能等待過程中的日誌輸出")
    logger.info("")
    logger.info("預期行為:")
    logger.info("- 當系統檢測不到 send_button 和 stop_button 時")
    logger.info("- 日誌會顯示 '⚠️ 同時檢測不到 stop 或 send 按鈕，可能有通知遮擋 UI'")
    logger.info("- 系統會自動執行 Ctrl+Shift+P")
    logger.info("- 輸入 'Notifications: Clear All Notifications'")
    logger.info("- 按 Enter 執行命令")
    logger.info("- 然後重新檢測按鈕狀態")
    logger.info("- 日誌會顯示 '🔄 已清除 VS Code 通知，繼續檢測...'")
    logger.info("")
    logger.info("驗證成功的標誌:")
    logger.info("- 通知消失")
    logger.info("- 系統能正常檢測到 send_button 或 stop_button")
    logger.info("- 智能等待繼續正常運行")
    logger.info("=" * 60)

if __name__ == "__main__":
    print("通知干擾場景測試")
    print("請選擇測試類型:")
    print("1. 模擬測試（使用模擬數據）")
    print("2. 真實場景測試指南")
    print("3. 執行所有測試")
    
    choice = input("請輸入選擇 (1-3): ").strip()
    
    if choice == "1":
        test_notification_interference_scenario()
    elif choice == "2":
        test_real_scenario_guide()
    elif choice == "3":
        test_notification_interference_scenario()
        print("\n" + "="*40 + "\n")
        test_real_scenario_guide()
    else:
        print("無效選擇，退出測試")