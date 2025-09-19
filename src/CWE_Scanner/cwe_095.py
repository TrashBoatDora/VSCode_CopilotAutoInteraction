"""
CWE-095: 程式碼注入掃描器
檢測可能導致程式碼注入攻擊的代碼模式
"""

from typing import List
from cwe_base import CWEScanner, ScanResult, ScanUtils
import re


class CWE095Scanner(CWEScanner):
    """CWE-095: 程式碼注入掃描器"""
    
    def __init__(self):
        super().__init__(
            cwe_id="CWE-095",
            name="Code Injection",
            description="檢測可能導致程式碼注入攻擊的代碼模式"
        )
        
        # 危險的程式碼執行模式
        self.dangerous_code_patterns = [
            # Python
            r'eval\s*\([^)]*(?:input|request|args|params)[^)]*\)',
            r'exec\s*\([^)]*(?:input|request|args|params)[^)]*\)',
            r'compile\s*\([^)]*(?:input|request|args|params)[^)]*\)',
            r'__import__\s*\([^)]*(?:input|request|args|params)[^)]*\)',
            
            # JavaScript
            r'eval\s*\([^)]*(?:req\.|params|query)[^)]*\)',
            r'Function\s*\([^)]*(?:req\.|params|query)[^)]*\)',
            r'setTimeout\s*\([^)]*(?:req\.|params|query)[^)]*\)',
            r'setInterval\s*\([^)]*(?:req\.|params|query)[^)]*\)',
            
            # PHP
            r'eval\s*\([^)]*\$_(?:GET|POST|REQUEST)[^)]*\)',
            r'create_function\s*\([^)]*\$_(?:GET|POST|REQUEST)[^)]*\)',
            r'preg_replace\s*\([^)]*\/.*?e[^)]*\$_(?:GET|POST|REQUEST)[^)]*\)',
            
            # Java
            r'ScriptEngine\.eval\s*\([^)]*request\.getParameter[^)]*\)',
            r'Class\.forName\s*\([^)]*request\.getParameter[^)]*\)',
            
            # Ruby
            r'eval\s*\([^)]*params\[',
            r'instance_eval\s*\([^)]*params\[',
            r'class_eval\s*\([^)]*params\[',
        ]
        
        # 動態載入模式
        self.dynamic_loading_patterns = [
            r'importlib\.import_module\s*\([^)]*(?:input|request)[^)]*\)',
            r'__import__\s*\([^)]*(?:input|request)[^)]*\)',
            r'getattr\s*\([^)]*(?:input|request)[^)]*\)',
            r'hasattr\s*\([^)]*(?:input|request)[^)]*\)',
            r'setattr\s*\([^)]*(?:input|request)[^)]*\)',
        ]
        
        # 反射相關模式
        self.reflection_patterns = [
            # Java
            r'Class\.forName\s*\([^)]*request\.',
            r'Method\.invoke\s*\([^)]*request\.',
            r'Constructor\.newInstance\s*\([^)]*request\.',
            
            # C#
            r'Assembly\.Load\s*\([^)]*Request\.',
            r'Type\.GetType\s*\([^)]*Request\.',
            r'Activator\.CreateInstance\s*\([^)]*Request\.',
        ]
        
        # 安全驗證模式
        self.security_patterns = [
            r'(?:whitelist|allowlist).*?check',
            r'(?:validate|sanitize).*?code',
            r'ast\.literal_eval\s*\(',
            r'json\.loads\s*\(',
            r'safe_eval\s*\(',
            r'restricted_eval\s*\(',
        ]
    
    def scan_text(self, text: str) -> List[ScanResult]:
        """掃描文本內容"""
        results = []
        lines = text.split('\n')
        total_lines = len(lines)
        
        # 檢查危險的程式碼執行
        code_matches = ScanUtils.find_patterns_in_text(text, self.dangerous_code_patterns)
        
        # 檢查動態載入
        loading_matches = ScanUtils.find_patterns_in_text(text, self.dynamic_loading_patterns)
        
        # 檢查反射
        reflection_matches = ScanUtils.find_patterns_in_text(text, self.reflection_patterns)
        
        # 檢查安全措施
        security_matches = ScanUtils.find_patterns_in_text(text, self.security_patterns)
        
        # 分析程式碼執行漏洞
        if code_matches:
            for match in code_matches:
                # 檢查附近是否有安全驗證
                line_start = max(0, match['line_number'] - 3)
                line_end = min(total_lines, match['line_number'] + 3)
                context_lines = lines[line_start:line_end]
                context = '\n'.join(context_lines)
                
                has_security = any(
                    re.search(pattern, context, re.IGNORECASE) 
                    for pattern in self.security_patterns
                )
                
                if not has_security:
                    confidence = 0.9
                    severity = "Critical"
                    description = f"檢測到危險的程式碼執行: {match['match']}"
                    
                    results.append(self.create_result(
                        vulnerability_found=True,
                        confidence=confidence,
                        severity=severity,
                        description=description,
                        location=f"第 {match['line_number']} 行",
                        line_number=match['line_number'],
                        evidence=match['match'],
                        mitigation="避免執行用戶提供的代碼，使用白名單驗證或沙箱環境"
                    ))
        
        # 分析動態載入漏洞
        if loading_matches:
            for match in loading_matches:
                confidence = 0.7
                severity = "High"
                description = f"檢測到潛在的動態載入漏洞: {match['match']}"
                
                results.append(self.create_result(
                    vulnerability_found=True,
                    confidence=confidence,
                    severity=severity,
                    description=description,
                    location=f"第 {match['line_number']} 行",
                    line_number=match['line_number'],
                    evidence=match['match'],
                    mitigation="限制動態載入的模組，使用白名單驗證"
                ))
        
        # 分析反射漏洞
        if reflection_matches:
            for match in reflection_matches:
                confidence = 0.8
                severity = "High"
                description = f"檢測到潛在的反射攻擊: {match['match']}"
                
                results.append(self.create_result(
                    vulnerability_found=True,
                    confidence=confidence,
                    severity=severity,
                    description=description,
                    location=f"第 {match['line_number']} 行",
                    line_number=match['line_number'],
                    evidence=match['match'],
                    mitigation="限制反射操作，驗證類名和方法名"
                ))
        
        # 如果有安全措施
        if security_matches and not (code_matches or loading_matches):
            results.append(self.create_result(
                vulnerability_found=False,
                confidence=0.8,
                severity="Low",
                description="檢測到安全的代碼處理模式"
            ))
        
        # 如果沒有發現問題
        if not results:
            results.append(self.create_result(
                vulnerability_found=False,
                confidence=0.8,
                severity="Low",
                description="未檢測到程式碼注入漏洞"
            ))
        
        return results
    
    def scan_file(self, file_path: str) -> List[ScanResult]:
        """掃描單個文件"""
        content = ScanUtils.read_file_safely(file_path)
        if content is None:
            return [self.create_result(
                vulnerability_found=False,
                confidence=0.0,
                severity="Low",
                description=f"無法讀取文件: {file_path}"
            )]
        
        results = self.scan_text(content)
        
        # 更新結果中的位置信息
        for result in results:
            if result.location is None:
                result.location = file_path
            else:
                result.location = f"{file_path} - {result.location}"
        
        return results