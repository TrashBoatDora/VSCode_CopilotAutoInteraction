"""
CWE 掃描器測試腳本
測試各個 CWE 掃描器的基本功能
"""

import os
import sys

# 添加 CWE_Scanner 目錄到路徑
cwe_scanner_dir = os.path.dirname(os.path.abspath(__file__))
if cwe_scanner_dir not in sys.path:
    sys.path.insert(0, cwe_scanner_dir)

# 測試用的惡意代碼樣本
test_samples = {
    "cwe_020_input_validation": """
# 不當的輸入驗證測試
user_input = input("Enter your name: ")
exec("print('Hello, " + user_input + "')")

request_data = request.args.get('data')
result = eval(request_data)
""",
    
    "cwe_022_path_traversal": """
# 路徑遍歷測試
import os
filename = input("Enter filename: ")
with open(filename, 'r') as f:
    content = f.read()

# 危險的路徑拼接
file_path = "../../../etc/passwd"
""",
    
    "cwe_078_command_injection": """
# 命令注入測試
import os
import subprocess

user_command = input("Enter command: ")
os.system("ls " + user_command)
subprocess.call("ping " + user_command, shell=True)
""",
    
    "cwe_079_xss": """
# XSS 測試
from flask import Flask, render_template_string, request

app = Flask(__name__)

@app.route('/unsafe')
def unsafe():
    user_data = request.args.get('data', '')
    return render_template_string('<h1>Hello ' + user_data + '</h1>')

# 危險的 JavaScript
script_content = "<script>alert('XSS')</script>"
""",
    
    "cwe_095_code_injection": """
# 程式碼注入測試
user_code = input("Enter Python code: ")
eval(user_code)
exec(user_code)

# 動態導入
module_name = request.args.get('module')
imported_module = __import__(module_name)
""",
    
    "cwe_327_weak_crypto": """
# 弱加密演算法測試
import hashlib
import md5

password = "secret123"
weak_hash = hashlib.md5(password.encode()).hexdigest()
another_weak = hashlib.sha1(password.encode()).hexdigest()

# DES 加密 (已過時)
from Crypto.Cipher import DES
cipher = DES.new(b'key12345', DES.MODE_ECB)
""",
    
    "cwe_400_resource_consumption": """
# 資源消耗測試
user_size = int(input("Enter array size: "))
big_array = [0] * user_size

# 潛在的無限循環
while True:
    print("This might run forever")
    
# 大量記憶體分配
data = list(range(user_size * 1000000))
""",
    
    "safe_code": """
# 安全的代碼示例
import hashlib
import re

def validate_input(user_input):
    # 輸入驗證
    if not re.match(r'^[a-zA-Z0-9_]+$', user_input):
        raise ValueError("Invalid input")
    return user_input

def secure_hash(password):
    # 使用強哈希
    return hashlib.sha256(password.encode()).hexdigest()

def safe_file_read(filename):
    # 路徑驗證
    if '..' in filename or filename.startswith('/'):
        raise ValueError("Invalid filename")
    return open(filename, 'r').read()
"""
}


def test_individual_scanners():
    """測試各個掃描器"""
    print("=" * 60)
    print("測試各個 CWE 掃描器")
    print("=" * 60)
    
    try:
        # 測試 CWE-020
        from cwe_020 import CWE020Scanner
        scanner_020 = CWE020Scanner()
        results_020 = scanner_020.scan_text(test_samples["cwe_020_input_validation"])
        print(f"CWE-020 掃描結果: {len(results_020)} 項")
        for result in results_020:
            if result.vulnerability_found:
                print(f"  - [{result.severity}] {result.description}")
        print()
        
        # 測試 CWE-078
        from cwe_078 import CWE078Scanner
        scanner_078 = CWE078Scanner()
        results_078 = scanner_078.scan_text(test_samples["cwe_078_command_injection"])
        print(f"CWE-078 掃描結果: {len(results_078)} 項")
        for result in results_078:
            if result.vulnerability_found:
                print(f"  - [{result.severity}] {result.description}")
        print()
        
        # 測試 CWE-327
        from cwe_327 import CWE327Scanner
        scanner_327 = CWE327Scanner()
        results_327 = scanner_327.scan_text(test_samples["cwe_327_weak_crypto"])
        print(f"CWE-327 掃描結果: {len(results_327)} 項")
        for result in results_327:
            if result.vulnerability_found:
                print(f"  - [{result.severity}] {result.description}")
        print()
        
        print("個別掃描器測試完成!")
        
    except ImportError as e:
        print(f"導入錯誤: {e}")
        print("請確保所有 CWE 掃描器文件都存在且無語法錯誤")
    except Exception as e:
        print(f"測試過程中發生錯誤: {e}")


def test_main_scanner():
    """測試主掃描器"""
    print("=" * 60)
    print("測試 CWE 主掃描器")
    print("=" * 60)
    
    try:
        from CWE_main import CWEMainScanner
        
        # 創建主掃描器
        main_scanner = CWEMainScanner()
        
        # 測試文本掃描
        print("測試文本掃描...")
        results = main_scanner.scan_text(test_samples["cwe_020_input_validation"])
        print(f"掃描完成，共 {len(results)} 個掃描器執行")
        
        # 生成報告
        print("\n生成文本報告...")
        text_report = main_scanner.generate_report(results, 'text')
        print(text_report[:500] + "..." if len(text_report) > 500 else text_report)
        
        print("\n主掃描器測試完成!")
        
    except ImportError as e:
        print(f"導入錯誤: {e}")
        print("請確保 CWE_main.py 和所有依賴文件都存在")
    except Exception as e:
        print(f"測試過程中發生錯誤: {e}")


def create_test_files():
    """創建測試文件"""
    print("=" * 60)
    print("創建測試文件")
    print("=" * 60)
    
    test_dir = os.path.join(os.path.dirname(__file__), "test_files")
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    
    for name, content in test_samples.items():
        file_path = os.path.join(test_dir, f"{name}.py")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"創建測試文件: {file_path}")
    
    return test_dir


def test_file_scanning():
    """測試文件掃描"""
    print("=" * 60)
    print("測試文件掃描功能")
    print("=" * 60)
    
    # 創建測試文件
    test_dir = create_test_files()
    
    try:
        from CWE_main import CWEMainScanner
        
        # 創建主掃描器
        scanner = CWEMainScanner(['CWE-020', 'CWE-078', 'CWE-327'])  # 只測試部分掃描器
        
        # 掃描目錄
        print(f"掃描目錄: {test_dir}")
        results = scanner.scan_directory(test_dir, ['.py'])
        
        print(f"掃描完成，共處理 {len(results)} 個文件")
        
        # 生成簡化報告
        vulnerability_count = 0
        for file_path, file_results in results.items():
            print(f"\n文件: {file_path}")
            for cwe_id, cwe_results in file_results.items():
                for result in cwe_results:
                    if result.vulnerability_found:
                        vulnerability_count += 1
                        print(f"  - [{result.severity}] {cwe_id}: {result.description}")
        
        print(f"\n總計發現 {vulnerability_count} 個漏洞")
        
    except Exception as e:
        print(f"文件掃描測試失敗: {e}")


if __name__ == "__main__":
    print("CWE 掃描器功能測試")
    print("=" * 60)
    
    # 測試個別掃描器
    test_individual_scanners()
    
    # 測試主掃描器
    test_main_scanner()
    
    # 測試文件掃描
    test_file_scanning()
    
    print("\n測試完成！")