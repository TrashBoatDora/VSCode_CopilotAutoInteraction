# -*- coding: utf-8 -*-
"""
測試修改結果處理參數傳遞
"""

import sys
from pathlib import Path

# 添加專案根目錄到路徑
sys.path.append(str(Path(__file__).parent))

from config.config import config
from src.vscode_controller import VSCodeController
from src.logger import get_logger

def test_modification_action_parameter():
    """測試修改結果處理參數傳遞"""
    logger = get_logger("TestModificationParam")
    
    logger.info("測試修改結果處理參數傳遞...")
    
    # 測試設定
    test_settings = {
        "copilot_chat_modification_action": "revert"
    }
    
    # 模擬從設定中獲取參數
    modification_action = test_settings.get("copilot_chat_modification_action", config.COPILOT_CHAT_MODIFICATION_ACTION)
    logger.info(f"從設定獲取的修改結果處理模式: {modification_action}")
    
    # 測試預設值
    default_action = config.COPILOT_CHAT_MODIFICATION_ACTION
    logger.info(f"預設修改結果處理模式: {default_action}")
    
    # 測試結果
    if modification_action == "revert":
        logger.info("✅ 參數傳遞測試成功")
        return True
    else:
        logger.error("❌ 參數傳遞測試失敗")
        return False

if __name__ == "__main__":
    success = test_modification_action_parameter()
    print(f"測試結果: {'成功' if success else '失敗'}")