"""
CWE 掃描器基礎類別
定義所有 CWE 掃描器的統一接口和通用功能
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re
import ast
import os


@dataclass
class ScanResult:
    """掃描結果數據類別"""
    cwe_id: str
    vulnerability_found: bool
    confidence: float  # 0.0 - 1.0
    severity: str  # "Low", "Medium", "High", "Critical"
    description: str
    location: Optional[str] = None
    line_number: Optional[int] = None
    evidence: Optional[str] = None
    mitigation: Optional[str] = None


class CWEScanner(ABC):
    """CWE 掃描器抽象基類"""
    
    def __init__(self, cwe_id: str, name: str, description: str):
        self.cwe_id = cwe_id
        self.name = name
        self.description = description
        self.severity_mapping = {
            "Low": 1,
            "Medium": 2, 
            "High": 3,
            "Critical": 4
        }
    
    @abstractmethod
    def scan_text(self, text: str) -> List[ScanResult]:
        """掃描文本內容"""
        pass
    
    @abstractmethod
    def scan_file(self, file_path: str) -> List[ScanResult]:
        """掃描單個文件"""
        pass
    
    def scan_directory(self, directory_path: str, file_extensions: List[str] = None) -> List[ScanResult]:
        """掃描目錄下的所有相關文件"""
        results = []
        
        if file_extensions is None:
            file_extensions = ['.py', '.java', '.js', '.ts', '.php', '.cpp', '.c', '.cs']
        
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if any(file.endswith(ext) for ext in file_extensions):
                    file_path = os.path.join(root, file)
                    try:
                        file_results = self.scan_file(file_path)
                        results.extend(file_results)
                    except Exception as e:
                        # 記錄錯誤但繼續掃描其他文件
                        print(f"Error scanning {file_path}: {str(e)}")
        
        return results
    
    def create_result(self, vulnerability_found: bool, confidence: float, 
                     severity: str, description: str, **kwargs) -> ScanResult:
        """創建掃描結果的輔助方法"""
        return ScanResult(
            cwe_id=self.cwe_id,
            vulnerability_found=vulnerability_found,
            confidence=confidence,
            severity=severity,
            description=description,
            **kwargs
        )


class ScanUtils:
    """掃描工具類，提供通用的掃描輔助方法"""
    
    @staticmethod
    def find_patterns_in_text(text: str, patterns: List[str], case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """在文本中查找模式匹配"""
        matches = []
        flags = 0 if case_sensitive else re.IGNORECASE
        
        for pattern in patterns:
            for match in re.finditer(pattern, text, flags):
                matches.append({
                    'pattern': pattern,
                    'match': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'line_number': text[:match.start()].count('\n') + 1
                })
        
        return matches
    
    @staticmethod
    def extract_function_calls(code: str, language: str = 'python') -> List[Dict[str, Any]]:
        """提取程式碼中的函數調用"""
        function_calls = []
        
        if language.lower() == 'python':
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name):
                            function_calls.append({
                                'name': node.func.id,
                                'line_number': node.lineno,
                                'args_count': len(node.args),
                                'keywords': [kw.arg for kw in node.keywords]
                            })
                        elif isinstance(node.func, ast.Attribute):
                            function_calls.append({
                                'name': node.func.attr,
                                'line_number': node.lineno,
                                'args_count': len(node.args),
                                'keywords': [kw.arg for kw in node.keywords]
                            })
            except SyntaxError:
                # 如果代碼有語法錯誤，使用正則表達式作為後備
                pattern = r'(\w+)\s*\('
                for match in re.finditer(pattern, code):
                    line_number = code[:match.start()].count('\n') + 1
                    function_calls.append({
                        'name': match.group(1),
                        'line_number': line_number,
                        'args_count': -1,  # 未知
                        'keywords': []
                    })
        
        return function_calls
    
    @staticmethod
    def extract_imports(code: str, language: str = 'python') -> List[Dict[str, Any]]:
        """提取程式碼中的導入語句"""
        imports = []
        
        if language.lower() == 'python':
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append({
                                'type': 'import',
                                'module': alias.name,
                                'alias': alias.asname,
                                'line_number': node.lineno
                            })
                    elif isinstance(node, ast.ImportFrom):
                        for alias in node.names:
                            imports.append({
                                'type': 'from_import',
                                'module': node.module,
                                'name': alias.name,
                                'alias': alias.asname,
                                'line_number': node.lineno
                            })
            except SyntaxError:
                # 使用正則表達式作為後備
                import_patterns = [
                    r'import\s+(\w+(?:\.\w+)*)',
                    r'from\s+(\w+(?:\.\w+)*)\s+import\s+(\w+)'
                ]
                for pattern in import_patterns:
                    for match in re.finditer(pattern, code):
                        line_number = code[:match.start()].count('\n') + 1
                        imports.append({
                            'type': 'import',
                            'module': match.group(1),
                            'line_number': line_number
                        })
        
        return imports
    
    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """獲取文件擴展名"""
        return os.path.splitext(file_path)[1].lower()
    
    @staticmethod
    def read_file_safely(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
        """安全地讀取文件內容"""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception:
                return None
        except Exception:
            return None
    
    @staticmethod
    def calculate_confidence(matches_count: int, total_lines: int, pattern_strength: float = 0.7) -> float:
        """計算檢測置信度"""
        if total_lines == 0:
            return 0.0
        
        density = matches_count / total_lines
        confidence = min(density * pattern_strength * 10, 1.0)
        return round(confidence, 2)