"""
CWE-400: 不受控制的資源消耗掃描器
檢測可能導致拒絕服務攻擊的代碼模式
"""

from typing import List
from cwe_base import CWEScanner, ScanResult, ScanUtils
import re


class CWE400Scanner(CWEScanner):
    """CWE-400: 不受控制的資源消耗掃描器"""
    
    def __init__(self):
        super().__init__(
            cwe_id="CWE-400",
            name="Uncontrolled Resource Consumption",
            description="檢測可能導致拒絕服務攻擊的代碼模式"
        )
        
        # 危險的循環模式
        self.dangerous_loop_patterns = [
            # 無限循環或大循環
            r'while\s+True\s*:(?!\s*#.*?timeout|break)',
            r'for\s+\w+\s+in\s+range\s*\(\s*(?:int\s*\()?(?:input|request|params)',
            r'while\s+[^:]*(?:input|request|params)[^:]*:',
            
            # 遞迴調用
            r'def\s+(\w+).*?:\s*.*?\1\s*\(',  # 可能的遞迴函數
        ]
        
        # 危險的記憶體分配
        self.memory_allocation_patterns = [
            # Python
            r'list\s*\(\s*range\s*\([^)]*(?:input|request|params)',
            r'\[\s*0\s*\]\s*\*\s*(?:int\s*\()?(?:input|request|params)',
            r'bytearray\s*\([^)]*(?:input|request|params)',
            
            # JavaScript
            r'new\s+Array\s*\([^)]*(?:req\.|params|query)',
            r'Buffer\.alloc\s*\([^)]*(?:req\.|params|query)',
            
            # Java
            r'new\s+\w+\[\s*(?:Integer\.parseInt\s*\()?request\.getParameter',
            r'ArrayList\s*\([^)]*(?:Integer\.parseInt\s*\()?request\.getParameter',
        ]
        
        # 檔案操作模式
        self.file_operation_patterns = [
            r'open\s*\([^)]*(?:input|request|params)[^)]*\)\.read\s*\(\s*\)',
            r'file\.read\s*\(\s*(?:int\s*\()?(?:input|request|params)',
            r'readlines\s*\(\s*(?:int\s*\()?(?:input|request|params)',
        ]
        
        # 網路操作模式
        self.network_patterns = [
            r'requests\.get\s*\([^)]*(?:input|request|params)',
            r'urllib\.request\.urlopen\s*\([^)]*(?:input|request|params)',
            r'socket\.connect\s*\([^)]*(?:input|request|params)',
        ]
        
        # 保護措施模式
        self.protection_patterns = [
            r'timeout\s*=',
            r'max_size\s*=',
            r'limit\s*=',
            r'if\s+len\s*\([^)]*\)\s*>\s*\d+',
            r'raise\s+.*?(?:Timeout|Limit|Size)Error',
            r'signal\.alarm\s*\(',
            r'threading\.Timer\s*\(',
        ]
    
    def scan_text(self, text: str) -> List[ScanResult]:
        """掃描文本內容"""
        results = []
        lines = text.split('\n')
        total_lines = len(lines)
        
        # 檢查危險的循環
        loop_matches = ScanUtils.find_patterns_in_text(text, self.dangerous_loop_patterns)
        
        # 檢查記憶體分配
        memory_matches = ScanUtils.find_patterns_in_text(text, self.memory_allocation_patterns)
        
        # 檢查檔案操作
        file_matches = ScanUtils.find_patterns_in_text(text, self.file_operation_patterns)
        
        # 檢查網路操作
        network_matches = ScanUtils.find_patterns_in_text(text, self.network_patterns)
        
        # 檢查保護措施
        protection_matches = ScanUtils.find_patterns_in_text(text, self.protection_patterns)
        
        # 分析危險循環
        if loop_matches:
            for match in loop_matches:
                confidence = 0.7
                severity = "High"
                description = f"檢測到潛在的無限循環或大循環: {match['match']}"
                
                results.append(self.create_result(
                    vulnerability_found=True,
                    confidence=confidence,
                    severity=severity,
                    description=description,
                    location=f"第 {match['line_number']} 行",
                    line_number=match['line_number'],
                    evidence=match['match'],
                    mitigation="設定循環限制、超時機制或輸入驗證"
                ))
        
        # 分析記憶體分配
        if memory_matches:
            for match in memory_matches:
                confidence = 0.8
                severity = "High"
                description = f"檢測到不受控制的記憶體分配: {match['match']}"
                
                results.append(self.create_result(
                    vulnerability_found=True,
                    confidence=confidence,
                    severity=severity,
                    description=description,
                    location=f"第 {match['line_number']} 行",
                    line_number=match['line_number'],
                    evidence=match['match'],
                    mitigation="限制記憶體分配大小，驗證輸入範圍"
                ))
        
        # 分析檔案操作
        if file_matches:
            for match in file_matches:
                confidence = 0.6
                severity = "Medium"
                description = f"檢測到不受限制的檔案讀取: {match['match']}"
                
                results.append(self.create_result(
                    vulnerability_found=True,
                    confidence=confidence,
                    severity=severity,
                    description=description,
                    location=f"第 {match['line_number']} 行",
                    line_number=match['line_number'],
                    evidence=match['match'],
                    mitigation="限制檔案讀取大小和設定超時"
                ))
        
        # 分析網路操作
        if network_matches:
            for match in network_matches:
                confidence = 0.6
                severity = "Medium"
                description = f"檢測到不受限制的網路請求: {match['match']}"
                
                results.append(self.create_result(
                    vulnerability_found=True,
                    confidence=confidence,
                    severity=severity,
                    description=description,
                    location=f"第 {match['line_number']} 行",
                    line_number=match['line_number'],
                    evidence=match['match'],
                    mitigation="設定請求超時和大小限制"
                ))
        
        # 檢查是否有保護措施
        if protection_matches and (loop_matches or memory_matches or file_matches):
            results.append(self.create_result(
                vulnerability_found=False,
                confidence=0.7,
                severity="Low",
                description="檢測到資源保護措施"
            ))
        
        # 如果沒有發現問題
        if not results:
            results.append(self.create_result(
                vulnerability_found=False,
                confidence=0.8,
                severity="Low",
                description="未檢測到資源消耗漏洞"
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