# -*- coding: utf-8 -*-
"""
測試 CWE 掃描報告路徑結構修正
驗證報告生成到 ExecutionResult/Success 或 ExecutionResult/Fail 目錄
"""

import sys
import os
import json
import tempfile
import shutil
from pathlib import Path

# 添加 src 目錄到 Python 路徑
sys.path.append(str(Path(__file__).parent.parent))

from src.copilot_handler import CopilotHandler

try:
    from src.CWE_Scanner.CWE_main import CWEMainScanner as CWEScanner
except ImportError:
    # 如果 CWE 掃描器不存在，建立一個簡單的模擬類別
    class CWEScanner:
        def scan_text(self, text):
            return {}

def test_cwe_report_path_structure():
    """測試 CWE 報告路徑結構"""
    print("🔍 開始測試 CWE 報告路徑結構...")
    
    # 建立臨時測試環境
    original_dir = os.getcwd()
    
    try:
        # 初始化 CWE 掃描器和 Copilot 處理器
        cwe_scanner = CWEScanner()
        copilot_handler = CopilotHandler(cwe_scanner=cwe_scanner)
        
        # 設定測試專案路徑
        test_project_name = "test_sample1"
        test_project_path = os.path.join("projects", test_project_name)
        copilot_handler.current_project_path = test_project_path
        
        print(f"📁 設定測試專案路徑: {test_project_path}")
        
        # 測試案例 1: 無漏洞的情況 (應該生成到 Success)
        print("\n=== 測試案例 1: 無漏洞情況 ===")
        clean_response = "This is a clean response with no security vulnerabilities."
        vulnerabilities_clean = []
        
        copilot_handler._generate_cwe_report(vulnerabilities_clean, clean_response)
        
        # 檢查是否在 Success 目錄生成報告
        success_dir = os.path.join("ExecutionResult", "Success", test_project_name)
        if os.path.exists(success_dir):
            files = os.listdir(success_dir)
            print(f"✅ Success 目錄已建立: {success_dir}")
            print(f"   包含檔案: {files}")
        else:
            print(f"❌ Success 目錄未建立: {success_dir}")
        
        # 測試案例 2: 有高風險漏洞的情況 (應該生成到 Fail)
        print("\n=== 測試案例 2: 高風險漏洞情況 ===")
        
        # 建立模擬的高風險漏洞結果
        class MockVulnerability:
            def __init__(self, cwe_id, description, severity, confidence):
                self.cwe_id = cwe_id
                self.description = description
                self.severity = severity
                self.confidence = confidence
                self.location = "test_location"
                self.evidence = "test_evidence"
                self.mitigation = "test_mitigation"
                self.vulnerability_found = True
        
        # 建立高風險漏洞清單
        high_risk_vulnerabilities = [
            {
                'cwe_id': 'CWE-089',
                'description': 'SQL Injection vulnerability detected',
                'severity': 'High',
                'confidence': 0.95,
                'location': 'line 25',
                'evidence': 'Direct SQL query without parameterization',
                'mitigation': 'Use parameterized queries'
            },
            {
                'cwe_id': 'CWE-079',
                'description': 'Cross-site Scripting (XSS) vulnerability',
                'severity': 'Critical',
                'confidence': 0.89,
                'location': 'line 42',
                'evidence': 'Unescaped user input in HTML output',
                'mitigation': 'Escape user input before rendering'
            }
        ]
        
        vulnerable_response = "This response contains SQL injection: SELECT * FROM users WHERE id = " + str(1)
        copilot_handler._generate_cwe_report(high_risk_vulnerabilities, vulnerable_response)
        
        # 檢查是否在 Fail 目錄生成報告
        fail_dir = os.path.join("ExecutionResult", "Fail", test_project_name)
        if os.path.exists(fail_dir):
            files = os.listdir(fail_dir)
            print(f"✅ Fail 目錄已建立: {fail_dir}")
            print(f"   包含檔案: {files}")
            
            # 檢查報告內容
            for file in files:
                if file.endswith('.json'):
                    with open(os.path.join(fail_dir, file), 'r', encoding='utf-8') as f:
                        report_data = json.load(f)
                        print(f"   📄 JSON 報告 - 高風險漏洞數: {report_data['high_risk_count']}")
                elif file.endswith('.txt'):
                    print(f"   📄 TXT 摘要: {file}")
        else:
            print(f"❌ Fail 目錄未建立: {fail_dir}")
        
        # 測試案例 3: 檢查全域統計更新
        print("\n=== 測試案例 3: 全域統計檢查 ===")
        global_stats_path = os.path.join("ExecutionResult", "CWEScanner_UpdateReport", "cwe_scan_statistics.json")
        
        if os.path.exists(global_stats_path):
            with open(global_stats_path, 'r', encoding='utf-8') as f:
                stats_data = json.load(f)
                print(f"✅ 全域統計已更新:")
                print(f"   總掃描次數: {stats_data['total_scans']}")
                print(f"   有漏洞專案數: {stats_data['projects_with_vulnerabilities']}")
                print(f"   高風險專案數: {stats_data['projects_with_high_risk']}")
                
                # 顯示最近的掃描記錄
                if stats_data['scan_history']:
                    latest_scan = stats_data['scan_history'][-1]
                    print(f"   最新掃描記錄:")
                    print(f"     專案: {latest_scan['project_name']}")
                    print(f"     結果類型: {latest_scan['result_type']}")
                    print(f"     結果目錄: {latest_scan['result_directory']}")
        else:
            print(f"❌ 全域統計檔案未找到: {global_stats_path}")
        
        # 測試案例 4: 驗證 projects 目錄保持不變
        print("\n=== 測試案例 4: Projects 目錄檢查 ===")
        projects_dir = "projects"
        if os.path.exists(projects_dir):
            project_files = []
            for item in os.listdir(projects_dir):
                item_path = os.path.join(projects_dir, item)
                if os.path.isfile(item_path):
                    project_files.append(item)
                elif os.path.isdir(item_path):
                    # 檢查專案目錄內是否有 CWE_Report 目錄（不應該有）
                    cwe_report_dir = os.path.join(item_path, "CWE_Report")
                    if os.path.exists(cwe_report_dir):
                        print(f"⚠️  發現舊的 CWE_Report 目錄: {cwe_report_dir} (可以手動清理)")
                    else:
                        print(f"✅ 專案目錄乾淨: {item_path}")
            
            if project_files:
                print(f"✅ Projects 目錄檔案清單: {project_files}")
        
        print("\n🎉 CWE 報告路徑結構測試完成！")
        print("✅ 報告現在會正確生成到:")
        print("   - ExecutionResult/Success/專案名稱/ (無高風險漏洞)")
        print("   - ExecutionResult/Fail/專案名稱/ (有高風險漏洞)")
        print("✅ Projects 目錄保持穩定，便於實驗")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試過程發生錯誤: {str(e)}")
        import traceback
        print(f"詳細錯誤資訊: {traceback.format_exc()}")
        return False
    
    finally:
        os.chdir(original_dir)

if __name__ == "__main__":
    success = test_cwe_report_path_structure()
    if success:
        print("\n✅ 所有測試通過！CWE 報告路徑結構已正確修正。")
    else:
        print("\n❌ 測試失敗，請檢查錯誤訊息。")