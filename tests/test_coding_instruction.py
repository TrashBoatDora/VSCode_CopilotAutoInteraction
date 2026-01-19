#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 Coding Instruction 功能的解析和模板套用
"""

import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
sys.path.append(str(Path(__file__).parent.parent))

from src.copilot_handler import CopilotHandler
from src.logger import get_logger

def test_parse_prompt_line():
    """測試 prompt 行解析功能（純路徑格式）"""
    print("=" * 60)
    print("測試 1: Prompt 行解析功能（純路徑格式）")
    print("=" * 60)
    
    handler = CopilotHandler()
    
    test_cases = [
        ("src/crypto/encryption.py", "src/crypto/encryption.py"),
        ("src/auth/login.py", "src/auth/login.py"),
        ("utils/helper.py", "utils/helper.py"),
        ("  path/with/spaces.py  ", "path/with/spaces.py"),  # 測試 strip
        ("", ""),  # 空字串
    ]
    
    for i, (input_str, expected) in enumerate(test_cases, 1):
        print(f"\n測試案例 {i}:")
        print(f"  輸入: {input_str!r}")
        
        result = handler._parse_prompt_line(input_str)
        
        print(f"  預期: {expected!r}")
        print(f"  結果: {result!r}")
        print(f"  狀態: {'✅ 通過' if result == expected else '❌ 失敗'}")

def test_apply_template():
    """測試模板套用功能"""
    print("\n" + "=" * 60)
    print("測試 2: 模板套用功能")
    print("=" * 60)
    
    handler = CopilotHandler()
    
    test_cases = [
        "src/crypto/encryption.py",
        "src/auth/login.py",
        "utils/helper.py",
    ]
    
    for i, filepath in enumerate(test_cases, 1):
        print(f"\n測試案例 {i}:")
        print(f"  檔案路徑: {filepath}")
        
        result = handler._apply_coding_instruction_template(filepath)
        
        if result:
            print(f"  套用結果:")
            print(f"  ---")
            print(f"  {result[:200]}..." if len(result) > 200 else f"  {result}")
            print(f"  ---")
            print(f"  狀態: ✅ 成功")
        else:
            print(f"  狀態: ❌ 失敗")

def test_end_to_end():
    """測試端對端流程"""
    print("\n" + "=" * 60)
    print("測試 3: 端對端流程")
    print("=" * 60)
    
    handler = CopilotHandler()
    
    prompt_line = "src/crypto/encryption.py"
    
    print(f"\n原始 Prompt 行: {prompt_line}")
    
    # 步驟 1: 解析
    filepath = handler._parse_prompt_line(prompt_line)
    print(f"\n步驟 1 - 解析結果:")
    print(f"  檔案路徑: {filepath}")
    
    # 步驟 2: 套用模板
    if filepath:
        processed_prompt = handler._apply_coding_instruction_template(filepath)
        
        print(f"\n步驟 2 - 套用模板後:")
        print(f"  ---")
        print(f"  {processed_prompt}")
        print(f"  ---")
        
        print(f"\n✅ 端對端測試完成")
    else:
        print(f"\n❌ 解析失敗，無法繼續")

def main():
    """主測試函數"""
    logger = get_logger("CodingInstructionTest")
    logger.info("開始測試 Coding Instruction 功能")
    
    try:
        test_parse_prompt_line()
        test_apply_template()
        test_end_to_end()
        
        print("\n" + "=" * 60)
        print("所有測試完成！")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"測試過程中發生錯誤: {e}")
        raise

if __name__ == "__main__":
    main()
