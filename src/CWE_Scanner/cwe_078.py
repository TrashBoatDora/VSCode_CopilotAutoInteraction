"""
CWE-078: 作業系統命令注入掃描器
檢測可能導致命令注入攻擊的代碼模式
"""

from typing import List
from cwe_base import CWEScanner, ScanResult, ScanUtils
import re


class CWE078Scanner(CWEScanner):
    """CWE-078: 作業系統命令注入掃描器"""
    
    def __init__(self):
        super().__init__(
            cwe_id="CWE-078",
            name="OS Command Injection",
            description="檢測可能導致命令注入攻擊的代碼模式"
        )
        
        # 危險的命令執行模式
        self.dangerous_command_patterns = [
            # Python
            r'os\.system\s*\([^)]*(?:input|request|args|params)[^)]*\)',
            r'subprocess\.(?:call|run|Popen|check_output)\s*\([^)]*(?:input|request|args|params)[^)]*\)',
            r'os\.popen\s*\([^)]*(?:input|request|args|params)[^)]*\)',
            r'commands\.getoutput\s*\([^)]*(?:input|request|args|params)[^)]*\)',
            
            # JavaScript/Node.js
            r'exec\s*\([^)]*(?:req\.|params|query)[^)]*\)',
            r'spawn\s*\([^)]*(?:req\.|params|query)[^)]*\)',
            r'execSync\s*\([^)]*(?:req\.|params|query)[^)]*\)',
            r'child_process\.(?:exec|spawn|execSync)\s*\([^)]*(?:req\.|params|query)[^)]*\)',
            
            # Java
            r'Runtime\.getRuntime\(\)\.exec\s*\([^)]*(?:request\.getParameter|args\[)[^)]*\)',
            r'ProcessBuilder\s*\([^)]*(?:request\.getParameter|args\[)[^)]*\)',
            
            # PHP
            r'(?:exec|system|shell_exec|passthru|popen)\s*\([^)]*\$_(?:GET|POST|REQUEST)[^)]*\)',
            r'`[^`]*\$_(?:GET|POST|REQUEST)[^`]*`',  # 反引號執行
            
            # C/C++
            r'system\s*\([^)]*(?:argv\[|getenv)[^)]*\)',
            r'popen\s*\([^)]*(?:argv\[|getenv)[^)]*\)',
        ]
        
        # 命令注入攻擊字符
        self.injection_chars = [
            r'[;&|`$\(\)]',  # 命令分隔符和特殊字符
            r'>>?',          # 重定向
            r'<<',           # Here document
            r'\|\|',         # OR 操作符
            r'&&',           # AND 操作符
        ]
        
        # 安全的命令執行模式
        self.safe_command_patterns = [
            r'subprocess\.(?:call|run|Popen)\s*\(\s*\[.*?\]',  # 使用列表參數
            r'shlex\.(?:split|quote)',                         # 使用 shlex 模組
            r'pipes\.quote',                                   # 使用 pipes.quote
            r're\.escape',                                     # 使用正則轉義
            r'shell=False',                                    # 明確禁用 shell
        ]
        
        # 輸入清理模式
        self.sanitization_patterns = [
            r'(?:validate|sanitize|clean|escape|filter).*?command',
            r're\.sub\s*\(',
            r'str\.replace\s*\(',
            r'["\']\.join\s*\(',
            r'shlex\.quote\s*\(',
        ]
    
    def scan_text(self, text: str) -> List[ScanResult]:
        """掃描文本內容"""
        results = []
        lines = text.split('\n')
        total_lines = len(lines)
        
        # 檢查危險的命令執行
        command_matches = ScanUtils.find_patterns_in_text(text, self.dangerous_command_patterns)
        
        # 檢查注入字符
        injection_matches = ScanUtils.find_patterns_in_text(text, self.injection_chars)
        
        # 檢查安全模式
        safe_matches = ScanUtils.find_patterns_in_text(text, self.safe_command_patterns)
        
        # 檢查輸入清理
        sanitization_matches = ScanUtils.find_patterns_in_text(text, self.sanitization_patterns)
        
        # 分析命令執行漏洞
        if command_matches:
            for match in command_matches:
                # 檢查附近是否有安全措施
                line_start = max(0, match['line_number'] - 5)
                line_end = min(total_lines, match['line_number'] + 2)
                context_lines = lines[line_start:line_end]
                context = '\n'.join(context_lines)
                
                has_safe_pattern = any(
                    re.search(pattern, context, re.IGNORECASE) 
                    for pattern in self.safe_command_patterns
                )
                
                has_sanitization = any(
                    re.search(pattern, context, re.IGNORECASE) 
                    for pattern in self.sanitization_patterns
                )
                
                if not (has_safe_pattern or has_sanitization):
                    # 檢查是否使用 shell=True
                    if 'shell=True' in context:
                        confidence = 0.9
                        severity = "Critical"
                    else:
                        confidence = 0.7
                        severity = "High"
                    
                    description = f"檢測到潛在的命令注入漏洞: {match['match']}"
                    
                    results.append(self.create_result(
                        vulnerability_found=True,
                        confidence=confidence,
                        severity=severity,
                        description=description,
                        location=f"第 {match['line_number']} 行",
                        line_number=match['line_number'],
                        evidence=match['match'],
                        mitigation="使用參數化命令執行、輸入驗證和避免 shell=True"
                    ))
        
        # 檢查注入字符在字符串中的使用
        if injection_matches:
            for match in injection_matches:
                # 檢查是否在字符串字面量中
                line_text = lines[match['line_number'] - 1] if match['line_number'] <= len(lines) else ""
                
                # 簡單檢查是否在引號內
                before_match = line_text[:match['start'] - line_text.find(match['match'])]
                quote_count_single = before_match.count("'") - before_match.count("\\'")
                quote_count_double = before_match.count('"') - before_match.count('\\"')
                
                # 如果不在引號內，可能是命令注入
                if quote_count_single % 2 == 0 and quote_count_double % 2 == 0:
                    confidence = 0.6
                    severity = "Medium"
                    description = f"檢測到可能的命令注入字符: {match['match']}"
                    
                    results.append(self.create_result(
                        vulnerability_found=True,
                        confidence=confidence,
                        severity=severity,
                        description=description,
                        location=f"第 {match['line_number']} 行",
                        line_number=match['line_number'],
                        evidence=match['match'],
                        mitigation="避免在命令中使用特殊字符，使用白名單驗證"
                    ))
        
        # 如果使用了安全模式，給予正面評價
        if safe_matches and not command_matches:
            results.append(self.create_result(
                vulnerability_found=False,
                confidence=0.8,
                severity="Low",
                description="檢測到安全的命令執行模式"
            ))
        
        # 如果沒有發現問題
        if not results:
            results.append(self.create_result(
                vulnerability_found=False,
                confidence=0.8,
                severity="Low",
                description="未檢測到命令注入漏洞"
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