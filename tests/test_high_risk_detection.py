#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CWE 高風險漏洞檢測快速測試
"""

import sys
import os
from pathlib import Path

# 添加項目根目錄到 Python 路徑
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_high_risk_detection():
    """測試高風險漏洞檢測"""
    print("=== 高風險漏洞檢測測試 ===\n")
    
    try:
        from src.copilot_handler import CopilotHandler
        from src.CWE_Scanner.CWE_main import CWEMainScanner
        from src.error_handler import ErrorHandler
        
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
        
        # 測試高風險漏洞內容
        high_risk_response = """
        eval(user_input)  # Critical 風險
        exec(user_code)   # Critical 風險
        """
        
        print("測試包含 Critical 風險漏洞的內容...")
        vulnerability_detected = copilot_handler._perform_cwe_security_check(high_risk_response)
        print(f"高風險檢測結果: {'檢測到高風險' if vulnerability_detected else '未檢測到高風險'}")
        
        # 檢查報告
        report_dir = Path("ExecutionResult/CWEScanner_UpdateReport")
        if report_dir.exists():
            report_files = list(report_dir.glob("*.json"))
            if report_files:
                latest_report = max(report_files, key=lambda f: f.stat().st_mtime)
                
                import json
                with open(latest_report, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                    
                print(f"\n最新報告摘要:")
                print(f"  - 總漏洞數: {report_data.get('total_vulnerabilities', 0)}")
                print(f"  - 高風險漏洞數: {report_data.get('high_risk_count', 0)}")
                
                # 檢查是否有高風險警報檔案
                txt_files = list(report_dir.glob("cwe_high_risk_alert_*.txt"))
                print(f"  - 高風險警報檔案: {len(txt_files)} 個")
                
                return vulnerability_detected and report_data.get('high_risk_count', 0) > 0
        
        return False
        
    except Exception as e:
        print(f"❌ 測試出錯: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 開始高風險漏洞檢測測試\n")
    success = test_high_risk_detection()
    
    if success:
        print("\n✅ 高風險漏洞檢測測試通過")
    else:
        print("\n❌ 高風險漏洞檢測測試失敗")
    
    sys.exit(0 if success else 1)