"""
CWE 掃描器主程式
整合所有 CWE 漏洞掃描器，提供統一的調用接口
"""

import os
import sys
import json
from typing import List, Dict, Any, Optional
from dataclasses import asdict
from datetime import datetime

# 添加當前目錄到 Python 路徑以支持相對導入
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 導入基礎類別
from cwe_base import CWEScanner, ScanResult, ScanUtils

# 導入所有 CWE 掃描器
from cwe_020 import CWE020Scanner
from cwe_022 import CWE022Scanner  
from cwe_078 import CWE078Scanner
from cwe_079 import CWE079Scanner
from cwe_095 import CWE095Scanner
from cwe_113 import CWE113Scanner
from cwe_327 import CWE327Scanner
from cwe_400 import CWE400Scanner


class CWEMainScanner:
    """CWE 主掃描器，整合所有個別的 CWE 掃描器"""
    
    def __init__(self, enabled_scanners: Optional[List[str]] = None):
        """
        初始化主掃描器
        
        Args:
            enabled_scanners: 要啟用的掃描器列表，如果為 None 則啟用所有掃描器
        """
        # 初始化所有可用的掃描器
        self.available_scanners = {
            'CWE-020': CWE020Scanner(),
            'CWE-022': CWE022Scanner(),
            'CWE-078': CWE078Scanner(),
            'CWE-079': CWE079Scanner(),
            'CWE-095': CWE095Scanner(),
            'CWE-113': CWE113Scanner(),
            'CWE-327': CWE327Scanner(),
            'CWE-400': CWE400Scanner(),
        }
        
        # 設定啟用的掃描器
        if enabled_scanners is None:
            self.enabled_scanners = self.available_scanners
        else:
            self.enabled_scanners = {
                cwe_id: scanner for cwe_id, scanner in self.available_scanners.items()
                if cwe_id in enabled_scanners
            }
        
        print(f"CWE 主掃描器初始化完成，啟用 {len(self.enabled_scanners)} 個掃描器")
        for cwe_id in self.enabled_scanners.keys():
            print(f"  - {cwe_id}")
    
    def scan_text(self, text: str, scanner_filter: Optional[List[str]] = None) -> Dict[str, List[ScanResult]]:
        """
        掃描文本內容
        
        Args:
            text: 要掃描的文本
            scanner_filter: 要使用的掃描器過濾列表
            
        Returns:
            Dict[str, List[ScanResult]]: 掃描結果，按 CWE ID 分組
        """
        results = {}
        
        scanners_to_use = self.enabled_scanners
        if scanner_filter:
            scanners_to_use = {
                cwe_id: scanner for cwe_id, scanner in self.enabled_scanners.items()
                if cwe_id in scanner_filter
            }
        
        for cwe_id, scanner in scanners_to_use.items():
            try:
                scan_results = scanner.scan_text(text)
                results[cwe_id] = scan_results
                print(f"  {cwe_id}: {len(scan_results)} 個結果")
            except Exception as e:
                print(f"掃描器 {cwe_id} 執行時發生錯誤: {str(e)}")
                # 創建錯誤結果
                error_result = scanner.create_result(
                    vulnerability_found=False,
                    confidence=0.0,
                    severity="Low",
                    description=f"掃描器執行錯誤: {str(e)}"
                )
                results[cwe_id] = [error_result]
        
        return results
    
    def scan_file(self, file_path: str, scanner_filter: Optional[List[str]] = None) -> Dict[str, List[ScanResult]]:
        """
        掃描單個文件
        
        Args:
            file_path: 文件路徑
            scanner_filter: 要使用的掃描器過濾列表
            
        Returns:
            Dict[str, List[ScanResult]]: 掃描結果，按 CWE ID 分組
        """
        print(f"掃描文件: {file_path}")
        
        if not os.path.exists(file_path):
            return {"ERROR": [ScanResult(
                cwe_id="ERROR",
                vulnerability_found=False,
                confidence=0.0,
                severity="Low",
                description=f"文件不存在: {file_path}"
            )]}
        
        results = {}
        scanners_to_use = self.enabled_scanners
        if scanner_filter:
            scanners_to_use = {
                cwe_id: scanner for cwe_id, scanner in self.enabled_scanners.items()
                if cwe_id in scanner_filter
            }
        
        for cwe_id, scanner in scanners_to_use.items():
            try:
                scan_results = scanner.scan_file(file_path)
                results[cwe_id] = scan_results
            except Exception as e:
                print(f"掃描器 {cwe_id} 執行時發生錯誤: {str(e)}")
                error_result = scanner.create_result(
                    vulnerability_found=False,
                    confidence=0.0,
                    severity="Low",
                    description=f"掃描器執行錯誤: {str(e)}"
                )
                results[cwe_id] = [error_result]
        
        return results
    
    def scan_directory(self, directory_path: str, file_extensions: Optional[List[str]] = None,
                      scanner_filter: Optional[List[str]] = None) -> Dict[str, Dict[str, List[ScanResult]]]:
        """
        掃描目錄下的所有文件
        
        Args:
            directory_path: 目錄路徑
            file_extensions: 要掃描的文件擴展名列表
            scanner_filter: 要使用的掃描器過濾列表
            
        Returns:
            Dict[str, Dict[str, List[ScanResult]]]: 掃描結果，按文件路徑和 CWE ID 分組
        """
        print(f"掃描目錄: {directory_path}")
        
        if not os.path.exists(directory_path):
            return {"ERROR": {"ERROR": [ScanResult(
                cwe_id="ERROR",
                vulnerability_found=False,
                confidence=0.0,
                severity="Low",
                description=f"目錄不存在: {directory_path}"
            )]}}
        
        if file_extensions is None:
            file_extensions = ['.py', '.java', '.js', '.ts', '.php', '.cpp', '.c', '.cs', '.html', '.jsp']
        
        results = {}
        file_count = 0
        
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if any(file.endswith(ext) for ext in file_extensions):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, directory_path)
                    
                    file_results = self.scan_file(file_path, scanner_filter)
                    results[relative_path] = file_results
                    file_count += 1
        
        print(f"掃描完成，共處理 {file_count} 個文件")
        return results
    
    def generate_report(self, scan_results: Dict[str, Any], output_format: str = 'json') -> str:
        """
        生成掃描報告
        
        Args:
            scan_results: 掃描結果
            output_format: 輸出格式 ('json', 'text', 'html')
            
        Returns:
            str: 格式化的報告內容
        """
        if output_format == 'json':
            return self._generate_json_report(scan_results)
        elif output_format == 'text':
            return self._generate_text_report(scan_results)
        elif output_format == 'html':
            return self._generate_html_report(scan_results)
        else:
            raise ValueError(f"不支援的輸出格式: {output_format}")
    
    def _generate_json_report(self, scan_results: Dict[str, Any]) -> str:
        """生成 JSON 格式報告"""
        report = {
            'scan_time': datetime.now().isoformat(),
            'total_files': len(scan_results) if isinstance(scan_results, dict) else 1,
            'enabled_scanners': list(self.enabled_scanners.keys()),
            'results': {}
        }
        
        # 轉換 ScanResult 對象為字典
        if isinstance(list(scan_results.values())[0], dict):
            # 多文件掃描結果
            for file_path, file_results in scan_results.items():
                report['results'][file_path] = {}
                for cwe_id, cwe_results in file_results.items():
                    report['results'][file_path][cwe_id] = [
                        asdict(result) for result in cwe_results
                    ]
        else:
            # 單文件或文本掃描結果
            for cwe_id, cwe_results in scan_results.items():
                report['results'][cwe_id] = [
                    asdict(result) for result in cwe_results
                ]
        
        return json.dumps(report, indent=2, ensure_ascii=False)
    
    def _generate_text_report(self, scan_results: Dict[str, Any]) -> str:
        """生成文本格式報告"""
        report_lines = [
            "CWE 漏洞掃描報告",
            "=" * 50,
            f"掃描時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"啟用掃描器: {', '.join(self.enabled_scanners.keys())}",
            "",
        ]
        
        vulnerability_count = 0
        warning_count = 0
        
        if isinstance(list(scan_results.values())[0], dict):
            # 多文件掃描結果
            for file_path, file_results in scan_results.items():
                report_lines.append(f"文件: {file_path}")
                report_lines.append("-" * 30)
                
                for cwe_id, cwe_results in file_results.items():
                    for result in cwe_results:
                        if result.vulnerability_found:
                            if result.severity in ['Critical', 'High']:
                                vulnerability_count += 1
                            else:
                                warning_count += 1
                            
                            report_lines.append(f"  [{result.severity}] {cwe_id}: {result.description}")
                            if result.location:
                                report_lines.append(f"    位置: {result.location}")
                            if result.evidence:
                                report_lines.append(f"    證據: {result.evidence}")
                            if result.mitigation:
                                report_lines.append(f"    建議: {result.mitigation}")
                            report_lines.append("")
                
                report_lines.append("")
        else:
            # 單文件或文本掃描結果
            for cwe_id, cwe_results in scan_results.items():
                report_lines.append(f"{cwe_id} 掃描結果:")
                for result in cwe_results:
                    if result.vulnerability_found:
                        if result.severity in ['Critical', 'High']:
                            vulnerability_count += 1
                        else:
                            warning_count += 1
                        
                        report_lines.append(f"  [{result.severity}] {result.description}")
                        if result.location:
                            report_lines.append(f"    位置: {result.location}")
                        if result.evidence:
                            report_lines.append(f"    證據: {result.evidence}")
                        if result.mitigation:
                            report_lines.append(f"    建議: {result.mitigation}")
                        report_lines.append("")
                
                report_lines.append("")
        
        # 添加摘要
        report_lines.extend([
            "掃描摘要",
            "=" * 20,
            f"發現 {vulnerability_count} 個高風險漏洞",
            f"發現 {warning_count} 個警告",
            f"總計 {vulnerability_count + warning_count} 個問題"
        ])
        
        return "\n".join(report_lines)
    
    def _generate_html_report(self, scan_results: Dict[str, Any]) -> str:
        """生成 HTML 格式報告"""
        # 簡化的 HTML 報告
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>CWE 漏洞掃描報告</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 10px; border-radius: 5px; }}
                .vulnerability {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ff6b6b; background-color: #fff5f5; }}
                .warning {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ffa726; background-color: #fff8e1; }}
                .safe {{ margin: 10px 0; padding: 10px; border-left: 4px solid #66bb6a; background-color: #f1f8e9; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>CWE 漏洞掃描報告</h1>
                <p>掃描時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>啟用掃描器: {', '.join(self.enabled_scanners.keys())}</p>
            </div>
        """
        
        # 這裡可以添加更詳細的 HTML 生成邏輯
        html_content += """
            <p>詳細的 HTML 報告功能尚在開發中...</p>
        </body>
        </html>
        """
        
        return html_content


def main():
    """主程式入口點"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CWE 漏洞掃描器')
    parser.add_argument('target', help='要掃描的文件或目錄路徑')
    parser.add_argument('--format', choices=['json', 'text', 'html'], default='text', help='報告格式')
    parser.add_argument('--output', '-o', help='輸出文件路徑')
    parser.add_argument('--scanners', nargs='+', help='要使用的掃描器列表')
    parser.add_argument('--extensions', nargs='+', default=['.py', '.java', '.js', '.ts', '.php'], 
                       help='要掃描的文件擴展名')
    
    args = parser.parse_args()
    
    # 初始化掃描器
    scanner = CWEMainScanner(enabled_scanners=args.scanners)
    
    # 執行掃描
    if os.path.isfile(args.target):
        results = scanner.scan_file(args.target)
    elif os.path.isdir(args.target):
        results = scanner.scan_directory(args.target, file_extensions=args.extensions)
    else:
        print(f"錯誤: 無效的目標路徑 {args.target}")
        return 1
    
    # 生成報告
    report = scanner.generate_report(results, args.format)
    
    # 輸出報告
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"報告已保存到: {args.output}")
    else:
        print(report)
    
    return 0


if __name__ == '__main__':
    exit(main())