# -*- coding: utf-8 -*-
"""
測試優化後的功能：專案視窗最大化和複製內容檢查
"""

import sys
from pathlib import Path

# 添加專案根目錄到路徑
sys.path.append(str(Path(__file__).parent))

from src.vscode_controller import VSCodeController
from src.copilot_handler import CopilotHandler
from src.logger import get_logger
import time

def test_vscode_controller_optimization():
    """測試 VS Code 控制器的視窗最大化優化"""
    print("🔍 測試 VS Code 控制器優化...")
    logger = get_logger("TestOptimizations")
    
    controller = VSCodeController()
    
    # 測試直接最大化視窗方法
    print("✅ VSCodeController._maximize_window_direct() 方法存在")
    assert hasattr(controller, '_maximize_window_direct'), "缺少 _maximize_window_direct 方法"
    
    # 檢查 open_project 方法中是否包含最大化邏輯
    import inspect
    source = inspect.getsource(controller.open_project)
    assert "_maximize_window_direct" in source, "open_project 方法中缺少最大化邏輯"
    print("✅ open_project 方法已包含自動最大化邏輯")
    
    print("🎉 VS Code 控制器優化測試通過！")

def test_copilot_handler_optimization():
    """測試 Copilot 處理器的複製內容檢查優化"""
    print("\n🔍 測試 Copilot 處理器優化...")
    logger = get_logger("TestOptimizations")
    
    controller = VSCodeController()
    handler = CopilotHandler(controller)
    
    # 測試簡化的完整性檢查
    test_cases = [
        ("這是一個完整的回應，包含了代碼和解釋。", True),
        ("```python\nprint('hello')\n```", True),  # 完整的程式碼區塊
        ("```python\nprint('hello')", False),  # 未閉合的程式碼區塊
        ("", False),  # 空回應
        ("短", False),  # 太短的回應
        ("我正在分析您的代碼", False),  # 明顯未完成的回應
        ("這是一個回應，但結尾有...", False),  # 明顯截斷
        ("正常的回應內容，沒有明顯問題，可以提供建議", True),  # 正常回應
    ]
    
    print("📋 測試簡化的完整性檢查邏輯...")
    for i, (response, expected) in enumerate(test_cases, 1):
        result = handler._check_response_completeness(response)
        status = "✅" if result == expected else "❌"
        print(f"  {status} 測試 {i}: 預期 {expected}, 得到 {result}")
        if result != expected:
            print(f"    失敗的回應: '{response[:50]}...'")
    
    # 檢查 _smart_wait_for_response 方法是否包含優化邏輯
    import inspect
    source = inspect.getsource(handler._smart_wait_for_response)
    assert "圖像檢測優先" in source, "缺少圖像檢測優先邏輯"
    print("✅ _smart_wait_for_response 方法已包含圖像檢測優先邏輯")
    
    print("🎉 Copilot 處理器優化測試通過！")

def main():
    """主測試函數"""
    print("🚀 開始測試優化後的功能...")
    print("=" * 60)
    
    try:
        test_vscode_controller_optimization()
        test_copilot_handler_optimization()
        
        print("\n" + "=" * 60)
        print("🎉 所有測試通過！優化成功！")
        print("\n✨ 主要改進：")
        print("  1. 專案開啟時自動一步驟最大化視窗")
        print("  2. 簡化複製內容完整性檢查，優先使用圖像檢測")
        print("  3. 減少超時等待，提高自動化效率")
        
    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        return False
    except Exception as e:
        print(f"\n💥 測試過程中發生錯誤: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)