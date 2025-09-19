# -*- coding: utf-8 -*-
"""
測試新的圖像檢測機制
"""

import sys
from pathlib import Path

# 添加專案根目錄到路徑
sys.path.append(str(Path(__file__).parent))

from src.image_recognition import image_recognition
from src.logger import get_logger

def test_new_detection():
    """測試新的 stop/send 按鈕檢測機制"""
    logger = get_logger("TestDetection")
    
    logger.info("開始測試新的圖像檢測機制...")
    
    # 測試圖像資源驗證
    logger.info("1. 測試圖像資源驗證...")
    if image_recognition.validate_required_images():
        logger.info("✅ 圖像資源驗證通過")
    else:
        logger.warning("⚠️ 圖像資源驗證失敗，但會繼續執行")
    
    # 測試基本檢測方法
    logger.info("2. 測試基本檢測方法...")
    is_ready = image_recognition.check_copilot_response_ready()
    logger.info(f"Copilot 回應準備狀態: {is_ready}")
    
    # 測試詳細狀態檢測
    logger.info("3. 測試詳細狀態檢測...")
    status = image_recognition.check_copilot_response_status()
    logger.info(f"詳細狀態:")
    logger.info(f"  - 有 stop 按鈕: {status['has_stop_button']}")
    logger.info(f"  - 有 send 按鈕: {status['has_send_button']}")
    logger.info(f"  - 正在回應: {status['is_responding']}")
    logger.info(f"  - 回應準備就緒: {status['is_ready']}")
    logger.info(f"  - 狀態訊息: {status['status_message']}")
    
    logger.info("4. 測試完成！")
    logger.info("如果看到圖像檢測錯誤，請確保:")
    logger.info("  - VS Code 已經開啟")
    logger.info("  - Copilot Chat 面板可見")
    logger.info("  - stop_button.png 和 send_button.png 圖像正確")

if __name__ == "__main__":
    test_new_detection()