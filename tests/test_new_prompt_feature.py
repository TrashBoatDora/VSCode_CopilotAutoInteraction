# -*- coding: utf-8 -*-
"""
測試新的多輪 prompt 功能
"""

import sys
import os
from pathlib import Path

# 設定模組搜尋路徑
sys.path.append(os.getcwd())

from config.config import config
from src.copilot_handler import CopilotHandler

def test_new_prompt_functionality():
    """測試新的 prompt 功能"""
    print("=== 測試新的多輪 prompt 功能 ===\n")
    
    # 1. 測試配置
    print("1. 測試配置功能:")
    print(f"   PROMPTS_DIR: {config.PROMPTS_DIR}")
    print(f"   PROMPT1_FILE_PATH: {config.PROMPT1_FILE_PATH}")
    print(f"   PROMPT2_FILE_PATH: {config.PROMPT2_FILE_PATH}")
    
    # 驗證檔案存在
    prompt1_exists, prompt2_exists = config.validate_prompt_files()
    print(f"   prompt1.txt 存在: {prompt1_exists}")
    print(f"   prompt2.txt 存在: {prompt2_exists}")
    
    # 2. 測試 CopilotHandler
    print("\n2. 測試 CopilotHandler 功能:")
    handler = CopilotHandler()
    
    # 測試各輪次的 prompt 讀取
    for round_num in [1, 2, 3]:
        prompt = handler._load_prompt_from_file(round_num)
        if prompt:
            print(f"   第 {round_num} 輪 prompt (長度: {len(prompt)} 字元): {prompt[:50]}...")
        else:
            print(f"   第 {round_num} 輪 prompt: 讀取失敗")
    
    # 3. 測試輪數對應關係
    print("\n3. 測試輪數對應關係:")
    for round_num in [1, 2, 3, 4, 5]:
        expected_file = config.get_prompt_file_path(round_num)
        print(f"   第 {round_num} 輪 -> {expected_file.name}")
    
    print("\n=== 測試完成 ===")
    return True

if __name__ == "__main__":
    test_new_prompt_functionality()