# -*- coding: utf-8 -*-
"""
測試改進後的智能等待和通知清除功能
"""

import sys
import time
from pathlib import Path

# 添加項目根目錄到路徑
sys.path.append(str(Path(__file__).parent))

from src.image_recognition import image_recognition
from src.copilot_handler import copilot_handler
from src.logger import get_logger

def test_improved_notification_clearing():
    """測試改進後的通知清除功能"""
    logger = get_logger("ImprovedNotificationTest")
    
    logger.info("=" * 60)
    logger.info("測試改進後的通知清除功能")
    logger.info("=" * 60)
    
    try:
        # 測試 1: 測試使用剪貼簿的通知清除功能
        logger.info("測試 1: 改進的通知清除功能（剪貼簿方式）")
        result = image_recognition.clear_vscode_notifications()
        logger.info(f"通知清除結果: {'✅ 成功' if result else '❌ 失敗'}")
        
        time.sleep(2)
        
        # 測試 2: 測試自動清除通知的狀態檢查
        logger.info("測試 2: 自動清除通知的狀態檢查")
        status = image_recognition.check_copilot_response_status_with_auto_clear()
        
        logger.info("自動清除通知的狀態檢查結果:")
        logger.info(f"  - 有 stop 按鈕: {status['has_stop_button']}")
        logger.info(f"  - 有 send 按鈕: {status['has_send_button']}")
        logger.info(f"  - 正在回應: {status['is_responding']}")
        logger.info(f"  - 回應準備就緒: {status['is_ready']}")
        logger.info(f"  - 狀態訊息: {status['status_message']}")
        logger.info(f"  - 通知已清除: {status.get('notifications_cleared', False)}")
        
        # 測試 3: 比較新舊方法的行為差異
        logger.info("測試 3: 比較舊方法和新方法")
        
        # 舊方法（不自動清除）
        status_old = image_recognition.check_copilot_response_status()
        logger.info("舊方法（不自動清除通知）:")
        logger.info(f"  - 通知已清除: {status_old.get('notifications_cleared', False)}")
        
        time.sleep(1)
        
        # 新方法（自動清除）
        status_new = image_recognition.check_copilot_response_status_with_auto_clear()
        logger.info("新方法（自動清除通知）:")
        logger.info(f"  - 通知已清除: {status_new.get('notifications_cleared', False)}")
        
        logger.info("=" * 60)
        logger.info("通知清除功能測試完成")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"測試過程中發生錯誤: {str(e)}")
        return False

def test_simplified_smart_wait():
    """測試簡化後的智能等待功能"""
    logger = get_logger("SimplifiedSmartWaitTest")
    
    logger.info("=" * 60)
    logger.info("測試簡化後的智能等待功能")
    logger.info("=" * 60)
    
    try:
        logger.info("簡化後的智能等待特點:")
        logger.info("- 只使用圖像辨識和基本穩定性檢查")
        logger.info("- 每次檢測不到按鈕時自動清除通知")
        logger.info("- 降低穩定檢查次數和時間要求")
        logger.info("- 簡化內容完整性檢查")
        logger.info("")
        
        # 測試簡化的內容完整性檢查
        logger.info("測試簡化的內容完整性檢查:")
        
        test_responses = [
            ("", False, "空回應"),
            ("很短", False, "太短"),
            ("這是一個足夠長的回應內容，應該被認為是完整的", True, "正常回應"),
            ("程式碼範例：\n```python\nprint('hello')", False, "未閉合程式碼區塊"),
            ("程式碼範例：\n```python\nprint('hello')\n```", True, "正常程式碼區塊"),
            ("回應中斷了...", False, "明顯截斷"),
            ("正常的回應內容結束。", True, "正常結束")
        ]
        
        for response, expected, description in test_responses:
            result = copilot_handler._is_response_basic_complete(response)
            status = "✅ 通過" if result == expected else "❌ 失敗"
            logger.info(f"  {description}: {status} (預期: {expected}, 實際: {result})")
        
        logger.info("=" * 60)
        logger.info("簡化智能等待功能測試完成")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"測試過程中發生錯誤: {str(e)}")
        return False

def show_improvement_summary():
    """顯示改進總結"""
    logger = get_logger("ImprovementSummary")
    
    logger.info("=" * 60)
    logger.info("功能改進總結")
    logger.info("=" * 60)
    
    logger.info("✅ 已完成的改進:")
    logger.info("")
    logger.info("1. 通知清除觸發邏輯改進:")
    logger.info("   - 每次檢測不到按鈕時都會自動清除通知")
    logger.info("   - 新增 check_copilot_response_status_with_auto_clear() 方法")
    logger.info("   - 原有方法保持不變，提供選擇性")
    logger.info("")
    logger.info("2. 中文輸入法問題解決:")
    logger.info("   - 使用剪貼簿 (pyperclip) 來輸入命令")
    logger.info("   - 避免 typewrite 受中文輸入法干擾")
    logger.info("   - 自動保存和恢復原始剪貼簿內容")
    logger.info("   - 增加更多錯誤處理和恢復機制")
    logger.info("")
    logger.info("3. 智能等待邏輯簡化:")
    logger.info("   - 移除複雜的內容分析邏輯")
    logger.info("   - 只保留圖像辨識和基本穩定性檢查")
    logger.info("   - 降低穩定檢查次數 (5次→3次)")
    logger.info("   - 減少最小回應長度要求 (200→100字元)")
    logger.info("   - 簡化內容完整性檢查")
    logger.info("   - 縮短檢查間隔 (2秒→1.5秒)")
    logger.info("")
    logger.info("🎯 效果預期:")
    logger.info("- 更快的回應檢測速度")
    logger.info("- 更穩定的通知處理")
    logger.info("- 減少誤判和等待時間")
    logger.info("- 更好的中文環境相容性")
    logger.info("=" * 60)

if __name__ == "__main__":
    print("改進後功能測試")
    print("請選擇測試類型:")
    print("1. 測試改進的通知清除功能")
    print("2. 測試簡化的智能等待功能")
    print("3. 顯示改進總結")
    print("4. 執行所有測試")
    
    choice = input("請輸入選擇 (1-4): ").strip()
    
    if choice == "1":
        test_improved_notification_clearing()
    elif choice == "2":
        test_simplified_smart_wait()
    elif choice == "3":
        show_improvement_summary()
    elif choice == "4":
        test_improved_notification_clearing()
        print("\n" + "="*40 + "\n")
        test_simplified_smart_wait()
        print("\n" + "="*40 + "\n")
        show_improvement_summary()
    else:
        print("無效選擇，退出測試")