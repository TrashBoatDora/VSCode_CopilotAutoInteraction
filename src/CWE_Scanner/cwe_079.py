"""
CWE-079: 跨網站指令碼 (XSS) 掃描器
檢測可能導致 XSS 攻擊的代碼模式
"""

from typing import List
from cwe_base import CWEScanner, ScanResult, ScanUtils
import re


class CWE079Scanner(CWEScanner):
    """CWE-079: 跨網站指令碼 (XSS) 掃描器"""
    
    def __init__(self):
        super().__init__(
            cwe_id="CWE-079",
            name="Cross-Site Scripting (XSS)",
            description="檢測可能導致 XSS 攻擊的代碼模式"
        )
        
        # 危險的 HTML 輸出模式
        self.dangerous_html_patterns = [
            # Python (Flask, Django)
            r'render_template_string\s*\([^)]*(?:request|input)[^)]*\)',
            r'Markup\s*\([^)]*(?:request|input)[^)]*\)',
            r'format_html\s*\([^)]*(?:request|input)[^)]*\)',
            r'HttpResponse\s*\([^)]*(?:request\.GET|request\.POST)[^)]*\)',
            
            # JavaScript/Node.js
            r'document\.write\s*\([^)]*(?:req\.|params|query)[^)]*\)',
            r'innerHTML\s*=\s*[^;]*(?:req\.|params|query)',
            r'outerHTML\s*=\s*[^;]*(?:req\.|params|query)',
            r'insertAdjacentHTML\s*\([^)]*(?:req\.|params|query)[^)]*\)',
            
            # PHP
            r'echo\s+[^;]*\$_(?:GET|POST|REQUEST)',
            r'print\s+[^;]*\$_(?:GET|POST|REQUEST)',
            r'printf\s*\([^)]*\$_(?:GET|POST|REQUEST)[^)]*\)',
            
            # JSP/Java
            r'out\.print\s*\([^)]*request\.getParameter[^)]*\)',
            r'<%=\s*request\.getParameter',
        ]
        
        # XSS 攻擊載荷模式
        self.xss_payload_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'on\w+\s*=',  # event handlers
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'<svg[^>]*>',
            r'<img[^>]*onerror',
            r'<input[^>]*onfocus',
        ]
        
        # XSS 防護模式
        self.xss_protection_patterns = [
            # 轉義函數
            r'html\.escape\s*\(',
            r'cgi\.escape\s*\(',
            r'htmlspecialchars\s*\(',
            r'htmlentities\s*\(',
            r'escape\s*\(',
            r'sanitize\s*\(',
            
            # 模板引擎自動轉義
            r'autoescape\s*=\s*True',
            r'\{\{\s*.*?\s*\|\s*escape\s*\}\}',
            r'\{\{\s*.*?\s*\|\s*safe\s*\}\}',  # 需要注意的反向模式
            
            # Content Security Policy
            r'Content-Security-Policy',
            r'X-XSS-Protection',
            
            # 現代前端框架
            r'dangerouslySetInnerHTML',  # React (需要注意)
            r'v-html',                   # Vue.js (需要注意)
        ]
        
        # 危險的模板語法
        self.dangerous_template_patterns = [
            r'\{\{\s*.*?\s*\|\s*safe\s*\}\}',        # Django/Jinja2 safe filter
            r'\{\{\{.*?\}\}\}',                      # Handlebars unescaped
            r'<%=\s*[^%]*%>',                        # JSP/ERB raw output
            r'<%\s*[^%]*%>',                         # JSP/ERB code blocks
        ]
    
    def scan_text(self, text: str) -> List[ScanResult]:
        """掃描文本內容"""
        results = []
        lines = text.split('\n')
        total_lines = len(lines)
        
        # 檢查危險的 HTML 輸出
        html_matches = ScanUtils.find_patterns_in_text(text, self.dangerous_html_patterns)
        
        # 檢查 XSS 載荷
        payload_matches = ScanUtils.find_patterns_in_text(text, self.xss_payload_patterns)
        
        # 檢查防護措施
        protection_matches = ScanUtils.find_patterns_in_text(text, self.xss_protection_patterns)
        
        # 檢查危險的模板語法
        template_matches = ScanUtils.find_patterns_in_text(text, self.dangerous_template_patterns)
        
        # 分析 HTML 輸出漏洞
        if html_matches:
            for match in html_matches:
                # 檢查附近是否有防護措施
                line_start = max(0, match['line_number'] - 3)
                line_end = min(total_lines, match['line_number'] + 3)
                context_lines = lines[line_start:line_end]
                context = '\n'.join(context_lines)
                
                has_protection = any(
                    re.search(pattern, context, re.IGNORECASE) 
                    for pattern in self.xss_protection_patterns
                )
                
                if not has_protection:
                    confidence = 0.8
                    severity = "High"
                    description = f"檢測到未轉義的 HTML 輸出: {match['match']}"
                    
                    results.append(self.create_result(
                        vulnerability_found=True,
                        confidence=confidence,
                        severity=severity,
                        description=description,
                        location=f"第 {match['line_number']} 行",
                        line_number=match['line_number'],
                        evidence=match['match'],
                        mitigation="對所有用戶輸入進行 HTML 轉義或使用安全的模板引擎"
                    ))
        
        # 分析 XSS 載荷
        if payload_matches:
            for match in payload_matches:
                confidence = 0.9
                severity = "Critical"
                description = f"檢測到潛在的 XSS 載荷: {match['match']}"
                
                results.append(self.create_result(
                    vulnerability_found=True,
                    confidence=confidence,
                    severity=severity,
                    description=description,
                    location=f"第 {match['line_number']} 行",
                    line_number=match['line_number'],
                    evidence=match['match'],
                    mitigation="移除或正確轉義 XSS 載荷，實施 CSP 政策"
                ))
        
        # 分析危險的模板語法
        if template_matches:
            for match in template_matches:
                confidence = 0.7
                severity = "Medium"
                description = f"檢測到可能不安全的模板語法: {match['match']}"
                
                results.append(self.create_result(
                    vulnerability_found=True,
                    confidence=confidence,
                    severity=severity,
                    description=description,
                    location=f"第 {match['line_number']} 行",
                    line_number=match['line_number'],
                    evidence=match['match'],
                    mitigation="避免使用 safe 過濾器，確保所有輸出都經過適當轉義"
                ))
        
        # 檢查是否有適當的防護措施
        if (html_matches or payload_matches) and not protection_matches:
            results.append(self.create_result(
                vulnerability_found=True,
                confidence=0.6,
                severity="Medium",
                description="代碼中有 HTML 輸出但缺乏 XSS 防護措施",
                mitigation="實施 HTML 轉義、CSP 政策和輸入驗證"
            ))
        
        # 如果有防護措施但沒有危險模式
        if protection_matches and not (html_matches or payload_matches):
            results.append(self.create_result(
                vulnerability_found=False,
                confidence=0.8,
                severity="Low",
                description="檢測到 XSS 防護措施"
            ))
        
        # 如果沒有發現問題
        if not results:
            results.append(self.create_result(
                vulnerability_found=False,
                confidence=0.7,
                severity="Low",
                description="未檢測到明顯的 XSS 漏洞"
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