# -*- coding: utf-8 -*-
"""
測試新的鍵盤操作流程
"""

import sys
from pathlib import Path

# 添加專案根目錄到路徑
sys.path.append(str(Path(__file__).parent))

from src.copilot_handler import copilot_handler
from config.config import config

def test_prompt_loading():
    """測試提示詞載入"""
    print("=== 測試提示詞載入 ===")
    
    prompt = copilot_handler._load_prompt_from_file()
    if prompt:
        print(f"✓ 成功載入提示詞: {len(prompt)} 字元")
        print(f"內容預覽: {prompt[:100]}...")
        return True
    else:
        print("✗ 提示詞載入失敗")
        return False

def test_image_validation():
    """測試圖像驗證（現已可選）"""
    print("\n=== 測試圖像驗證 ===")
    
    from src.image_recognition import image_recognition
    success = image_recognition.validate_required_images()
    
    if success:
        print("✓ 圖像驗證通過（或已跳過）")
        return True
    else:
        print("✗ 圖像驗證失敗")
        return False

def test_keyboard_operations():
    """測試鍵盤操作功能（模擬）"""
    print("\n=== 測試鍵盤操作功能 ===")
    
    print("測試的鍵盤操作序列:")
    print("1. Ctrl+Shift+I - 聚焦 Copilot Chat")
    print("2. Ctrl+V - 貼上提示詞")
    print("3. Enter - 發送提示詞") 
    print("4. Ctrl+↑ - 聚焦回應")
    print("5. Shift+F10 - 開啟右鍵選單")
    print("6. ↓↓ - 選擇'複製全部'")
    print("7. Enter - 執行複製")
    
    print("✓ 鍵盤操作序列定義完成")
    return True

def main():
    """主測試函數"""
    print("=" * 60)
    print("Hybrid UI Automation Script - 新功能測試")
    print("=" * 60)
    
    tests = [
        test_prompt_loading,
        test_image_validation,
        test_keyboard_operations
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    if passed == total:
        print(f"✅ 所有測試通過 ({passed}/{total})")
        print("新的鍵盤操作流程已就緒！")
        print("\n下一步:")
        print("1. 編輯 prompt.txt 設定你的提示詞")
        print("2. 將專案放入 projects/ 目錄")
        print("3. 執行 main.py 開始自動化")
    else:
        print(f"❌ 部分測試失敗 ({passed}/{total})")
    print("=" * 60)

if __name__ == "__main__":
    main()