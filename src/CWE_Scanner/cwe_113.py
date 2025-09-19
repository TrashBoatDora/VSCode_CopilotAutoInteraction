"""
CWE-113: HTTP 回應分割掃描器
檢測可能導致 HTTP 回應分割攻擊的代碼模式
"""

from typing import List
from cwe_base import CWEScanner, ScanResult, ScanUtils
import re


class CWE113Scanner(CWEScanner):
    """CWE-113: HTTP 回應分割掃描器"""
    
    def __init__(self):
        super().__init__(
            cwe_id="CWE-113",
            name="HTTP Response Splitting",
            description="檢測可能導致 HTTP 回應分割攻擊的代碼模式"
        )
        
        # 危險的 HTTP 標頭設定模式
        self.dangerous_header_patterns = [
            # Python Flask/Django
            r'response\[.*?\]\s*=\s*[^;]*(?:request|input|params)',
            r'add_header\s*\([^)]*(?:request|input|params)[^)]*\)',
            r'HttpResponse\s*\([^)]*headers.*?(?:request|input|params)',
            
            # JavaScript/Node.js
            r'res\.(?:set|header)\s*\([^)]*(?:req\.|params|query)[^)]*\)',
            r'setHeader\s*\([^)]*(?:req\.|params|query)[^)]*\)',
            
            # Java Servlet
            r'response\.(?:setHeader|addHeader)\s*\([^)]*request\.getParameter[^)]*\)',
            r'response\.sendRedirect\s*\([^)]*request\.getParameter[^)]*\)',
            
            # PHP
            r'header\s*\([^)]*\$_(?:GET|POST|REQUEST)[^)]*\)',
            r'setcookie\s*\([^)]*\$_(?:GET|POST|REQUEST)[^)]*\)',
            
            # ASP.NET
            r'Response\.(?:AddHeader|AppendHeader)\s*\([^)]*Request\.',
            r'Response\.Redirect\s*\([^)]*Request\.',
        ]
        
        # HTTP 回應分割攻擊字符
        self.splitting_chars = [
            r'\\r\\n',        # CRLF 序列
            r'\\x0d\\x0a',    # 十六進制 CRLF
            r'%0d%0a',        # URL 編碼 CRLF
            r'%0D%0A',        # 大寫 URL 編碼 CRLF
            r'\r\n',          # 實際 CRLF
        ]
        
        # 安全的標頭處理模式
        self.safe_header_patterns = [
            r'(?:validate|sanitize|clean).*?header',
            r're\.sub\s*\([^)]*[\\\\]r[\\\\]n',
            r'str\.replace\s*\([^)]*[\\\\]r[\\\\]n',
            r'header.*?(?:whitelist|allowlist)',
            r'preg_replace\s*\([^)]*[\\\\]r[\\\\]n',
        ]
    
    def scan_text(self, text: str) -> List[ScanResult]:
        """掃描文本內容"""
        results = []
        lines = text.split('\n')
        total_lines = len(lines)
        
        # 檢查危險的標頭設定
        header_matches = ScanUtils.find_patterns_in_text(text, self.dangerous_header_patterns)
        
        # 檢查分割字符
        splitting_matches = ScanUtils.find_patterns_in_text(text, self.splitting_chars)
        
        # 檢查安全措施
        safe_matches = ScanUtils.find_patterns_in_text(text, self.safe_header_patterns)
        
        # 分析標頭設定漏洞
        if header_matches:
            for match in header_matches:
                # 檢查附近是否有安全措施
                line_start = max(0, match['line_number'] - 3)
                line_end = min(total_lines, match['line_number'] + 3)
                context_lines = lines[line_start:line_end]
                context = '\n'.join(context_lines)
                
                has_safety = any(
                    re.search(pattern, context, re.IGNORECASE) 
                    for pattern in self.safe_header_patterns
                )
                
                if not has_safety:
                    confidence = 0.7
                    severity = "High"
                    description = f"檢測到未驗證的 HTTP 標頭設定: {match['match']}"
                    
                    results.append(self.create_result(
                        vulnerability_found=True,
                        confidence=confidence,
                        severity=severity,
                        description=description,
                        location=f"第 {match['line_number']} 行",
                        line_number=match['line_number'],
                        evidence=match['match'],
                        mitigation="驗證和清理 HTTP 標頭值，移除 CRLF 字符"
                    ))
        
        # 分析分割字符
        if splitting_matches:
            for match in splitting_matches:
                confidence = 0.9
                severity = "Critical"
                description = f"檢測到 HTTP 回應分割字符: {match['match']}"
                
                results.append(self.create_result(
                    vulnerability_found=True,
                    confidence=confidence,
                    severity=severity,
                    description=description,
                    location=f"第 {match['line_number']} 行",
                    line_number=match['line_number'],
                    evidence=match['match'],
                    mitigation="移除或轉義 CRLF 字符，使用安全的標頭設定函數"
                ))
        
        if not results:
            results.append(self.create_result(
                vulnerability_found=False,
                confidence=0.8,
                severity="Low",
                description="未檢測到 HTTP 回應分割漏洞"
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
        for result in results:
            if result.location is None:
                result.location = file_path
            else:
                result.location = f"{file_path} - {result.location}"
        
        return results