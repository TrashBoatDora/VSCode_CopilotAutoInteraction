import json
import shutil
from pathlib import Path
import os

status_file = Path('projects/automation_status.json')
script_root = Path(__file__).parent  # 腳本根目錄
execution_result_dir = script_root / "ExecutionResult"

# 刪除舊的 automation_report 文件
projects_dir = Path('projects')
if projects_dir.exists():
    for file in projects_dir.glob("automation_report_*.json"):
        try:
            file.unlink()
            print(f"已刪除舊的報告文件: {file}")
        except Exception as e:
            print(f"刪除 {file} 失敗: {e}")

if status_file.exists():
    with open(status_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 重設所有專案為 pending
    for project in data['projects']:
        project['status'] = 'pending'
        project['retry_count'] = 0
        project['error_message'] = None
        project['last_processed'] = None
        
        # 清理專案目錄中的舊檔案（向後相容）
        proj_path = Path(project['path'])
        for fname in ["Copilot_AutoComplete.txt", "Copilot_AutoComplete.md", "Copilot_AutoComplete.report", "automation_log.txt"]:
            fpath = proj_path / fname
            if fpath.exists():
                try:
                    fpath.unlink()
                    print(f"已刪除 {fpath}")
                except Exception as e:
                    print(f"刪除 {fpath} 失敗: {e}")
        
        # 刪除專案內的舊 ExecutionResult 資料夾（向後相容）
        old_execution_result = proj_path / "ExecutionResult"
        if old_execution_result.exists():
            try:
                shutil.rmtree(old_execution_result)
                print(f"已刪除 {old_execution_result}")
            except Exception as e:
                print(f"刪除 {old_execution_result} 失敗: {e}")
    
    # 刪除統一的 ExecutionResult 資料夾
    if execution_result_dir.exists():
        try:
            shutil.rmtree(execution_result_dir)
            print(f"已刪除統一的 ExecutionResult 資料夾: {execution_result_dir}")
        except Exception as e:
            print(f"刪除 {execution_result_dir} 失敗: {e}")
    
    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print('✅ 所有專案狀態已重設為 pending，並清除統一的 ExecutionResult 資料夾')
else:
    print('❌ 狀態檔案不存在')
