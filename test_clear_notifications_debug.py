# -*- coding: utf-8 -*-
"""
測試清除通知功能是否正常工作
"""

import sys
from pathlib import Path

# 添加專案根目錄到路徑
sys.path.append(str(Path(__file__).parent))

from src.image_recognition import clear_notifications
from src.logger import get_logger

def test_clear_notifications():
    """測試清除通知功能"""
    logger = get_logger("TestClearNotifications")
    
    logger.info("開始測試清除通知功能...")
    
    try:
        # 測試清除通知功能
        logger.info("執行清除通知...")
        result = clear_notifications()
        
        if result:
            logger.info("✅ 清除通知功能執行成功")
        else:
            logger.error("❌ 清除通知功能執行失敗")
        
        return result
        
    except Exception as e:
        logger.error(f"測試過程中發生錯誤: {str(e)}")
        return False

if __name__ == "__main__":
    test_clear_notifications()