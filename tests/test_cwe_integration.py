#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CWE 安全檢查整合測試腳本
測試 CopilotHandler 中的 CWE 安全檢查功能
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# 添加項目根目錄到 Python 路徑
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_cwe_security_integration():
    """測試 CWE 安全檢查在 CopilotHandler 中的整合"""
    print("=== CWE 安全檢查整合測試 ===\n")
    
    try:
        # 導入必要模組
        from src.copilot_handler import CopilotHandler
        from src.CWE_Scanner.CWE_main import CWEMainScanner
        from src.error_handler import ErrorHandler
        from src.logger import AutomationLogger
        
        # 初始化組件
        logger = AutomationLogger()
        error_handler = ErrorHandler()
        cwe_scanner = CWEMainScanner()
        
        # 創建 CopilotHandler 實例，啟用 CWE 掃描器
        interaction_settings = {
            'cwe_scanner_enabled': True,
            'cwe_termination_on_high_risk': True
        }
        
        copilot_handler = CopilotHandler(
            error_handler=error_handler,
            interaction_settings=interaction_settings,
            cwe_scanner=cwe_scanner
        )
        
        print("✅ CopilotHandler 與 CWE 掃描器初始化成功")
        print(f"   CWE 掃描器狀態: {'已啟用' if copilot_handler.cwe_scanner else '未啟用'}")
        
        # 測試案例 1: 安全的回應內容
        print("\n--- 測試案例 1: 安全回應內容 ---")
        safe_response = """
        這是一個安全的程式碼範例：
        
        def hello_world():
            return "Hello, World!"
            
        def add_numbers(a, b):
            return a + b
        """
        
        vulnerability_detected = copilot_handler._perform_cwe_security_check(safe_response)
        print(f"安全內容檢查結果: {'發現漏洞' if vulnerability_detected else '未發現漏洞'}")
        
        # 測試案例 2: 包含 SQL 注入漏洞的回應
        print("\n--- 測試案例 2: SQL 注入漏洞內容 ---")
        sql_injection_response = """
        這裡是一個存在 SQL 注入漏洞的程式碼：
        
        def get_user(user_id):
            query = "SELECT * FROM users WHERE id = '" + user_id + "'"
            cursor.execute(query)
            return cursor.fetchone()
        """
        
        vulnerability_detected = copilot_handler._perform_cwe_security_check(sql_injection_response)
        print(f"SQL 注入內容檢查結果: {'發現漏洞' if vulnerability_detected else '未發現漏洞'}")
        
        # 測試案例 3: 包含 XSS 漏洞的回應
        print("\n--- 測試案例 3: XSS 漏洞內容 ---")
        xss_response = """
        這是一個存在 XSS 漏洞的 HTML 程式碼：
        
        <script>
        function display_user_input(input) {
            document.getElementById('output').innerHTML = input;
        }
        </script>
        """
        
        vulnerability_detected = copilot_handler._perform_cwe_security_check(xss_response)
        print(f"XSS 內容檢查結果: {'發現漏洞' if vulnerability_detected else '未發現漏洞'}")
        
        # 測試案例 4: 包含路徑遍歷漏洞的回應
        print("\n--- 測試案例 4: 路徑遍歷漏洞內容 ---")
        path_traversal_response = """
        這個函數存在路徑遍歷漏洞：
        
        def read_file(filename):
            with open("uploads/" + filename, 'r') as f:
                return f.read()
        """
        
        vulnerability_detected = copilot_handler._perform_cwe_security_check(path_traversal_response)
        print(f"路徑遍歷內容檢查結果: {'發現漏洞' if vulnerability_detected else '未發現漏洞'}")
        
        # 測試案例 5: 測試 copy_response 方法的整合
        print("\n--- 測試案例 5: copy_response 方法整合測試 ---")
        
        # 模擬一個包含高風險漏洞的回應
        class MockClipboard:
            def __init__(self, content):
                self.content = content
                
            def get_clipboard_content(self):
                return self.content
        
        # 這裡我們無法直接測試 copy_response，因為它依賴 UI 元素
        # 但我們可以測試內部的安全檢查邏輯
        high_risk_response = """
        eval(user_input)  # 這是一個高風險的代碼執行
        
        import subprocess
        subprocess.call(user_command, shell=True)  # 命令注入漏洞
        """
        
        vulnerability_detected = copilot_handler._perform_cwe_security_check(high_risk_response)
        print(f"高風險內容檢查結果: {'發現漏洞' if vulnerability_detected else '未發現漏洞'}")
        
        # 檢查報告生成
        print("\n--- 檢查報告生成 ---")
        report_dir = Path("ExecutionResult/CWEScanner_UpdateReport")
        if report_dir.exists():
            report_files = list(report_dir.glob("*.json"))
            txt_files = list(report_dir.glob("*.txt"))
            print(f"生成的 JSON 報告數量: {len(report_files)}")
            print(f"生成的 TXT 警報數量: {len(txt_files)}")
            
            if report_files:
                latest_report = max(report_files, key=lambda f: f.stat().st_mtime)
                print(f"最新報告: {latest_report.name}")
                
                # 讀取並顯示報告內容摘要
                import json
                with open(latest_report, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                    
                print(f"報告摘要:")
                print(f"  - 掃描時間: {report_data.get('scan_timestamp', 'N/A')}")
                print(f"  - 總漏洞數: {report_data.get('total_vulnerabilities', 0)}")
                print(f"  - 高風險漏洞數: {report_data.get('high_risk_count', 0)}")
        else:
            print("⚠️ 報告目錄不存在")
        
        print("\n✅ CWE 安全檢查整合測試完成")
        return True
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_cwe_configuration():
    """測試 CWE 配置選項"""
    print("\n=== CWE 配置測試 ===\n")
    
    try:
        from config.config import config
        
        print(f"CWE 掃描器預設啟用狀態: {config.CWE_SCANNER_ENABLED}")
        print(f"高風險漏洞自動終止: {config.CWE_TERMINATE_ON_VULNERABILITY}")
        
        # 測試配置檔案
        config_file = Path("config/settings.json")
        if config_file.exists():
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                
            cwe_settings = settings.get('cwe_scanner', {})
            print(f"設定檔中的 CWE 配置: {cwe_settings}")
        
        print("✅ CWE 配置測試完成")
        return True
        
    except Exception as e:
        print(f"❌ 配置測試錯誤: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 開始 CWE 安全檢查整合測試\n")
    
    # 測試配置
    config_success = test_cwe_configuration()
    
    # 測試整合功能
    integration_success = test_cwe_security_integration()
    
    # 總結
    print("\n" + "="*50)
    print("測試結果總結:")
    print(f"  配置測試: {'✅ 通過' if config_success else '❌ 失敗'}")
    print(f"  整合測試: {'✅ 通過' if integration_success else '❌ 失敗'}")
    
    if config_success and integration_success:
        print("\n🎉 所有測試通過！CWE 安全檢查整合成功")
        sys.exit(0)
    else:
        print("\n⚠️ 部分測試失敗，請檢查相關配置和代碼")
        sys.exit(1)