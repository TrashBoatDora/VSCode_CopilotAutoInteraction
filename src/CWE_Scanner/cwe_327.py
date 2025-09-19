"""
CWE-327: 使用已遭破解或有風險的加密演算法掃描器
檢測使用弱加密演算法的代碼模式
"""

from typing import List
from cwe_base import CWEScanner, ScanResult, ScanUtils
import re


class CWE327Scanner(CWEScanner):
    """CWE-327: 使用已遭破解或有風險的加密演算法掃描器"""
    
    def __init__(self):
        super().__init__(
            cwe_id="CWE-327",
            name="Use of Broken or Risky Cryptographic Algorithm",
            description="檢測使用弱加密演算法的代碼模式"
        )
        
        # 弱加密演算法模式
        self.weak_crypto_patterns = [
            # 弱雜湊演算法
            r'hashlib\.md5\s*\(',
            r'hashlib\.sha1\s*\(',
            r'Crypto\.Hash\.MD5',
            r'Crypto\.Hash\.SHA1',
            r'MessageDigest\.getInstance\s*\(\s*["\'](?:MD5|SHA-?1)["\']',
            
            # 弱對稱加密
            r'Crypto\.Cipher\.DES',
            r'Crypto\.Cipher\.ARC4',
            r'Cipher\.getInstance\s*\(\s*["\']DES',
            r'Cipher\.getInstance\s*\(\s*["\']RC4',
            
            # 弱非對稱加密
            r'RSA.*?keysize.*?512',
            r'RSA.*?keysize.*?1024',
            r'generate_key\s*\(\s*512',
            r'generate_key\s*\(\s*1024',
            
            # 其他弱演算法
            r'crypt\s*\(',  # Unix crypt
            r'CRC32',
            r'Adler32',
        ]
        
        # 強加密演算法模式
        self.strong_crypto_patterns = [
            # 強雜湊演算法
            r'hashlib\.sha256\s*\(',
            r'hashlib\.sha384\s*\(',
            r'hashlib\.sha512\s*\(',
            r'hashlib\.sha3_256\s*\(',
            r'hashlib\.blake2b\s*\(',
            r'Crypto\.Hash\.SHA256',
            r'Crypto\.Hash\.SHA384',
            r'Crypto\.Hash\.SHA512',
            
            # 強對稱加密
            r'Crypto\.Cipher\.AES',
            r'Crypto\.Cipher\.ChaCha20',
            r'Cipher\.getInstance\s*\(\s*["\']AES',
            
            # 強非對稱加密
            r'RSA.*?keysize.*?(?:2048|3072|4096)',
            r'generate_key\s*\(\s*(?:2048|3072|4096)',
            r'Ed25519',
            r'X25519',
        ]
        
        # 密碼學庫導入
        self.crypto_imports = [
            r'import\s+hashlib',
            r'from\s+Crypto',
            r'import\s+cryptography',
            r'import\s+javax\.crypto',
            r'import\s+java\.security',
        ]
    
    def scan_text(self, text: str) -> List[ScanResult]:
        """掃描文本內容"""
        results = []
        
        # 檢查弱加密演算法
        weak_matches = ScanUtils.find_patterns_in_text(text, self.weak_crypto_patterns)
        
        # 檢查強加密演算法
        strong_matches = ScanUtils.find_patterns_in_text(text, self.strong_crypto_patterns)
        
        # 檢查密碼學庫導入
        import_matches = ScanUtils.find_patterns_in_text(text, self.crypto_imports)
        
        # 分析弱加密演算法
        if weak_matches:
            for match in weak_matches:
                confidence = 0.9
                
                # 根據演算法類型設定嚴重性
                if any(alg in match['match'].lower() for alg in ['md5', 'sha1']):
                    severity = "High"
                    description = f"檢測到弱雜湊演算法: {match['match']}"
                elif any(alg in match['match'].lower() for alg in ['des', 'rc4']):
                    severity = "Critical"
                    description = f"檢測到弱對稱加密演算法: {match['match']}"
                elif any(size in match['match'] for size in ['512', '1024']):
                    severity = "High"
                    description = f"檢測到弱金鑰長度: {match['match']}"
                else:
                    severity = "Medium"
                    description = f"檢測到可能的弱加密: {match['match']}"
                
                results.append(self.create_result(
                    vulnerability_found=True,
                    confidence=confidence,
                    severity=severity,
                    description=description,
                    location=f"第 {match['line_number']} 行",
                    line_number=match['line_number'],
                    evidence=match['match'],
                    mitigation="使用強加密演算法如 SHA-256、AES、RSA-2048 或更高"
                ))
        
        # 檢查是否有加密但沒有使用弱演算法
        if import_matches and strong_matches and not weak_matches:
            results.append(self.create_result(
                vulnerability_found=False,
                confidence=0.8,
                severity="Low",
                description="檢測到使用強加密演算法"
            ))
        
        # 如果有加密庫導入但沒有明確的加密使用
        if import_matches and not (weak_matches or strong_matches):
            results.append(self.create_result(
                vulnerability_found=False,
                confidence=0.5,
                severity="Low",
                description="檢測到加密庫導入但未發現具體使用"
            ))
        
        # 如果沒有發現任何加密相關內容
        if not results:
            results.append(self.create_result(
                vulnerability_found=False,
                confidence=0.9,
                severity="Low",
                description="未檢測到加密演算法使用"
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