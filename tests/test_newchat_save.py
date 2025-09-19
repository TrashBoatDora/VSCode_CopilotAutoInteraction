# -*- coding: utf-8 -*-
"""
測試新增的 NewChat_Save 對話框檢測功能
"""

import sys
from pathlib import Path

# 添加專案根目錄到路徑
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))

from config.config import config
from src.image_recognition import check_newchat_save_dialog, handle_newchat_save_dialog
from src.logger import get_logger

def test_newchat_save_detection():
    """測試 NewChat_Save 檢測功能"""
    logger = get_logger("TestNewChatSave")
    
    logger.info("開始測試 NewChat_Save 對話框檢測功能...")
    
    # 檢查配置是否正確設置
    logger.info(f"NewChat_Save 圖像路徑: {config.NEWCHAT_SAVE_IMAGE}")
    logger.info(f"圖像檔案是否存在: {config.NEWCHAT_SAVE_IMAGE.exists()}")
    
    if not config.NEWCHAT_SAVE_IMAGE.exists():
        logger.error("❌ NewChat_Save.png 檔案不存在")
        return False
    
    # 測試檢測功能（這會在 2 秒內查找圖像）
    logger.info("測試檢測功能（2秒超時）...")
    result = check_newchat_save_dialog(timeout=2)
    
    if result:
        logger.info("✅ 檢測到 NewChat_Save 對話框")
        logger.info("測試處理功能...")
        if handle_newchat_save_dialog():
            logger.info("✅ 成功處理對話框")
        else:
            logger.warning("⚠️ 處理對話框失敗")
    else:
        logger.info("ℹ️ 未檢測到 NewChat_Save 對話框（這是正常的，因為目前沒有顯示）")
    
    logger.info("測試完成")
    return True

if __name__ == "__main__":
    test_newchat_save_detection()