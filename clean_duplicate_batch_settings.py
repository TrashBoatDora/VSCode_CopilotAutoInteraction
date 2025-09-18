# -*- coding: utf-8 -*-
"""
清理腳本 - 移除 interaction_settings_ui.py 中的重複批次設定
"""

import re
import shutil
from pathlib import Path

def clean_interaction_ui():
    """清理互動設定 UI 中的重複批次設定"""
    
    ui_file = Path("src/interaction_settings_ui.py")
    
    if not ui_file.exists():
        print("❌ 找不到 interaction_settings_ui.py 檔案")
        return False
    
    # 備份原檔案
    backup_file = ui_file.with_suffix('.py.backup')
    shutil.copy2(ui_file, backup_file)
    print(f"✅ 已備份原檔案到 {backup_file}")
    
    # 讀取檔案內容
    with open(ui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查是否有批次相關的內容
    batch_patterns = [
        r'.*每批處理專案數量.*',
        r'.*batch_size.*',
        r'.*批次.*數量.*',
        r'.*專案數量.*'
    ]
    
    found_issues = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines, 1):
        for pattern in batch_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                found_issues.append(f"第 {i} 行: {line.strip()}")
    
    if found_issues:
        print("🔍 發現以下可能的批次設定相關內容：")
        for issue in found_issues:
            print(f"  - {issue}")
        
        # 詢問是否要清理
        response = input("\n是否要移除這些內容？ (y/n): ")
        if response.lower() == 'y':
            # 移除相關行
            cleaned_lines = []
            for line in lines:
                should_keep = True
                for pattern in batch_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        should_keep = False
                        break
                if should_keep:
                    cleaned_lines.append(line)
            
            # 寫入清理後的內容
            with open(ui_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(cleaned_lines))
            
            print("✅ 已清理完成")
            return True
    else:
        print("✅ 沒有發現批次設定相關的重複內容")
        return False

if __name__ == "__main__":
    print("=== 清理 interaction_settings_ui.py 中的重複批次設定 ===")
    clean_interaction_ui()