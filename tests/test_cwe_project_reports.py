#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CWE 報告生成位置測試腳本
測試新的報告生成功能：專案內詳細報告 + 全域高風險警報
"""

import sys
import os
import shutil
import tempfile
from pathlib import Path

# 添加項目根目錄到 Python 路徑
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def create_test_project(project_name: str = "test_cwe_project"):
    """創建測試專案目錄"""
    test_project_path = Path("ExecutionResult") / "Success" / project_name
    test_project_path.mkdir(parents=True, exist_ok=True)
    return str(test_project_path)

def test_project_report_generation():
    """測試專案報告生成功能"""
    print("=== CWE 專案報告生成測試 ===\n")
    
    try:
        from src.copilot_handler import CopilotHandler
        from src.CWE_Scanner.CWE_main import CWEMainScanner
        from src.error_handler import ErrorHandler
        
        # 創建測試專案
        test_project1 = create_test_project("sample_project")
        test_project2 = create_test_project("sample_project2")
        
        print(f"創建測試專案: {test_project1}")
        print(f"創建測試專案: {test_project2}")
        
        # 初始化組件
        error_handler = ErrorHandler()
        cwe_scanner = CWEMainScanner()
        
        interaction_settings = {
            'cwe_scanner_enabled': True,
            'cwe_termination_on_high_risk': True
        }
        
        copilot_handler = CopilotHandler(
            error_handler=error_handler,
            interaction_settings=interaction_settings,
            cwe_scanner=cwe_scanner
        )
        
        # 測試案例 1: 專案1 - 包含高風險漏洞
        print(f"\n--- 測試專案1: {Path(test_project1).name} ---")
        copilot_handler.current_project_path = test_project1
        
        high_risk_response = """
        def unsafe_function(user_input):
            eval(user_input)  # Critical 風險
            return "processed"
        """
        
        vulnerability_detected = copilot_handler._perform_cwe_security_check(high_risk_response)
        print(f"專案1 漏洞檢測結果: {'檢測到高風險' if vulnerability_detected else '未檢測到高風險'}")
        
        # 檢查專案1的報告
        project1_report_dir = Path(test_project1) / "CWE_Report"
        if project1_report_dir.exists():
            json_files = list(project1_report_dir.glob("*.json"))
            txt_files = list(project1_report_dir.glob("*.txt"))
            print(f"專案1 報告目錄: {project1_report_dir}")
            print(f"  - JSON 報告數量: {len(json_files)}")
            print(f"  - TXT 摘要數量: {len(txt_files)}")
        
        # 測試案例 2: 專案2 - 安全代碼（低風險）
        print(f"\n--- 測試專案2: {Path(test_project2).name} ---")
        copilot_handler.current_project_path = test_project2
        
        safe_response = """
        def safe_function(user_input):
            # 安全的輸入處理
            if isinstance(user_input, str) and len(user_input) < 100:
                return f"Hello, {user_input}!"
            return "Invalid input"
        """
        
        vulnerability_detected = copilot_handler._perform_cwe_security_check(safe_response)
        print(f"專案2 漏洞檢測結果: {'檢測到高風險' if vulnerability_detected else '未檢測到高風險'}")
        
        # 檢查專案2的報告
        project2_report_dir = Path(test_project2) / "CWE_Report"
        if project2_report_dir.exists():
            json_files = list(project2_report_dir.glob("*.json"))
            txt_files = list(project2_report_dir.glob("*.txt"))
            print(f"專案2 報告目錄: {project2_report_dir}")
            print(f"  - JSON 報告數量: {len(json_files)}")
            print(f"  - TXT 摘要數量: {len(txt_files)}")
        
        # 檢查全域報告目錄
        print(f"\n--- 檢查全域報告目錄 ---")
        global_report_dir = Path("ExecutionResult/CWEScanner_UpdateReport")
        if global_report_dir.exists():
            global_alerts = list(global_report_dir.glob("cwe_high_risk_alert_*.txt"))
            global_stats = global_report_dir / "cwe_scan_statistics.json"
            
            print(f"全域報告目錄: {global_report_dir}")
            print(f"  - 高風險警報數量: {len(global_alerts)}")
            print(f"  - 統計檔案存在: {global_stats.exists()}")
            
            # 顯示最新的高風險警報內容
            if global_alerts:
                latest_alert = max(global_alerts, key=lambda f: f.stat().st_mtime)
                print(f"  - 最新警報檔案: {latest_alert.name}")
                
                with open(latest_alert, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')[:10]  # 只顯示前10行
                    print("  - 警報內容預覽:")
                    for line in lines:
                        if line.strip():
                            print(f"    {line}")
            
            # 顯示統計資料
            if global_stats.exists():
                import json
                with open(global_stats, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
                    
                print(f"  - 掃描統計:")
                print(f"    總掃描次數: {stats.get('total_scans', 0)}")
                print(f"    有漏洞的專案: {stats.get('projects_with_vulnerabilities', 0)}")
                print(f"    高風險專案: {stats.get('projects_with_high_risk', 0)}")
                
                recent_scans = stats.get('scan_history', [])[-3:]  # 顯示最近3次掃描
                print(f"    最近掃描記錄:")
                for scan in recent_scans:
                    print(f"      - {scan.get('project_name', 'Unknown')}: {scan.get('high_risk_count', 0)} 高風險")
        
        print("\n✅ CWE 報告生成位置測試完成")
        return True
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def verify_directory_structure():
    """驗證目錄結構是否正確生成"""
    print("\n=== 驗證目錄結構 ===")
    
    expected_dirs = [
        "ExecutionResult/Success/sample_project/CWE_Report",
        "ExecutionResult/Success/sample_project2/CWE_Report",
        "ExecutionResult/CWEScanner_UpdateReport"
    ]
    
    for dir_path in expected_dirs:
        path = Path(dir_path)
        status = "✅ 存在" if path.exists() else "❌ 不存在"
        print(f"{status}: {dir_path}")
        
        if path.exists():
            files = list(path.glob("*"))
            print(f"    檔案數量: {len(files)}")
            for file in files[:3]:  # 只顯示前3個檔案
                print(f"    - {file.name}")

if __name__ == "__main__":
    print("🔍 開始 CWE 報告生成位置測試\n")
    
    # 執行測試
    success = test_project_report_generation()
    
    # 驗證目錄結構
    verify_directory_structure()
    
    # 總結
    print("\n" + "="*50)
    if success:
        print("✅ CWE 報告生成位置測試通過")
        print("\n📂 新的報告結構:")
        print("   📁 ExecutionResult/Success/[專案名]/CWE_Report/")
        print("      ├── cwe_scan_result_*.json     (詳細掃描報告)")
        print("      └── cwe_summary_*.txt          (漏洞摘要)")
        print("   📁 ExecutionResult/CWEScanner_UpdateReport/")
        print("      ├── cwe_high_risk_alert_*.txt  (高風險警報)")
        print("      └── cwe_scan_statistics.json   (全域統計)")
    else:
        print("❌ CWE 報告生成位置測試失敗")
    
    sys.exit(0 if success else 1)