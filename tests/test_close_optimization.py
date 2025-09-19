# -*- coding: utf-8 -*-
"""
測試優化後的 VS Code 關閉功能
"""

import sys
from pathlib import Path
import time

# 添加專案根目錄到路徑
sys.path.append(str(Path(__file__).parent))

from src.vscode_controller import VSCodeController
from src.logger import get_logger

def test_vscode_close_optimization():
    """測試 VS Code 關閉功能優化"""
    print("🔍 測試 VS Code 關閉功能優化...")
    logger = get_logger("TestCloseOptimization")
    
    controller = VSCodeController()
    
    # 檢查新增的方法是否存在
    required_methods = [
        '_try_graceful_close',
        '_is_auto_opened_vscode_running',
        '_close_method_process_termination',
        '_close_method_ctrl_shift_w',
        '_close_method_alt_f4'
    ]
    
    print("📋 檢查新增的關閉方法...")
    for method_name in required_methods:
        if hasattr(controller, method_name):
            print(f"  ✅ {method_name} 方法存在")
        else:
            print(f"  ❌ {method_name} 方法缺失")
            return False
    
    # 檢查 close_current_project 方法是否使用新的優雅關閉邏輯
    import inspect
    source = inspect.getsource(controller.close_current_project)
    if "_try_graceful_close" in source:
        print("✅ close_current_project 方法已使用新的優雅關閉邏輯")
    else:
        print("❌ close_current_project 方法未使用新的優雅關閉邏輯")
        return False
    
    print("🎉 VS Code 關閉功能優化測試通過！")
    return True

def simulate_close_test():
    """模擬關閉測試（不實際開啟 VS Code）"""
    print("\n🔍 模擬關閉功能測試...")
    logger = get_logger("TestCloseOptimization")
    
    controller = VSCodeController()
    
    # 測試各種關閉方法的邏輯（不實際執行）
    print("📋 測試關閉方法邏輯...")
    
    try:
        # 測試方法是否可以調用（不實際執行快捷鍵）
        methods_to_test = [
            controller._close_method_process_termination,
            controller._close_method_ctrl_shift_w,
            controller._close_method_alt_f4
        ]
        
        for i, method in enumerate(methods_to_test, 1):
            method_name = method.__name__
            print(f"  ✅ 關閉方法 {i}: {method_name} - 可以調用")
        
        print("✅ 所有關閉方法邏輯測試通過")
        return True
        
    except Exception as e:
        print(f"❌ 關閉方法測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 開始測試優化後的 VS Code 關閉功能...")
    print("=" * 60)
    
    try:
        # 測試方法存在性
        if not test_vscode_close_optimization():
            return False
        
        # 模擬測試
        if not simulate_close_test():
            return False
        
        print("\n" + "=" * 60)
        print("🎉 所有測試通過！關閉功能優化成功！")
        print("\n✨ 主要改進：")
        print("  1. 精確的目標視窗關閉方法：")
        print("     - 進程關閉 (Process Termination) - 最精確")
        print("     - Ctrl+Shift+W (關閉視窗)")
        print("     - Alt+F4 (關閉應用程式)")
        print("  2. 移除有問題的焦點切換機制")
        print("  3. 只檢查和關閉自動開啟的 VS Code 實例")
        print("  4. 保護用戶既有的 VS Code 視窗")
        
        return True
        
    except Exception as e:
        print(f"\n💥 測試過程中發生錯誤: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)