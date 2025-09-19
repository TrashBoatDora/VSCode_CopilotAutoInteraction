# -*- coding: utf-8 -*-
"""
測試新增的 CopilotChat 修改結果處理功能 UI
"""

import sys
from pathlib import Path

# 添加專案根目錄到路徑
sys.path.append(str(Path(__file__).parent))

def test_ui():
    """測試互動設定 UI 是否包含新選項"""
    try:
        from src.interaction_settings_ui import show_interaction_settings
        
        print("開啟互動設定 UI...")
        print("請檢查是否有新的 'CopilotChat 修改結果處理' 選項")
        print("包含兩個選項：")
        print("1. 保留修改 (按 Enter)")
        print("2. 復原修改 (按右鍵 + Enter)")
        print("")
        
        settings = show_interaction_settings()
        
        if settings is None:
            print("設定已取消")
            return False
        else:
            print(f"設定完成！最終設定:")
            for key, value in settings.items():
                print(f"  {key}: {value}")
            
            # 特別檢查新增的設定
            if "copilot_chat_modification_action" in settings:
                action = settings["copilot_chat_modification_action"]
                print(f"\n✅ 新功能測試成功！CopilotChat 修改結果處理設定為: {action}")
                return True
            else:
                print("\n❌ 新功能測試失敗！找不到 copilot_chat_modification_action 設定")
                return False
        
    except Exception as e:
        print(f"測試過程中發生錯誤: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== CopilotChat 修改結果處理功能 UI 測試 ===")
    success = test_ui()
    print(f"\n測試結果: {'成功' if success else '失敗'}")