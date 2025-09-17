# -*- coding: utf-8 -*-
"""
測試通知清除功能
驗證新的通知清除機制是否正確工作
"""

import sys
import time
from pathlib import Path

# 添加項目根目錄到路徑
sys.path.append(str(Path(__file__).parent))

from src.image_recognition import image_recognition
from src.logger import get_logger

def test_notification_clearing():
    """測試通知清除功能"""
    logger = get_logger("NotificationTest")
    
    logger.info("=" * 60)
    logger.info("測試通知清除功能")
    logger.info("=" * 60)
    
    try:
        # 測試 1: 測試基本的通知清除功能
        logger.info("測試 1: 基本通知清除功能")
        result = image_recognition.clear_vscode_notifications()
        logger.info(f"通知清除結果: {'✅ 成功' if result else '❌ 失敗'}")
        
        time.sleep(2)
        
        # 測試 2: 測試完整的狀態檢查（包含通知清除）
        logger.info("測試 2: 完整的 Copilot 狀態檢查")
        status = image_recognition.check_copilot_response_status()
        
        logger.info("Copilot 狀態檢查結果:")
        logger.info(f"  - 有 stop 按鈕: {status['has_stop_button']}")
        logger.info(f"  - 有 send 按鈕: {status['has_send_button']}")
        logger.info(f"  - 正在回應: {status['is_responding']}")
        logger.info(f"  - 回應準備就緒: {status['is_ready']}")
        logger.info(f"  - 狀態訊息: {status['status_message']}")
        logger.info(f"  - 通知已清除: {status.get('notifications_cleared', False)}")
        
        # 測試 3: 測試按鈕檢測功能
        logger.info("測試 3: 個別按鈕檢測")
        
        stop_button = image_recognition.find_image_on_screen(
            str(Path(__file__).parent / "assets" / "stop_button.png"),
            confidence=0.8
        )
        send_button = image_recognition.find_image_on_screen(
            str(Path(__file__).parent / "assets" / "send_button.png"),
            confidence=0.8
        )
        
        logger.info(f"Stop 按鈕檢測: {'✅ 找到' if stop_button else '❌ 未找到'}")
        logger.info(f"Send 按鈕檢測: {'✅ 找到' if send_button else '❌ 未找到'}")
        
        if not stop_button and not send_button:
            logger.warning("⚠️ 兩個按鈕都未檢測到，這會觸發通知清除機制")
        
        logger.info("=" * 60)
        logger.info("測試完成")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"測試過程中發生錯誤: {str(e)}")
        return False

def test_manual_scenario():
    """手動測試場景指南"""
    logger = get_logger("ManualTest")
    
    logger.info("=" * 60)
    logger.info("手動測試場景指南")
    logger.info("=" * 60)
    
    logger.info("請按照以下步驟進行手動測試:")
    logger.info("")
    logger.info("1. 確保 VS Code 已開啟並載入 Copilot Chat")
    logger.info("2. 在 VS Code 中觸發一些通知（例如：安裝擴展、錯誤訊息等）")
    logger.info("3. 確保右下角有通知彈出，可能會遮擋到 UI 按鈕")
    logger.info("4. 運行主腳本並發送 prompt 給 Copilot")
    logger.info("5. 觀察智能等待過程中是否自動清除通知")
    logger.info("")
    logger.info("預期行為:")
    logger.info("- 當同時檢測不到 send_button 和 stop_button 時")
    logger.info("- 腳本應該自動按 Ctrl+Shift+P")
    logger.info("- 輸入 'Notifications: Clear All Notifications'")
    logger.info("- 按 Enter 執行命令")
    logger.info("- 繼續正常的智能等待流程")
    logger.info("")
    logger.info("注意事項:")
    logger.info("- 確保 VS Code 是當前焦點視窗")
    logger.info("- 確保沒有其他彈出視窗干擾")
    logger.info("- 觀察日誌輸出以確認功能正確執行")
    logger.info("=" * 60)

if __name__ == "__main__":
    print("通知清除功能測試")
    print("請選擇測試類型:")
    print("1. 自動測試基本功能")
    print("2. 顯示手動測試指南")
    print("3. 執行完整測試")
    
    choice = input("請輸入選擇 (1-3): ").strip()
    
    if choice == "1":
        test_notification_clearing()
    elif choice == "2":
        test_manual_scenario()
    elif choice == "3":
        test_notification_clearing()
        print("\n" + "="*40 + "\n")
        test_manual_scenario()
    else:
        print("無效選擇，退出測試")