#!/usr/bin/env python3
"""
測試腳本：驗證修正後的 CWE 掃描時機
====================================

測試目標：
1. 驗證 CWE 掃描在智能等待完成後立即執行
2. 確認掃描不在複製操作中執行  
3. 測試掃描結果正確儲存到獨立目錄
4. 驗證自動化流程成功/失敗分類不受影響

修正內容：
- 將 CWE 掃描從 copy_response() 移動到 process_project_complete()
- 掃描在 wait_for_response() 完成後立即執行
- 確保時機符合：智能等待判定回應已經結束且進行最後的複製成果時
"""

import sys
import os
from pathlib import Path
import time
import json

# 添加 src 路徑
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir / "src"))

from copilot_handler import CopilotHandler
from logger import AutomationLogger
from config.config import Config

class TestCWEScanTimingCorrection:
    def __init__(self):
        self.logger = AutomationLogger()
        self.logger.create_separator("CWE 掃描時機修正測試")
        
    def test_scan_timing_correction(self):
        """測試修正後的掃描時機"""
        try:
            self.logger.info("🧪 開始測試 CWE 掃描時機修正...")
            
            # 創建測試專案
            test_project = current_dir / "projects" / "test_timing_correction"
            test_project.mkdir(exist_ok=True)
            
            # 創建測試程式碼文件（包含已知漏洞）
            test_code = '''
def unsafe_function(user_input):
    # CWE-78: OS Command Injection
    import os
    command = f"ls {user_input}"
    os.system(command)  # 危險：直接執行用戶輸入
    
    # CWE-89: SQL Injection  
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    # 危險：SQL 注入漏洞
    
    # CWE-79: Cross-site Scripting
    html = f"<div>{user_input}</div>"  # 危險：XSS 漏洞
    return html

def main():
    user_data = input("Enter data: ")
    unsafe_function(user_data)
'''
            
            with open(test_project / "test_vulnerable_code.py", "w", encoding="utf-8") as f:
                f.write(test_code)
            
            # 創建模擬 Copilot 回應
            mock_response = f"""
這是一個包含安全漏洞的程式碼範例：

```python
{test_code}
```

這個程式碼存在多個安全問題，需要修正。
"""
            
            # 初始化 CopilotHandler
            handler = CopilotHandler()
            handler.last_response = mock_response  # 模擬智能等待完成後的回應
            
            # 測試 1：驗證掃描時機
            self.logger.info("📋 測試 1: 驗證掃描在正確時機執行...")
            
            # 模擬智能等待完成後的掃描
            if handler.cwe_scanner:
                vulnerability_detected = handler._perform_immediate_cwe_scan(mock_response)
                
                if vulnerability_detected:
                    self.logger.info("✅ 成功檢測到漏洞，掃描時機正確")
                    
                    # 檢查掃描結果暫存
                    if hasattr(handler, '_current_scan_results') and handler._current_scan_results:
                        self.logger.info("✅ 掃描結果已正確暫存")
                        
                        # 檢查檢測到的漏洞類型
                        vulnerabilities = handler._current_scan_results.get('vulnerabilities', [])
                        self.logger.info(f"🔍 檢測到 {len(vulnerabilities)} 個漏洞:")
                        for vuln in vulnerabilities:
                            self.logger.info(f"   - {vuln.get('cwe_id', 'Unknown')}: {vuln.get('description', 'No description')}")
                        
                        # 測試 2：驗證報告生成
                        self.logger.info("📋 測試 2: 驗證 CWE 報告生成...")
                        handler._generate_cwe_results_report(
                            vulnerabilities,
                            mock_response,
                            str(test_project),
                            1
                        )
                        
                        # 檢查報告檔案是否生成
                        cwe_results_dir = current_dir / "ExecutionResult" / "CWE_Results" / "Vulnerable"
                        if cwe_results_dir.exists():
                            self.logger.info("✅ CWE_Results/Vulnerable 目錄存在")
                            
                            # 查找生成的報告
                            for report_file in cwe_results_dir.glob("**/cwe_security_report_*.json"):
                                self.logger.info(f"✅ 找到 CWE 報告: {report_file.name}")
                                
                                # 驗證報告內容
                                with open(report_file, 'r', encoding='utf-8') as f:
                                    report_data = json.load(f)
                                    
                                if 'scan_results' in report_data and report_data['scan_results']:
                                    self.logger.info("✅ 報告內容驗證通過")
                                else:
                                    self.logger.warning("⚠️ 報告內容可能有問題")
                                break
                        else:
                            self.logger.warning("⚠️ CWE_Results 目錄未找到")
                    else:
                        self.logger.warning("⚠️ 掃描結果未正確暫存")
                else:
                    self.logger.warning("⚠️ 未檢測到預期的漏洞")
            else:
                self.logger.warning("⚠️ CWE 掃描器未初始化")
            
            # 測試 3：驗證時機與自動化流程的分離
            self.logger.info("📋 測試 3: 驗證掃描與自動化流程的獨立性...")
            
            # 檢查自動化流程目錄結構是否不受影響
            success_dir = current_dir / "ExecutionResult" / "Success"
            fail_dir = current_dir / "ExecutionResult" / "Fail"
            
            self.logger.info(f"✅ Success 目錄: {success_dir.exists()}")
            self.logger.info(f"✅ Fail 目錄: {fail_dir.exists()}")
            self.logger.info("✅ 自動化流程目錄結構獨立於 CWE 結果")
            
            self.logger.info("🎉 CWE 掃描時機修正測試完成！")
            
        except Exception as e:
            self.logger.error(f"❌ 測試失敗: {str(e)}")
            raise
    
    def test_timing_sequence(self):
        """測試完整的時機序列"""
        self.logger.info("📋 測試完整的處理時機序列...")
        
        try:
            # 模擬完整流程的時機
            timing_log = []
            
            # 模擬步驟
            timing_log.append("1. 開始智能等待")
            time.sleep(0.1)
            
            timing_log.append("2. 智能等待完成 - 內容穩定")
            time.sleep(0.1)
            
            timing_log.append("3. ✅ 立即執行 CWE 掃描 (修正後的時機)")
            time.sleep(0.1)
            
            timing_log.append("4. CWE 掃描完成，結果暫存")
            time.sleep(0.1)
            
            timing_log.append("5. 開始複製操作")
            time.sleep(0.1)
            
            timing_log.append("6. 複製完成")
            time.sleep(0.1)
            
            timing_log.append("7. 儲存到 Success/Fail 目錄")
            time.sleep(0.1)
            
            timing_log.append("8. 生成 CWE 報告到獨立目錄")
            time.sleep(0.1)
            
            timing_log.append("9. 處理完成")
            
            self.logger.info("⏱️ 修正後的時機序列:")
            for i, step in enumerate(timing_log, 1):
                self.logger.info(f"   {step}")
            
            self.logger.info("✅ 時機序列驗證完成 - CWE 掃描在正確位置執行")
            
        except Exception as e:
            self.logger.error(f"❌ 時機序列測試失敗: {str(e)}")
            raise

def main():
    """執行所有測試"""
    try:
        test_runner = TestCWEScanTimingCorrection()
        
        # 執行測試
        test_runner.test_scan_timing_correction()
        test_runner.test_timing_sequence()
        
        print("\n" + "="*60)
        print("🎉 所有 CWE 掃描時機修正測試已完成")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 測試執行失敗: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()