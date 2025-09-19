"""
CWE-022: 路徑遍歷掃描器
檢測可能導致路徑遍歷攻擊的代碼模式
"""

from typing import List
from cwe_base import CWEScanner, ScanResult, ScanUtils
import re


class CWE022Scanner(CWEScanner):
    """CWE-022: 路徑遍歷掃描器"""
    
    def __init__(self):
        super().__init__(
            cwe_id="CWE-022",
            name="Path Traversal",
            description="檢測可能導致路徑遍歷攻擊的代碼模式"
        )
        
        # 危險的文件操作模式
        self.dangerous_file_patterns = [
            # Python
            r'open\s*\(\s*[^,)]*(?:input|request|args|params)[^,)]*\s*[,)]',
            r'os\.path\.join\s*\([^)]*(?:input|request|args|params)[^)]*\)',
            r'pathlib\.Path\s*\([^)]*(?:input|request|args|params)[^)]*\)',
            
            # JavaScript/Node.js
            r'fs\.(?:readFile|writeFile|open|createReadStream|createWriteStream)\s*\([^,)]*(?:req\.|params|query)[^,)]*',
            r'path\.join\s*\([^)]*(?:req\.|params|query)[^)]*\)',
            
            # Java
            r'new\s+File\s*\([^)]*(?:request\.getParameter|args\[)[^)]*\)',
            r'Files\.(?:read|write|copy|move)\s*\([^,)]*(?:request\.getParameter|args\[)[^,)]*',
            
            # PHP
            r'(?:fopen|file_get_contents|include|require|readfile)\s*\([^)]*\$_(?:GET|POST|REQUEST)[^)]*\)',
            
            # C/C++
            r'fopen\s*\([^,)]*(?:argv\[|getenv)[^,)]*',
        ]
        
        # 路徑遍歷攻擊模式
        self.traversal_patterns = [
            r'\.\./',  # 相對路徑
            r'\.\.\x5c',  # Windows 反斜線
            r'%2e%2e%2f',  # URL 編碼
            r'%2e%2e%5c',  # URL 編碼反斜線
            r'..%2f',  # 混合編碼
            r'..%5c',  # 混合編碼反斜線
        ]
        
        # 路徑驗證模式
        self.path_validation_patterns = [
            r'os\.path\.(?:abspath|realpath|normpath)',
            r'pathlib\.Path\([^)]*\)\.resolve\(\)',
            r'\.(?:startswith|endswith)\s*\(',
            r'(?:validate|sanitize|check).*?path',
            r'path\.(?:normalize|resolve)',
            r'realpath\s*\(',
            r'canonicalize\s*\(',
        ]
    
    def scan_text(self, text: str) -> List[ScanResult]:
        """掃描文本內容"""
        results = []
        lines = text.split('\n')
        total_lines = len(lines)
        
        # 檢查危險的文件操作
        file_op_matches = ScanUtils.find_patterns_in_text(text, self.dangerous_file_patterns)
        
        # 檢查路徑遍歷模式
        traversal_matches = ScanUtils.find_patterns_in_text(text, self.traversal_patterns)
        
        # 檢查路徑驗證
        validation_matches = ScanUtils.find_patterns_in_text(text, self.path_validation_patterns)
        
        # 分析文件操作漏洞
        if file_op_matches:
            for match in file_op_matches:
                # 檢查附近是否有路徑驗證
                line_start = max(0, match['line_number'] - 5)
                line_end = min(total_lines, match['line_number'] + 2)
                context_lines = lines[line_start:line_end]
                context = '\n'.join(context_lines)
                
                has_validation = any(
                    re.search(pattern, context, re.IGNORECASE) 
                    for pattern in self.path_validation_patterns
                )
                
                if not has_validation:
                    confidence = 0.7
                    severity = "High"
                    description = f"檢測到未驗證的文件路徑操作: {match['match']}"
                    
                    results.append(self.create_result(
                        vulnerability_found=True,
                        confidence=confidence,
                        severity=severity,
                        description=description,
                        location=f"第 {match['line_number']} 行",
                        line_number=match['line_number'],
                        evidence=match['match'],
                        mitigation="使用絕對路徑、路徑正規化和白名單驗證來防範路徑遍歷攻擊"
                    ))
        
        # 分析路徑遍歷模式
        if traversal_matches:
            for match in traversal_matches:
                confidence = 0.9
                severity = "Critical"
                description = f"檢測到路徑遍歷攻擊模式: {match['match']}"
                
                results.append(self.create_result(
                    vulnerability_found=True,
                    confidence=confidence,
                    severity=severity,
                    description=description,
                    location=f"第 {match['line_number']} 行",
                    line_number=match['line_number'],
                    evidence=match['match'],
                    mitigation="移除或過濾路徑遍歷字符，使用安全的路徑處理函數"
                ))
        
        # 檢查是否有適當的路徑驗證
        if file_op_matches and not validation_matches:
            results.append(self.create_result(
                vulnerability_found=True,
                confidence=0.6,
                severity="Medium",
                description="代碼中存在文件操作但缺乏路徑驗證機制",
                mitigation="實施路徑驗證和正規化機制"
            ))
        
        # 如果沒有發現問題
        if not results:
            results.append(self.create_result(
                vulnerability_found=False,
                confidence=0.8,
                severity="Low",
                description="未檢測到路徑遍歷漏洞"
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