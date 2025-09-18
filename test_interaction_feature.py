#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試多輪互動新功能
"""

import sys
import json
from pathlib import Path

# 設定模組搜尋路徑
sys.path.append(str(Path(__file__).parent))

from config.config import config

def test_interaction_settings():
    """測試互動設定功能"""
    print("=== 測試多輪互動設定功能 ===\n")
    
    # 測試載入設定
    print("1. 測試載入預設設定...")
    settings_file = config.PROJECT_ROOT / "config" / "interaction_settings.json"
    
    if settings_file.exists():
        print(f"   設定檔案存在: {settings_file}")
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        print(f"   當前設定: {settings}")
    else:
        print(f"   設定檔案不存在: {settings_file}")
        print("   將使用預設設定")
    
    # 測試 copilot_handler 載入設定
    print("\n2. 測試 CopilotHandler 載入設定...")
    try:
        from src.copilot_handler import CopilotHandler
        from src.error_handler import ErrorHandler
        
        error_handler = ErrorHandler()
        copilot_handler = CopilotHandler(error_handler)
        
        # 測試載入設定方法
        interaction_settings = copilot_handler._load_interaction_settings()
        print(f"   載入的設定: {interaction_settings}")
        
        # 測試設定應用
        if interaction_settings["include_previous_response"]:
            print("   ✅ 回應串接功能：啟用")
        else:
            print("   ❌ 回應串接功能：停用")
            
        print(f"   最大輪數: {interaction_settings['max_rounds']}")
        print(f"   輪次間隔: {interaction_settings['round_delay']} 秒")
        
    except Exception as e:
        print(f"   ❌ 測試失敗: {e}")
    
    print("\n3. 測試配置參數...")
    print(f"   預設回應串接前綴: {config.INTERACTION_RESPONSE_CHAINING_PREFIX.strip()}")
    print(f"   預設回應串接後綴: {config.INTERACTION_RESPONSE_CHAINING_SUFFIX.strip()}")
    
    print("\n測試完成！")

def create_test_settings():
    """創建測試用的設定檔案"""
    print("\n=== 創建測試設定 ===")
    
    test_settings = {
        "interaction_enabled": True,
        "max_rounds": 2,
        "include_previous_response": False,  # 測試停用回應串接
        "round_delay": 3
    }
    
    settings_file = config.PROJECT_ROOT / "config" / "interaction_settings.json"
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(settings_file, 'w', encoding='utf-8') as f:
        json.dump(test_settings, f, indent=2, ensure_ascii=False)
    
    print(f"已創建測試設定檔案: {settings_file}")
    print(f"測試設定內容: {test_settings}")

if __name__ == "__main__":
    print("多輪互動新功能測試\n")
    
    choice = input("選擇測試項目:\n1. 測試設定載入功能\n2. 創建測試設定檔案\n3. 全部測試\n請輸入選擇 (1-3): ")
    
    if choice == "1":
        test_interaction_settings()
    elif choice == "2":
        create_test_settings()
    elif choice == "3":
        create_test_settings()
        test_interaction_settings()
    else:
        print("無效選擇")
    
    input("\n按 Enter 鍵結束...")