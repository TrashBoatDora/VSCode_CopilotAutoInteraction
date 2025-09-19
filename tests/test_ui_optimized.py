# -*- coding: utf-8 -*-
"""
UI介面優化測試腳本
測試調整後的介面尺寸和佈局
"""

import sys
import os
from pathlib import Path

# 設定模組搜尋路徑
sys.path.append(str(Path(__file__).parent.parent))

def test_optimized_ui():
    """測試優化後的UI介面"""
    try:
        print("=== UI介面優化測試 ===")
        print("正在啟動優化後的設定介面...")
        
        # 導入介面模組
        from src.interaction_settings_ui import show_interaction_settings
        
        print("介面已啟動，請檢查以下優化項目：")
        print("1. 視窗尺寸是否適中 (650x550)")
        print("2. 是否減少了不必要的空白區域")
        print("3. 文字說明區塊是否更緊湊")
        print("4. 整體佈局是否更協調")
        print("5. 所有按鈕是否正常顯示並可操作")
        
        # 顯示設定介面
        settings = show_interaction_settings()
        
        if settings is None:
            print("\n✓ 取消功能正常")
        else:
            print("\n✓ 設定保存功能正常")
            print("最終設定:")
            for key, value in settings.items():
                print(f"  {key}: {value}")
        
        print("\n=== UI優化測試完成 ===")
        
    except Exception as e:
        print(f"測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_optimized_ui()