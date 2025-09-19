"""
CWE-020: 不當的輸入驗證掃描器
檢測程式碼中缺乏適當輸入驗證的情況
"""

from typing import List
from cwe_base import CWEScanner, ScanResult, ScanUtils
import re


class CWE020Scanner(CWEScanner):
    """CWE-020: 不當的輸入驗證掃描器"""
    
    def __init__(self):
        super().__init__(
            cwe_id="CWE-020",
            name="Improper Input Validation",
            description="檢測缺乏適當輸入驗證的代碼模式"
        )
        
        # 危險的直接使用用戶輸入的模式
        self.dangerous_patterns = [
            # Python
            r'input\(\)\s*(?!.*(?:int|float|strip|validate|sanitize|clean))',
            r'request\.(?:args|form|json|data)\[.*?\]\s*(?!.*(?:validate|sanitize|clean|strip))',
            r'sys\.argv\[.*?\]\s*(?!.*(?:validate|sanitize|clean))',
            r'os\.environ\[.*?\]\s*(?!.*(?:validate|sanitize|clean))',
            
            # JavaScript/TypeScript
            r'req\.(?:query|body|params)\.\w+\s*(?!.*(?:validate|sanitize|escape))',
            r'location\.search\s*(?!.*(?:validate|sanitize|escape))',
            r'document\.cookie\s*(?!.*(?:validate|sanitize|escape))',
            
            # Java
            r'request\.getParameter\(.*?\)\s*(?!.*(?:validate|sanitize))',
            r'Scanner\.next\w*\(\)\s*(?!.*(?:validate|sanitize))',
            
            # PHP
            r'\$_(?:GET|POST|REQUEST|COOKIE)\[.*?\]\s*(?!.*(?:validate|sanitize|filter))',
            
            # C/C++
            r'gets\s*\(',
            r'scanf\s*\(',
            r'fgets\s*\([^,]*,[^,]*,\s*stdin\s*\)'
        ]
        
        # 驗證函數模式
        self.validation_patterns = [
            r'(?:validate|sanitize|clean|escape|filter)_?\w*\s*\(',
            r'is_(?:valid|safe|clean)\s*\(',
            r'check_\w*\s*\(',
            r'preg_match\s*\(',
            r'filter_var\s*\(',
            r'htmlspecialchars\s*\(',
            r'addslashes\s*\(',
            r'strip_tags\s*\('
        ]
        
        # 危險的字符串操作模式
        self.dangerous_string_ops = [
            r'["\'].*?\+.*?input.*?["\']',  # 字符串拼接用戶輸入
            r'["\'].*?\%.*?["\'].*?\%.*?',   # 格式化字符串
            r'f["\'].*?\{.*?\}.*?["\']',     # f-string with variables
            r'\.format\s*\([^)]*\w+[^)]*\)'  # .format() 方法
        ]
    
    def scan_text(self, text: str) -> List[ScanResult]:
        """掃描文本內容"""
        results = []
        lines = text.split('\n')
        total_lines = len(lines)
        
        # 檢查危險模式
        dangerous_matches = ScanUtils.find_patterns_in_text(text, self.dangerous_patterns)
        
        # 檢查是否存在驗證邏輯
        validation_matches = ScanUtils.find_patterns_in_text(text, self.validation_patterns)
        
        # 檢查危險的字符串操作
        string_op_matches = ScanUtils.find_patterns_in_text(text, self.dangerous_string_ops)
        
        # 分析結果
        if dangerous_matches:
            for match in dangerous_matches:
                # 檢查附近是否有驗證邏輯
                line_start = max(0, match['line_number'] - 3)
                line_end = min(total_lines, match['line_number'] + 3)
                context_lines = lines[line_start:line_end]
                context = '\n'.join(context_lines)
                
                has_validation = any(
                    re.search(pattern, context, re.IGNORECASE) 
                    for pattern in self.validation_patterns
                )
                
                if not has_validation:
                    confidence = 0.8
                    severity = "High"
                    description = f"檢測到未驗證的用戶輸入使用: {match['match']}"
                    
                    results.append(self.create_result(
                        vulnerability_found=True,
                        confidence=confidence,
                        severity=severity,
                        description=description,
                        location=f"第 {match['line_number']} 行",
                        line_number=match['line_number'],
                        evidence=match['match'],
                        mitigation="在使用用戶輸入前應進行適當的驗證和清理"
                    ))
        
        # 檢查字符串操作漏洞
        if string_op_matches:
            for match in string_op_matches:
                confidence = 0.6
                severity = "Medium"
                description = f"檢測到潛在的不安全字符串操作: {match['match']}"
                
                results.append(self.create_result(
                    vulnerability_found=True,
                    confidence=confidence,
                    severity=severity,
                    description=description,
                    location=f"第 {match['line_number']} 行",
                    line_number=match['line_number'],
                    evidence=match['match'],
                    mitigation="使用參數化查詢或模板引擎避免直接字符串拼接"
                ))
        
        # 如果沒有發現問題，返回安全結果
        if not results:
            results.append(self.create_result(
                vulnerability_found=False,
                confidence=0.9,
                severity="Low",
                description="未檢測到明顯的輸入驗證問題"
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