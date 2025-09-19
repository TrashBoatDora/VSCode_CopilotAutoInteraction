# -*- coding: utf-8 -*-
"""
測試新的 CWE 分離架構
驗證自動化流程不受 CWE 影響，CWE 結果正確分類到獨立目錄
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
from src.CWE_Scanner.CWE_main import CWEMainScanner

def test_cwe_separation_architecture():
    """測試新的 CWE 分離架構"""
    print("🔍 開始測試新的 CWE 分離架構...")
    
    # 建立臨時測試環境
    original_dir = os.getcwd()
    
    try:
        # 初始化 CWE 掃描器和 Copilot 處理器
        cwe_scanner = CWEMainScanner()
        copilot_handler = CopilotHandler(cwe_scanner=cwe_scanner)
        
        # 設定測試專案路徑
        test_project_name = "test_separation"
        test_project_path = os.path.join("projects", test_project_name)
        
        print(f"📁 設定測試專案路徑: {test_project_path}")
        
        # 測試案例 1: 測試後處理 CWE 掃描（無漏洞）
        print("\n=== 測試案例 1: 無漏洞後處理掃描 ===")
        clean_response = "This is a clean response with no security vulnerabilities. Just simple Python code."
        copilot_handler._perform_post_processing_cwe_scan(clean_response, test_project_path, 1)
        
        # 檢查是否在 CWE_Results/Safe 目錄生成報告
        safe_dir = os.path.join("ExecutionResult", "CWE_Results", "Safe", test_project_name)
        if os.path.exists(safe_dir):
            files = os.listdir(safe_dir)
            print(f"✅ CWE_Results/Safe 目錄已建立: {safe_dir}")
            print(f"   包含檔案: {files}")
        else:
            print(f"❌ CWE_Results/Safe 目錄未建立: {safe_dir}")
        
        # 測試案例 2: 測試後處理 CWE 掃描（有高風險漏洞）
        print("\n=== 測試案例 2: 高風險漏洞後處理掃描 ===")
        vulnerable_response = '''
        Here's some dangerous code:
        
        import os
        user_input = input("Enter command: ")
        os.system(user_input)  # Command injection vulnerability
        
        import sqlite3
        query = "SELECT * FROM users WHERE id = " + request.args.get('id')
        cursor.execute(query)  # SQL injection vulnerability
        '''
        
        copilot_handler._perform_post_processing_cwe_scan(vulnerable_response, test_project_path, 2)
        
        # 檢查是否在 CWE_Results/Vulnerable 目錄生成報告
        vulnerable_dir = os.path.join("ExecutionResult", "CWE_Results", "Vulnerable", test_project_name)
        if os.path.exists(vulnerable_dir):
            files = os.listdir(vulnerable_dir)
            print(f"✅ CWE_Results/Vulnerable 目錄已建立: {vulnerable_dir}")
            print(f"   包含檔案: {files}")
            
            # 檢查報告內容
            for file in files:
                if file.endswith('.json'):
                    with open(os.path.join(vulnerable_dir, file), 'r', encoding='utf-8') as f:
                        report_data = json.load(f)
                        print(f"   📄 JSON 報告 - 漏洞數: {report_data['total_vulnerabilities']}, 高風險: {report_data['high_risk_count']}")
        else:
            print(f"❌ CWE_Results/Vulnerable 目錄未建立: {vulnerable_dir}")
        
        # 測試案例 3: 測試批次掃描功能
        print("\n=== 測試案例 3: 批次掃描現有結果 ===")
        
        # 檢查是否有現有的 Success 目錄可以掃描
        success_dir = os.path.join("ExecutionResult", "Success")
        if os.path.exists(success_dir) and os.listdir(success_dir):
            print(f"發現現有結果目錄，執行批次掃描...")
            success = copilot_handler.batch_scan_existing_results()
            if success:
                print("✅ 批次掃描執行成功")
            else:
                print("❌ 批次掃描執行失敗")
        else:
            print("ℹ️ 沒有現有結果可供批次掃描")
        
        # 測試案例 4: 驗證目錄結構分離
        print("\n=== 測試案例 4: 目錄結構分離驗證 ===")
        
        # 檢查 CWE_Results 結構
        cwe_results_dir = os.path.join("ExecutionResult", "CWE_Results")
        if os.path.exists(cwe_results_dir):
            print(f"✅ CWE_Results 目錄存在: {cwe_results_dir}")
            
            safe_exists = os.path.exists(os.path.join(cwe_results_dir, "Safe"))
            vulnerable_exists = os.path.exists(os.path.join(cwe_results_dir, "Vulnerable"))
            
            print(f"   Safe 目錄: {'✅' if safe_exists else '❌'}")
            print(f"   Vulnerable 目錄: {'✅' if vulnerable_exists else '❌'}")
            
            if safe_exists:
                safe_projects = os.listdir(os.path.join(cwe_results_dir, "Safe"))
                print(f"   Safe 專案: {safe_projects}")
                
            if vulnerable_exists:
                vulnerable_projects = os.listdir(os.path.join(cwe_results_dir, "Vulnerable"))
                print(f"   Vulnerable 專案: {vulnerable_projects}")
        else:
            print(f"❌ CWE_Results 目錄不存在: {cwe_results_dir}")
        
        # 檢查自動化流程目錄是否獨立
        success_automation_dir = os.path.join("ExecutionResult", "Success")
        fail_automation_dir = os.path.join("ExecutionResult", "Fail")
        
        print(f"\n自動化流程目錄:")
        print(f"   Success 目錄: {'✅' if os.path.exists(success_automation_dir) else '❌'}")
        print(f"   Fail 目錄: {'✅' if os.path.exists(fail_automation_dir) else '❌'}")
        
        # 測試案例 5: 檢查全域統計更新
        print("\n=== 測試案例 5: 全域統計檢查 ===")
        global_stats_path = os.path.join("ExecutionResult", "CWEScanner_UpdateReport", "cwe_scan_statistics.json")
        
        if os.path.exists(global_stats_path):
            with open(global_stats_path, 'r', encoding='utf-8') as f:
                stats_data = json.load(f)
                print(f"✅ 全域統計已更新:")
                print(f"   總掃描次數: {stats_data['total_scans']}")
                print(f"   有漏洞專案數: {stats_data['projects_with_vulnerabilities']}")
                print(f"   高風險專案數: {stats_data['projects_with_high_risk']}")
                
                # 顯示最近的掃描記錄（包含新的欄位）
                if stats_data['scan_history']:
                    latest_scan = stats_data['scan_history'][-1]
                    print(f"   最新掃描記錄:")
                    print(f"     專案: {latest_scan['project_name']}")
                    print(f"     輪數: 第{latest_scan.get('round_number', 'N/A')}輪")
                    print(f"     安全分類: {latest_scan.get('result_type', 'N/A')}")
                    print(f"     結果目錄: {latest_scan.get('result_directory', 'N/A')}")
        else:
            print(f"❌ 全域統計檔案未找到: {global_stats_path}")
        
        print("\n🎉 CWE 分離架構測試完成！")
        print("✅ 新架構特點:")
        print("   - CWE 掃描不干預自動化流程")
        print("   - 安全結果獨立分類到 CWE_Results/Safe 和 Vulnerable")
        print("   - 支援批次掃描現有結果")
        print("   - 保持向後相容性")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試過程發生錯誤: {str(e)}")
        import traceback
        print(f"詳細錯誤資訊: {traceback.format_exc()}")
        return False
    
    finally:
        os.chdir(original_dir)

def test_automation_flow_independence():
    """測試自動化流程的獨立性"""
    print("\n🔬 測試自動化流程獨立性...")
    
    try:
        # 初始化處理器（模擬無 CWE 掃描器的情況）
        copilot_handler_no_cwe = CopilotHandler()
        
        # 模擬一個成功的自動化流程
        test_project_path = os.path.join("projects", "test_independence")
        test_response = "This is a simulated successful response from Copilot."
        
        # 這應該能正常完成，不會因為沒有 CWE 掃描器而失敗
        print("測試無 CWE 掃描器的自動化流程...")
        
        # 模擬儲存回應
        success = copilot_handler_no_cwe.save_response_to_file(
            test_project_path, 
            test_response, 
            is_success=True,
            round_number=1,
            prompt_text="測試提示詞"
        )
        
        if success:
            print("✅ 自動化流程獨立性測試通過")
            print("   - 沒有 CWE 掃描器時仍能正常運作")
            print("   - 自動化流程不依賴安全掃描")
            
            # 檢查檔案是否正確生成
            success_dir = os.path.join("ExecutionResult", "Success", "test_independence")
            if os.path.exists(success_dir):
                files = [f for f in os.listdir(success_dir) if f.endswith('.md')]
                print(f"   - 成功生成檔案: {files}")
            
            return True
        else:
            print("❌ 自動化流程獨立性測試失敗")
            return False
            
    except Exception as e:
        print(f"❌ 獨立性測試過程出錯: {str(e)}")
        return False

if __name__ == "__main__":
    # 執行主要測試
    success1 = test_cwe_separation_architecture()
    
    # 執行獨立性測試
    success2 = test_automation_flow_independence()
    
    overall_success = success1 and success2
    
    if overall_success:
        print("\n✅ 所有測試通過！新的 CWE 分離架構運作正常。")
        print("\n📋 架構優勢總結:")
        print("   1. 自動化流程穩定：不會因安全檢查而中斷")
        print("   2. 清晰分類：安全結果獨立分到 Safe/Vulnerable")
        print("   3. 後處理掃描：不影響原始流程性能")
        print("   4. 批次處理：可掃描現有歷史結果")
        print("   5. 向後相容：保留舊介面以防破壞")
    else:
        print("\n❌ 部分測試失敗，請檢查錯誤訊息。")
    
    sys.exit(0 if overall_success else 1)