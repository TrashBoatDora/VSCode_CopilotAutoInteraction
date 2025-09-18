#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copilot Chat 多輪互動設定工具
獨立的設定程式，讓使用者配置多輪互動功能
"""

import sys
from pathlib import Path

# 設定模組搜尋路徑
sys.path.append(str(Path(__file__).parent))

from src.interaction_settings_ui import show_interaction_settings

if __name__ == "__main__":
    print("=== Copilot Chat 多輪互動設定 ===")
    print("啟動設定介面...")
    
    try:
        settings = show_interaction_settings()
        print("\n設定完成！")
        print(f"最終設定: {settings}")
    except Exception as e:
        print(f"設定過程中發生錯誤: {e}")
        input("按 Enter 鍵結束...")
    
    print("設定程式結束。")