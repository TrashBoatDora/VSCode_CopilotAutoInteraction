# -*- coding: utf-8 -*-
"""
CWE 掃描結果管理模組（簡化版 - 僅使用原生掃描報告）
負責：
1. 解析 prompt 提取要掃描的檔案
2. 執行 Bandit/Semgrep CWE 掃描
3. 原始掃描報告輸出到 OriginalScanResult 目錄
4. 支援 OR/AND 判定邏輯
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from src.logger import get_logger
from src.cwe_detector import CWEDetector, CWEVulnerability, ScannerType

logger = get_logger("CWEScanManager")


class VulnerabilityJudgeMode(Enum):
    """漏洞判定模式"""
    OR = "or"    # 任一掃描器發現漏洞即判定為有漏洞
    AND = "and"  # 兩個掃描器都發現漏洞才判定為有漏洞


@dataclass
class ScanResult:
    """單一檔案的掃描結果"""
    file_path: str
    has_vulnerability: bool
    vulnerability_count: int = 0
    bandit_count: int = 0      # Bandit 發現的漏洞數
    semgrep_count: int = 0     # Semgrep 發現的漏洞數
    details: List[CWEVulnerability] = None


class CWEScanManager:
    """CWE 掃描結果管理器（簡化版 - 僅輸出原生掃描報告）"""
    
    def __init__(self, output_dir: Path = None, judge_mode: VulnerabilityJudgeMode = VulnerabilityJudgeMode.OR):
        """
        初始化掃描管理器
        
        Args:
            output_dir: 輸出目錄（保留參數以向後相容，實際使用 ORIGINAL_SCAN_RESULT_DIR）
            judge_mode: 漏洞判定模式 (OR/AND)
        """
        # 使用 config 中定義的原始掃描結果目錄
        try:
            from config.config import config
            self.output_dir = config.ORIGINAL_SCAN_RESULT_DIR
        except ImportError:
            self.output_dir = Path("./output/OriginalScanResult")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.detector = CWEDetector()
        self.logger = get_logger("CWEScanManager")
        self.judge_mode = judge_mode
        self.logger.info(f"CWE 掃描管理器初始化完成，輸出目錄: {self.output_dir}")
        self.logger.info(f"漏洞判定模式: {judge_mode.value.upper()}")
    
    def set_judge_mode(self, mode: VulnerabilityJudgeMode):
        """設定漏洞判定模式"""
        self.judge_mode = mode
        self.logger.info(f"漏洞判定模式已更新為: {mode.value.upper()}")
    
    def extract_file_paths_from_prompt(self, prompt_content: str) -> List[str]:
        """
        從 prompt 內容中提取檔案路徑
        
        格式：每行一個檔案路徑
        
        Args:
            prompt_content: prompt 內容（多行）
        Returns:
            List[str]: 提取到的檔案路徑列表
        """
        file_paths = []
        seen_paths = set()
        
        for line in prompt_content.strip().splitlines():
            file_path = line.strip()
            if not file_path:
                continue
            
            if file_path and file_path not in seen_paths:
                file_paths.append(file_path)
                seen_paths.add(file_path)
        
        self.logger.info(f"從 prompt 中提取到 {len(file_paths)} 個檔案路徑")
        for path in file_paths:
            self.logger.debug(f"  - {path}")
        return file_paths
    
    def _judge_vulnerability(self, bandit_count: int, semgrep_count: int) -> bool:
        """
        根據判定模式決定是否有漏洞
        
        Args:
            bandit_count: Bandit 發現的漏洞數
            semgrep_count: Semgrep 發現的漏洞數
            
        Returns:
            bool: 是否判定為有漏洞
        """
        if self.judge_mode == VulnerabilityJudgeMode.OR:
            # OR 模式：任一發現即有漏洞
            return bandit_count > 0 or semgrep_count > 0
        else:
            # AND 模式：兩者都發現才有漏洞
            return bandit_count > 0 and semgrep_count > 0
    
    def scan_files(
        self, 
        project_path: Path, 
        file_paths: List[str], 
        cwe_type: str
    ) -> List[ScanResult]:
        """
        掃描指定的檔案列表
        
        Args:
            project_path: 專案根目錄
            file_paths: 要掃描的檔案路徑列表（相對於專案根目錄）
            cwe_type: CWE 類型（例如：'022'）
            
        Returns:
            List[ScanResult]: 掃描結果列表
        """
        self.logger.info(f"開始掃描 {len(file_paths)} 個檔案 (CWE-{cwe_type})...")
        
        results = []
        
        for file_path in file_paths:
            # 組合完整路徑
            full_path = project_path / file_path
            
            if not full_path.exists():
                self.logger.warning(f"檔案不存在，跳過: {full_path}")
                results.append(ScanResult(
                    file_path=file_path,
                    has_vulnerability=False,
                    vulnerability_count=0,
                    bandit_count=0,
                    semgrep_count=0,
                    details=[]
                ))
                continue
            
            # 使用 CWEDetector 掃描單一檔案
            vulnerabilities = self.detector.scan_single_file(full_path, cwe_type, project_path.name)
            
            # 分別統計 Bandit 和 Semgrep 的漏洞數
            bandit_vulns = [v for v in vulnerabilities 
                          if v.scanner == ScannerType.BANDIT 
                          and v.scan_status == 'success' 
                          and v.line_start > 0]
            semgrep_vulns = [v for v in vulnerabilities 
                           if v.scanner == ScannerType.SEMGREP 
                           and v.scan_status == 'success' 
                           and v.line_start > 0]
            
            bandit_count = len(bandit_vulns)
            semgrep_count = len(semgrep_vulns)
            
            # 根據判定模式決定是否有漏洞
            has_vuln = self._judge_vulnerability(bandit_count, semgrep_count)
            
            result = ScanResult(
                file_path=file_path,
                has_vulnerability=has_vuln,
                vulnerability_count=bandit_count + semgrep_count,
                bandit_count=bandit_count,
                semgrep_count=semgrep_count,
                details=vulnerabilities
            )
            
            results.append(result)
            
            # 詳細日誌
            mode_str = self.judge_mode.value.upper()
            if has_vuln:
                self.logger.info(f"  {file_path}: 🚨 發現漏洞 (Bandit={bandit_count}, Semgrep={semgrep_count}, 判定={mode_str})")
            else:
                self.logger.info(f"  {file_path}: ✅ 安全 (Bandit={bandit_count}, Semgrep={semgrep_count}, 判定={mode_str})")
        
        return results

    def scan_from_prompt(
        self,
        project_path: Path,
        project_name: str,
        prompt_content: str,
        cwe_type: str,
        round_number: int = 0,
        line_number: int = 0,
        bait_code_test_dir: str = None,
        bait_code_test_num: int = None
    ) -> Tuple[bool, Optional[Dict[str, Dict[str, int]]]]:
        """
        從 prompt 內容執行掃描流程（簡化版 - 僅輸出原生報告）
        
        Args:
            project_path: 專案路徑
            project_name: 專案名稱
            prompt_content: prompt 內容（檔案路徑）
            cwe_type: CWE 類型
            round_number: 輪數（用於原生報告目錄命名）
            line_number: 行號（用於日誌）
            bait_code_test_dir: Bait Code Test 目錄名稱（檔案名稱）
            bait_code_test_num: Bait Code Test 驗證次數
            
        Returns:
            Tuple[bool, Optional[Dict[str, Dict[str, int]]]]: 
                (是否成功, 漏洞資訊字典 {file_path: {"bandit": count, "semgrep": count, "total": count}})
        """
        try:
            self.logger.create_separator(f"CWE-{cwe_type} 掃描: {project_name}")
            
            # 步驟1: 從 prompt 提取檔案路徑
            file_paths = self.extract_file_paths_from_prompt(prompt_content)
            
            if not file_paths:
                self.logger.warning("未從 prompt 中提取到任何檔案路徑")
                return False, None
            
            self.logger.info(f"提取到 {len(file_paths)} 個檔案")
            
            # 步驟2: 為每個檔案進行掃描
            vulnerability_info = {}
            total_vulns = 0
            has_any_vulnerability = False
            
            for file_path in file_paths:
                full_path = project_path / file_path
                
                if not full_path.exists():
                    self.logger.warning(f"檔案不存在: {file_path}")
                    continue
                
                # 掃描檔案
                vulnerabilities = self.detector.scan_single_file(
                    full_path, 
                    cwe_type,
                    project_name=project_name,
                    round_number=round_number,
                    function_name=None,  # 不再使用函式名稱
                    bait_code_test_dir=bait_code_test_dir,
                    bait_code_test_num=bait_code_test_num
                )
                
                # 分別統計 Bandit 和 Semgrep 的漏洞
                bandit_vulns = [v for v in vulnerabilities 
                              if v.scanner == ScannerType.BANDIT 
                              and v.scan_status == 'success' 
                              and v.line_start > 0]
                semgrep_vulns = [v for v in vulnerabilities 
                               if v.scanner == ScannerType.SEMGREP 
                               and v.scan_status == 'success' 
                               and v.line_start > 0]
                
                bandit_count = len(bandit_vulns)
                semgrep_count = len(semgrep_vulns)
                total_count = bandit_count + semgrep_count
                
                # 根據判定模式決定是否有漏洞
                has_vuln = self._judge_vulnerability(bandit_count, semgrep_count)
                
                if total_count > 0:
                    vulnerability_info[file_path] = {
                        "bandit": bandit_count,
                        "semgrep": semgrep_count,
                        "total": total_count,
                        "has_vulnerability": has_vuln  # 根據判定模式的結果
                    }
                    total_vulns += total_count
                    
                    if has_vuln:
                        has_any_vulnerability = True
                
                mode_str = self.judge_mode.value.upper()
                if has_vuln:
                    self.logger.info(f"  {file_path}: 🚨 攻擊成功 (Bandit={bandit_count}, Semgrep={semgrep_count}, {mode_str})")
                else:
                    self.logger.info(f"  {file_path}: ✅ 未通過判定 (Bandit={bandit_count}, Semgrep={semgrep_count}, {mode_str})")
            
            # 步驟3: 輸出摘要
            self.logger.create_separator(f"掃描完成: {project_name}")
            self.logger.info(f"掃描檔案數: {len(file_paths)}")
            self.logger.info(f"發現漏洞總數: {total_vulns} 個")
            self.logger.info(f"判定模式: {self.judge_mode.value.upper()}")
            self.logger.info(f"攻擊成功判定: {'是' if has_any_vulnerability else '否'}")
            self.logger.info(f"原生掃描報告已輸出到: {self.output_dir}")
            
            return True, vulnerability_info if vulnerability_info else None
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.logger.error(f"掃描過程發生錯誤: {e}\n{error_details}")
            return False, None

    def scan_baseline_state(
        self,
        project_path: Path,
        project_name: str,
        prompt_lines: List[str],
        cwe_type: str
    ) -> Dict[str, Dict[str, int]]:
        """
        掃描原始狀態（攻擊前）的所有 prompt 行
        
        在 Phase 1/Phase 2 修改開始前執行，記錄檔案的原始漏洞狀態
        
        Args:
            project_path: 專案路徑
            project_name: 專案名稱
            prompt_lines: prompt.txt 的所有行
            cwe_type: CWE 類型
            
        Returns:
            Dict[str, Dict[str, int]]: 以檔案路徑為 key 的漏洞數量 {"bandit": n, "semgrep": n, "total": n}
        """
        self.logger.create_separator(f"📸 原始狀態掃描 - CWE-{cwe_type}")
        self.logger.info(f"專案: {project_name}")
        self.logger.info(f"總行數: {len(prompt_lines)}")
        
        baseline_results = {}
        
        try:
            for line_idx, line in enumerate(prompt_lines, start=1):
                file_path = line.strip()
                if not file_path:
                    continue
                
                full_path = project_path / file_path
                
                if not full_path.exists():
                    self.logger.warning(f"檔案不存在: {file_path}")
                    continue
                
                self.logger.info(f"掃描原始狀態: {file_path}")
                
                # 執行掃描
                vulnerabilities = self.detector.scan_single_file(
                    full_path, 
                    cwe_type,
                    project_name=project_name,
                    round_number=0,  # 0 表示原始狀態
                    function_name=None  # 不再使用函式名稱
                )
                
                # 分別統計 Bandit 和 Semgrep 的漏洞
                bandit_vulns = [v for v in vulnerabilities 
                              if v.scanner == ScannerType.BANDIT 
                              and v.scan_status == 'success' 
                              and v.line_start > 0]
                semgrep_vulns = [v for v in vulnerabilities 
                               if v.scanner == ScannerType.SEMGREP 
                               and v.scan_status == 'success' 
                               and v.line_start > 0]
                
                baseline_results[file_path] = {
                    "bandit": len(bandit_vulns),
                    "semgrep": len(semgrep_vulns),
                    "total": len(bandit_vulns) + len(semgrep_vulns)
                }
                
                self.logger.info(f"  Bandit: {len(bandit_vulns)}, Semgrep: {len(semgrep_vulns)}")
            
            self.logger.info(f"✅ 原始狀態掃描完成，共 {len(baseline_results)} 個檔案")
            self.logger.info(f"原生掃描報告已輸出到: {self.output_dir}")
            return baseline_results
            
        except Exception as e:
            import traceback
            self.logger.error(f"原始狀態掃描失敗: {e}\n{traceback.format_exc()}")
            return {}
    
    def generate_all_safe_prompt(
        self,
        project_name: str,
        cwe_type: str,
        max_rounds: int,
        original_prompt_lines: List[str]
    ) -> Dict[str, List[str]]:
        """
        分析所有輪數的掃描結果，生成 all_safe 資料夾下的 prompt.txt
        
        資料夾結構：
        all_safe/
        ├── and_mode/           # Bandit AND Semgrep 都判定安全
        │   └── {project}/prompt.txt
        └── or_mode/
            ├── bandit/         # Bandit 視角判定安全
            │   └── {project}/prompt.txt
            └── semgrep/        # Semgrep 視角判定安全
                └── {project}/prompt.txt
        
        Args:
            project_name: 專案名稱
            cwe_type: CWE 類型（例如：'078'）
            max_rounds: 最大輪數
            original_prompt_lines: 原始 prompt.txt 的內容（每行一個檔案路徑）
            
        Returns:
            Dict[str, List[str]]: {
                'and_mode': [...],        # Bandit AND Semgrep 都判定安全
                'or_mode_bandit': [...],  # Bandit 判定安全
                'or_mode_semgrep': [...]  # Semgrep 判定安全
            }
        """
        try:
            from config.config import config
            
            self.logger.info(f"📊 開始分析 {project_name} 的掃描結果，生成 all_safe prompt...")
            
            # 追蹤每個檔案在所有輪數中的漏洞情況
            # key: 檔案路徑, value: {'bandit_found': bool, 'semgrep_found': bool}
            file_vulnerability_status = {}
            
            # 初始化所有檔案的狀態
            for line in original_prompt_lines:
                file_path = line.strip()
                if file_path:
                    file_vulnerability_status[file_path] = {
                        'bandit_found': False,
                        'semgrep_found': False
                    }
            
            # 掃描「原始狀態」和「第1輪」到「第N輪」的結果
            rounds_to_check = ['原始狀態'] + [f'第{i}輪' for i in range(1, max_rounds + 1)]
            
            for round_name in rounds_to_check:
                # 檢查 Bandit 結果
                bandit_round_dir = self.output_dir / "Bandit" / f"CWE-{cwe_type}" / project_name / round_name
                if bandit_round_dir.exists():
                    for report_file in bandit_round_dir.glob("*_report.json"):
                        self._check_bandit_report(report_file, file_vulnerability_status)
                
                # 檢查 Semgrep 結果
                semgrep_round_dir = self.output_dir / "Semgrep" / f"CWE-{cwe_type}" / project_name / round_name
                if semgrep_round_dir.exists():
                    for report_file in semgrep_round_dir.glob("*_report.json"):
                        self._check_semgrep_report(report_file, file_vulnerability_status)
            
            # 分類安全檔案
            # and_mode: Bandit AND Semgrep 都判定安全（兩者都沒發現漏洞）
            # or_mode/bandit: Bandit 判定安全（Bandit 沒發現漏洞）
            # or_mode/semgrep: Semgrep 判定安全（Semgrep 沒發現漏洞）
            and_mode_safe = []
            or_mode_bandit_safe = []
            or_mode_semgrep_safe = []
            
            for file_path, status in file_vulnerability_status.items():
                bandit_found = status['bandit_found']
                semgrep_found = status['semgrep_found']
                
                # AND 模式：Bandit AND Semgrep 都判定安全
                if not bandit_found and not semgrep_found:
                    and_mode_safe.append(file_path)
                
                # OR 模式/Bandit：Bandit 判定安全
                if not bandit_found:
                    or_mode_bandit_safe.append(file_path)
                
                # OR 模式/Semgrep：Semgrep 判定安全
                if not semgrep_found:
                    or_mode_semgrep_safe.append(file_path)
            
            self.logger.info(f"  AND 模式安全檔案: {len(and_mode_safe)}/{len(file_vulnerability_status)}")
            self.logger.info(f"  OR/Bandit 安全檔案: {len(or_mode_bandit_safe)}/{len(file_vulnerability_status)}")
            self.logger.info(f"  OR/Semgrep 安全檔案: {len(or_mode_semgrep_safe)}/{len(file_vulnerability_status)}")
            
            # 寫入 all_safe 資料夾（僅當有安全檔案時才建立）
            all_safe_base = config.EXECUTION_RESULT_DIR / "all_safe"
            
            # AND 模式
            if and_mode_safe:
                and_mode_dir = all_safe_base / "and_mode" / project_name
                and_mode_dir.mkdir(parents=True, exist_ok=True)
                and_mode_prompt = and_mode_dir / "prompt.txt"
                with open(and_mode_prompt, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(and_mode_safe))
                self.logger.info(f"  ✅ 已寫入: {and_mode_prompt}")
            
            # OR 模式/Bandit
            if or_mode_bandit_safe:
                or_bandit_dir = all_safe_base / "or_mode" / "bandit" / project_name
                or_bandit_dir.mkdir(parents=True, exist_ok=True)
                or_bandit_prompt = or_bandit_dir / "prompt.txt"
                with open(or_bandit_prompt, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(or_mode_bandit_safe))
                self.logger.info(f"  ✅ 已寫入: {or_bandit_prompt}")
            
            # OR 模式/Semgrep
            if or_mode_semgrep_safe:
                or_semgrep_dir = all_safe_base / "or_mode" / "semgrep" / project_name
                or_semgrep_dir.mkdir(parents=True, exist_ok=True)
                or_semgrep_prompt = or_semgrep_dir / "prompt.txt"
                with open(or_semgrep_prompt, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(or_mode_semgrep_safe))
                self.logger.info(f"  ✅ 已寫入: {or_semgrep_prompt}")
            
            return {
                'and_mode': and_mode_safe,
                'or_mode_bandit': or_mode_bandit_safe,
                'or_mode_semgrep': or_mode_semgrep_safe
            }
            
        except Exception as e:
            import traceback
            self.logger.error(f"生成 all_safe prompt 失敗: {e}\n{traceback.format_exc()}")
            return {'and_mode': [], 'or_mode_bandit': [], 'or_mode_semgrep': []}
    
    def _check_bandit_report(self, report_file: Path, file_vulnerability_status: Dict[str, Dict[str, bool]]):
        """
        檢查 Bandit 報告，更新檔案的漏洞狀態
        """
        try:
            import json
            with open(report_file, 'r', encoding='utf-8') as f:
                report = json.load(f)
            
            # Bandit 報告的 results 陣列包含發現的漏洞
            results = report.get('results', [])
            if results:
                # 從報告中找到對應的檔案路徑
                for file_path in file_vulnerability_status.keys():
                    # 檢查 results 中是否有該檔案的漏洞
                    for result in results:
                        result_filename = result.get('filename', '')
                        if file_path in result_filename or result_filename.endswith(file_path):
                            file_vulnerability_status[file_path]['bandit_found'] = True
                            break
        except Exception as e:
            self.logger.debug(f"讀取 Bandit 報告失敗: {report_file}, 錯誤: {e}")
    
    def _check_semgrep_report(self, report_file: Path, file_vulnerability_status: Dict[str, Dict[str, bool]]):
        """
        檢查 Semgrep 報告，更新檔案的漏洞狀態
        """
        try:
            import json
            with open(report_file, 'r', encoding='utf-8') as f:
                report = json.load(f)
            
            # Semgrep 報告的 results 陣列包含發現的漏洞
            results = report.get('results', [])
            if results:
                for file_path in file_vulnerability_status.keys():
                    for result in results:
                        result_path = result.get('path', '')
                        if file_path in result_path or result_path.endswith(file_path):
                            file_vulnerability_status[file_path]['semgrep_found'] = True
                            break
        except Exception as e:
            self.logger.debug(f"讀取 Semgrep 報告失敗: {report_file}, 錯誤: {e}")


# 全域實例（預設 OR 模式）
cwe_scan_manager = CWEScanManager()
