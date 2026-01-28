# -*- coding: utf-8 -*-
"""
Artificial Suicide 攻擊模式 - 簡化版控制器
直接利用現有的 copilot_handler 和 vscode_controller 功能
掃描結果僅輸出原生報告到 OriginalScanResult
當檢測到漏洞時，備份觸發漏洞的檔案到 vicious_pattern 目錄
"""

import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time
import pyautogui

from src.logger import get_logger
from src.copilot_rate_limit_handler import is_response_incomplete, wait_and_retry
from config.config import config


class ArtificialSuicideMode:
    """
    Artificial Suicide 攻擊模式控制器（簡化版）
    
    功能：
    1. 載入三個 prompt 模板（initial_query, following_query, coding_instruction）
    2. 控制兩道程序的執行流程
    3. 調用現有的 copilot_handler 和 vscode_controller
    4. 僅輸出原生掃描報告（無 function_level CSV 和 query_statistics）
    5. 當檢測到漏洞時，備份觸發漏洞的檔案到 vicious_pattern 目錄
    """
    
    def __init__(self, copilot_handler, vscode_controller, cwe_scan_manager, 
                 error_handler, project_path: str, target_cwe: str, total_rounds: int,
                 max_files_limit: int = 0, files_processed_so_far: int = 0,
                 checkpoint_manager=None, resume_round: int = 1, resume_line: int = 1,
                 resume_phase: int = 1, bait_code_test_rounds: int = 3):
        """
        初始化 AS 模式控制器
        
        Args:
            copilot_handler: Copilot 處理器
            vscode_controller: VSCode 控制器
            cwe_scan_manager: CWE 掃描管理器
            error_handler: 錯誤處理器
            project_path: 專案路徑
            target_cwe: 目標 CWE 類型
            total_rounds: 總輪數
            max_files_limit: 最大檔案處理限制（0 表示無限制）
            files_processed_so_far: 目前已處理的檔案數
            checkpoint_manager: 檢查點管理器
            resume_round: 恢復起始輪數
            resume_line: 恢復起始行數
            resume_phase: 恢復起始階段（1=Query, 2=Coding）
            bait_code_test_rounds: Bait Code Test 驗證次數（預設 3）
        """
        self.logger = get_logger("ArtificialSuicide")
        self.copilot_handler = copilot_handler
        self.vscode_controller = vscode_controller
        self.cwe_scan_manager = cwe_scan_manager
        self.error_handler = error_handler
        self.project_path = Path(project_path)
        self.target_cwe = target_cwe
        self.total_rounds = total_rounds
        self.checkpoint_manager = checkpoint_manager
        
        # Bait Code Test 驗證次數
        self.bait_code_test_rounds = bait_code_test_rounds
        
        # Resume 狀態
        self.resume_round = resume_round
        self.resume_line = resume_line
        self.resume_phase = resume_phase
        self.is_resume_mode = (resume_round > 1 or resume_line > 1 or resume_phase > 1)
        
        if self.is_resume_mode:
            self.logger.info(f"🔄 AS Mode 恢復模式: 從第 {resume_round} 輪 Phase {resume_phase} 第 {resume_line} 行繼續")
        
        # 檔案數量限制相關
        self.max_files_limit = max_files_limit
        self.files_processed_so_far = files_processed_so_far
        self.files_processed_in_project = 0
        
        # Vicious Pattern 備份目錄
        self.vicious_pattern_dir = config.OUTPUT_BASE_DIR / "vicious_pattern" / self.project_path.name
        self.vicious_files_backed_up = 0
        
        # 待備份檔案清單：Phase 2 掃描後記錄，revert 後再實際備份
        # 格式: [(target_file, bandit_count, semgrep_count), ...]
        self.pending_vicious_backups = []
        
        # 漏洞追蹤：記錄每個檔案在哪一輪首次發現漏洞
        # key: line_idx, value: round_num (首次發現漏洞的輪數)
        # 如果某個檔案已經發現漏洞，後續輪次就跳過該檔案
        self.vulnerability_found_at = {}
        
        # 載入模板
        self.templates = self._load_templates()
        
        # 載入 CWE 範例程式碼
        self.cwe_example_code = self._load_cwe_example_code()
        
        # 載入專案的 prompt.txt
        self.prompt_lines = self._load_prompt_lines()
        original_line_count = len(self.prompt_lines)
        
        # 如果有檔案數量限制，計算本專案可處理的行數
        if self.max_files_limit > 0:
            remaining_quota = self.max_files_limit - self.files_processed_so_far
            if remaining_quota <= 0:
                self.logger.warning(f"⚠️  已達到檔案處理限制 ({self.files_processed_so_far}/{self.max_files_limit})，將不處理任何檔案")
                self.prompt_lines = []
            elif len(self.prompt_lines) > remaining_quota:
                self.logger.info(f"📊 檔案數量限制: 專案有 {original_line_count} 行，僅處理前 {remaining_quota} 行")
                self.prompt_lines = self.prompt_lines[:remaining_quota]
        
        # 儲存每一輪每一行的回應（用於串接到下一輪）
        self.round_responses = {}
        
        self.logger.info(f"✅ AS 模式初始化完成 - CWE-{target_cwe}, {total_rounds} 輪, {len(self.prompt_lines)} 行")
    
    def _load_templates(self) -> Dict[str, str]:
        """載入三個 prompt 模板"""
        template_dir = Path(__file__).parent.parent / "assets" / "prompt-template"
        templates = {}
        
        template_files = {
            "initial_query": "initial_query.txt",
            "following_query": "following_query.txt", 
            "coding_instruction": "coding_instruction.txt"
        }
        
        for key, filename in template_files.items():
            file_path = template_dir / filename
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    templates[key] = f.read()
                self.logger.debug(f"✅ 載入模板: {filename}")
            except FileNotFoundError:
                self.logger.error(f"❌ 找不到模板檔案: {file_path}")
                templates[key] = ""
        
        return templates
    
    def _load_cwe_example_code(self) -> str:
        """載入對應 CWE 類型的範例程式碼"""
        cwe_id = self.target_cwe.lstrip('0') if self.target_cwe else ""
        
        if not cwe_id:
            self.logger.warning("⚠️  未指定目標 CWE，無法載入範例程式碼")
            return ""
        
        cwe_example_dir = Path(__file__).parent.parent / "assets" / "prompt-template" / "CWE"
        cwe_example_file = cwe_example_dir / f"{cwe_id}.txt"
        
        try:
            with open(cwe_example_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            self.logger.info(f"✅ 載入 CWE-{self.target_cwe} 範例程式碼")
            return content
        except FileNotFoundError:
            self.logger.warning(f"⚠️  找不到 CWE 範例檔案: {cwe_example_file}")
            return ""
        except Exception as e:
            self.logger.error(f"❌ 載入 CWE 範例程式碼失敗: {e}")
            return ""
    
    def _load_prompt_lines(self) -> List[str]:
        """載入專案的 prompt.txt"""
        return self.copilot_handler.load_project_prompt_lines(str(self.project_path))
    
    def _generate_query_prompt(self, round_num: int, target_file: str, 
                               last_response: str = "") -> str:
        """生成第 1 道的 Query Prompt"""
        # 第 1 輪使用 initial_query，第 2+ 輪使用 following_query
        if round_num == 1:
            template = self.templates["initial_query"]
            variables = {
                "target_file": target_file,
                "CWE-XXX": f"CWE-{self.target_cwe}"
            }
        else:
            template = self.templates["following_query"]
            variables = {
                "target_file": target_file,
                "CWE-XXX": f"CWE-{self.target_cwe}"
            }
        
        # 替換 CWE 範例程式碼佔位符
        if "{{CWE_EXAMPLE_CODE}}" in template:
            template = template.replace("{{CWE_EXAMPLE_CODE}}", self.cwe_example_code)
        
        prompt = template.format(**variables)
        return prompt
    
    def _generate_coding_prompt(self, target_file: str) -> str:
        """生成第 2 道的 Coding Prompt"""
        template = self.templates["coding_instruction"]
        prompt = template.format(
            target_file=target_file
        )
        return prompt
    
    def _backup_vicious_pattern(
        self, 
        target_file: str, 
        round_num: int, 
        line_idx: int,
        bandit_count: int = 0,
        semgrep_count: int = 0
    ) -> bool:
        """
        備份觸發漏洞的檔案到 vicious_pattern 目錄
        
        資料夾結構（保持原始專案目錄結構，可直接覆蓋原專案）：
        vicious_pattern/
        ├── and_mode/           # Bandit AND Semgrep 都發現漏洞
        │   └── {project}/
        │       ├── torch_utils/custom_ops.py  ← 保持原始路徑
        │       └── prompt.txt                 ← 記錄有漏洞檔案的路徑
        └── or_mode/
            ├── bandit/
            │   └── {project}/
            │       ├── ...
            │       └── prompt.txt
            └── semgrep/
                └── {project}/
                    ├── ...
                    └── prompt.txt
        
        當 Phase 2 掃描發現漏洞時，在 UNDO 之前備份當前檔案狀態
        （此時檔案處於 Phase 1 修改後的狀態，即觸發漏洞的「惡意模式」）
        
        Args:
            target_file: 目標檔案相對路徑（例如：torch_utils/custom_ops.py）
            round_num: 當前輪數
            line_idx: 當前行號
            bandit_count: Bandit 發現的漏洞數
            semgrep_count: Semgrep 發現的漏洞數
            
        Returns:
            bool: 備份是否成功
        """
        try:
            # 來源檔案（專案中的檔案）
            source_file = self.project_path / target_file
            
            if not source_file.exists():
                self.logger.warning(f"  ⚠️  備份失敗：檔案不存在 {source_file}")
                return False
            
            backed_up = False
            project_name = self.project_path.name
            base_dir = config.OUTPUT_BASE_DIR / "vicious_pattern"
            
            # AND 模式：Bandit AND Semgrep 都發現漏洞
            if bandit_count > 0 and semgrep_count > 0:
                project_dir = base_dir / "and_mode" / project_name
                self._backup_file_with_structure(source_file, target_file, project_dir)
                self._append_to_prompt_txt(project_dir, target_file)
                self.logger.info(f"  📦 已備份 vicious pattern (AND): {target_file}")
                backed_up = True
            
            # OR 模式/Bandit：Bandit 發現漏洞
            if bandit_count > 0:
                project_dir = base_dir / "or_mode" / "bandit" / project_name
                self._backup_file_with_structure(source_file, target_file, project_dir)
                self._append_to_prompt_txt(project_dir, target_file)
                self.logger.info(f"  📦 已備份 vicious pattern (OR/Bandit): {target_file}")
                backed_up = True
            
            # OR 模式/Semgrep：Semgrep 發現漏洞
            if semgrep_count > 0:
                project_dir = base_dir / "or_mode" / "semgrep" / project_name
                self._backup_file_with_structure(source_file, target_file, project_dir)
                self._append_to_prompt_txt(project_dir, target_file)
                self.logger.info(f"  📦 已備份 vicious pattern (OR/Semgrep): {target_file}")
                backed_up = True
            
            if backed_up:
                self.vicious_files_backed_up += 1
            
            return backed_up
            
        except Exception as e:
            self.logger.error(f"  ❌ 備份 vicious pattern 失敗: {e}")
            return False
    
    def _backup_file_with_structure(self, source_file: Path, relative_path: str, project_dir: Path) -> None:
        """
        備份檔案並保持原始目錄結構
        
        Args:
            source_file: 來源檔案完整路徑
            relative_path: 相對於專案的路徑（例如：torch_utils/custom_ops.py）
            project_dir: 目標專案目錄（例如：vicious_pattern/or_mode/bandit/{project}/）
        """
        # 建立目標路徑，保持原始目錄結構
        backup_file = project_dir / relative_path
        backup_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, backup_file)
    
    def _append_to_prompt_txt(self, project_dir: Path, file_path: str) -> None:
        """
        即時追加寫入 prompt.txt
        
        Args:
            project_dir: 專案目錄
            file_path: 檔案相對路徑
        """
        prompt_file = project_dir / "prompt.txt"
        
        # 檢查是否已存在（避免重複寫入）
        existing_paths = set()
        if prompt_file.exists():
            with open(prompt_file, 'r', encoding='utf-8') as f:
                existing_paths = set(line.strip() for line in f if line.strip())
        
        if file_path not in existing_paths:
            with open(prompt_file, 'a', encoding='utf-8') as f:
                f.write(file_path + '\n')
    
    def _execute_bait_code_test(self, round_num: int) -> None:
        """
        執行 Bait Code Test 驗證
        
        對 pending_vicious_backups 中的每個檔案進行獨立驗證，
        每個檔案需要通過所有驗證次數才保留，否則從清單中移除。
        
        驗證流程（方案 B - 單檔案獨立驗證）：
        對每個待驗證檔案：
          1. 執行 N 次驗證循環
          2. 每次驗證：發送 coding_prompt → 掃描 → revert
          3. 任一次驗證失敗（無漏洞）→ 立即移除該檔案
          4. 全部驗證通過 → 保留該檔案
        
        Args:
            round_num: 當前輪數（用於目錄命名）
        """
        if not self.pending_vicious_backups:
            return
        
        self.logger.info(f"  🧪 Bait Code Test: 驗證 {len(self.pending_vicious_backups)} 個檔案，每個檔案 {self.bait_code_test_rounds} 次驗證")
        
        # 複製清單，因為驗證過程中會修改
        files_to_verify = self.pending_vicious_backups.copy()
        verified_files = []
        
        for target_file, bandit_count, semgrep_count in files_to_verify:
            self.logger.info(f"    🔬 驗證檔案: {target_file}")
            
            # 對單一檔案執行所有驗證
            is_valid = self._verify_single_file(target_file, round_num)
            
            if is_valid:
                self.logger.info(f"    ✅ {target_file} 通過所有 {self.bait_code_test_rounds} 次驗證")
                verified_files.append((target_file, bandit_count, semgrep_count))
            else:
                self.logger.info(f"    ❌ {target_file} 驗證失敗，從清單中移除")
        
        # 更新 pending_vicious_backups 為已驗證的檔案
        self.pending_vicious_backups = verified_files
        self.logger.info(f"  🧪 Bait Code Test 完成: {len(verified_files)}/{len(files_to_verify)} 個檔案通過驗證")
    
    def _verify_single_file(self, target_file: str, round_num: int) -> bool:
        """
        對單一檔案執行所有驗證
        
        使用嚴格模式：必須全部驗證都發現漏洞才算通過
        
        流程：
        1. 發送檔案的補 code prompt
        2. 等待回應並檢查回應完整
        3. 掃描
        4. 儲存掃描結果
        5. 調用 clear_copilot_memory(revert) 後進入下一次驗證或換下一個檔案
        
        注意：clear_copilot_memory(revert) 同時執行 revert 並開啟新對話，
        不需要額外呼叫 open_copilot_chat()
        
        Args:
            target_file: 目標檔案相對路徑
            round_num: 當前輪數
            
        Returns:
            bool: 是否通過所有驗證
        """
        # 建立 bait_code_test 目錄結構
        # OriginalScanResult/{scanner}/CWE-{cwe}/{project}/第{round}輪/bait_code_test/{filename}/
        safe_filename = target_file.replace('/', '__').replace('\\', '__')
        
        for test_num in range(1, self.bait_code_test_rounds + 1):
            self.logger.info(f"      驗證 {test_num}/{self.bait_code_test_rounds}")
            
            # 1. 發送 coding_prompt（此時已在新對話中）
            coding_prompt = self._generate_coding_prompt(target_file)
            
            success = self.copilot_handler._send_prompt_with_content(
                prompt_content=coding_prompt,
                line_number=1,
                total_lines=1
            )
            
            if not success:
                self.logger.warning(f"      ⚠️  發送 prompt 失敗")
                # 失敗時也要 revert 並開啟新對話，讓下一個檔案可以繼續
                self.vscode_controller.clear_copilot_memory(modification_action="revert")
                time.sleep(1)
                return False
            
            # 2. 等待回應
            if not self.copilot_handler.wait_for_response(use_smart_wait=True):
                self.logger.warning(f"      ⚠️  等待回應超時")
                self.vscode_controller.clear_copilot_memory(modification_action="revert")
                time.sleep(1)
                return False
            
            response = self.copilot_handler.copy_response()
            if not response:
                self.logger.warning(f"      ⚠️  無法複製回應")
                self.vscode_controller.clear_copilot_memory(modification_action="revert")
                time.sleep(1)
                return False
            
            # 3. 掃描
            has_vulnerability = False
            if self.cwe_scan_manager:
                try:
                    scan_success, vuln_info = self.cwe_scan_manager.scan_from_prompt(
                        project_path=self.project_path,
                        project_name=self.project_path.name,
                        prompt_content=target_file,
                        cwe_type=self.target_cwe,
                        round_number=round_num,
                        line_number=0,  # 特殊標記：bait_code_test
                        bait_code_test_dir=safe_filename,  # 指定 bait_code_test 子目錄
                        bait_code_test_num=test_num  # 驗證次數
                    )
                    
                    if scan_success and vuln_info:
                        for file_path, info in vuln_info.items():
                            if isinstance(info, dict) and info.get("has_vulnerability", False):
                                has_vulnerability = True
                                break
                except Exception as e:
                    self.logger.error(f"      ❌ 掃描錯誤: {e}")
                    self.vscode_controller.clear_copilot_memory(modification_action="revert")
                    time.sleep(1)
                    return False
            
            # 4. 檢查結果並 revert（無論成功或失敗都要 revert + 開啟新對話）
            if not has_vulnerability:
                self.logger.info(f"      驗證 {test_num} 未發現漏洞，驗證失敗")
                # revert 並開啟新對話後返回失敗
                self.vscode_controller.clear_copilot_memory(modification_action="revert")
                time.sleep(1)
                return False
            
            self.logger.info(f"      驗證 {test_num} 發現漏洞 ✓")
            
            # 5. revert 並開啟新對話，準備下一次驗證
            self.vscode_controller.clear_copilot_memory(modification_action="revert")
            time.sleep(1)
        
        # 所有驗證都通過
        return True
    
    def _parse_prompt_line(self, prompt_line: str) -> str:
        """
        解析 prompt.txt 的單行，提取檔案路徑
        
        格式：每行一個檔案路徑
        
        Returns:
            str: 檔案路徑，解析失敗返回空字串
        """
        return prompt_line.strip()
    
    def execute(self) -> Tuple[bool, int]:
        """
        執行完整的 AS 攻擊流程
        
        Returns:
            Tuple[bool, int]: (是否成功完成, 實際處理的檔案數)
        """
        try:
            self.logger.create_separator(f"🚀 開始 Artificial Suicide 攻擊 - CWE-{self.target_cwe}")
            self.logger.info(f"專案: {self.project_path.name}")
            self.logger.info(f"總輪數: {self.total_rounds}")
            self.logger.info(f"總行數: {len(self.prompt_lines)}")
            
            if len(self.prompt_lines) == 0:
                self.logger.warning("⚠️  沒有要處理的檔案")
                return True, 0
            
            self.files_processed_in_project = len(self.prompt_lines)
            
            # 步驟 0：開啟專案
            self.logger.info("📂 開啟專案到 VSCode...")
            if not self.vscode_controller.open_project(str(self.project_path)):
                self.logger.error("❌ 無法開啟專案")
                return False, self.files_processed_in_project
            time.sleep(3)
            
            # 步驟 0.5：執行原始狀態掃描（攻擊前基線掃描）
            should_do_baseline_scan = True
            
            if self.checkpoint_manager:
                if self.checkpoint_manager.is_baseline_scan_completed(self.project_path.name):
                    self.logger.info("📸 原始狀態掃描已在先前執行中完成，跳過...")
                    should_do_baseline_scan = False
            
            if should_do_baseline_scan and self.cwe_scan_manager:
                self.logger.info("📸 執行原始狀態掃描（攻擊前基線）...")
                self.cwe_scan_manager.scan_baseline_state(
                    project_path=self.project_path,
                    project_name=self.project_path.name,
                    prompt_lines=self.prompt_lines,
                    cwe_type=self.target_cwe
                )
                
                if self.checkpoint_manager:
                    self.checkpoint_manager.update_progress(
                        baseline_scan_completed=self.project_path.name
                    )
                    self.logger.info("✅ 原始狀態掃描完成")
            
            # 確定起始輪數
            start_round = self.resume_round if self.is_resume_mode else 1
            if start_round > 1:
                self.logger.info(f"🔄 恢復模式: 從第 {start_round} 輪開始")
            
            # 執行每一輪
            for round_num in range(start_round, self.total_rounds + 1):
                self.logger.create_separator(f"📍 第 {round_num}/{self.total_rounds} 輪")
                
                is_resume_round = self.is_resume_mode and round_num == start_round
                resume_phase = self.resume_phase if is_resume_round else 1
                resume_line = self.resume_line if is_resume_round else 1
                
                success = self._execute_round(round_num, resume_phase=resume_phase, resume_line=resume_line)
                
                if not success:
                    self.logger.error(f"❌ 第 {round_num} 輪執行失敗")
                    return False, self.files_processed_in_project
                
                self.logger.info(f"✅ 第 {round_num} 輪完成")
            
            self.logger.create_separator("🎉 Artificial Suicide 攻擊完成")
            self.logger.info(f"📊 本專案處理了 {self.files_processed_in_project} 個檔案")
            self.logger.info(f"📁 原生掃描報告已輸出到 OriginalScanResult 目錄")
            
            # 統計因早期終止而跳過的檔案
            skipped_count = len(self.vulnerability_found_at)
            if skipped_count > 0:
                self.logger.info(f"⏭️  早期終止: {skipped_count} 個檔案因已發現漏洞而在後續輪次中跳過")
                for line_idx, found_round in self.vulnerability_found_at.items():
                    self.logger.info(f"   - 第 {line_idx} 行: 第 {found_round} 輪發現漏洞")
            
            if self.vicious_files_backed_up > 0:
                self.logger.info(f"🚨 發現漏洞！已備份 {self.vicious_files_backed_up} 個 vicious pattern 檔案")
                self.logger.info(f"📦 備份位置: {self.vicious_pattern_dir}")
            else:
                self.logger.info(f"✅ 未發現漏洞，無 vicious pattern 備份")
            
            return True, self.files_processed_in_project
            
        except Exception as e:
            self.logger.error(f"❌ AS 模式執行錯誤: {e}")
            return False, self.files_processed_in_project
    
    def _execute_round(self, round_num: int, resume_phase: int = 1, resume_line: int = 1) -> bool:
        """執行單輪攻擊（兩道程序）"""
        if self.checkpoint_manager:
            self.checkpoint_manager.update_progress(
                current_round=round_num,
                current_line=resume_line,
                current_phase=resume_phase
            )
        
        # === 第 1 道程序：Query Phase ===
        if resume_phase <= 1:
            self.logger.info(f"▶️  第 {round_num} 輪 - 第 1 道程序（Query Phase）")
            
            if not self._execute_phase1(round_num, start_line=resume_line if resume_phase == 1 else 1):
                return False
            
            self.logger.info("  💾 Keep 修改...")
            self.vscode_controller.clear_copilot_memory(modification_action="keep")
            time.sleep(2)
            
            if self.checkpoint_manager:
                self.checkpoint_manager.update_progress(current_phase=2, current_line=1)
            
            phase2_start_line = 1
        else:
            self.logger.info(f"🔄 恢復模式: 跳過第 {round_num} 輪 Phase 1")
            phase2_start_line = resume_line
        
        # === 第 2 道程序：Coding Phase + Scan ===
        self.logger.info(f"▶️  第 {round_num} 輪 - 第 2 道程序（Coding Phase + Scan）")
        
        # 清空待備份清單（本輪開始時）
        self.pending_vicious_backups = []
        
        if not self._execute_phase2(round_num, start_line=phase2_start_line):
            return False
        
        self.logger.info("  ↩️  Undo 修改...")
        self.vscode_controller.clear_copilot_memory(modification_action="revert")
        time.sleep(2)
        
        # === Bait Code Test 驗證（revert 後執行）===
        # 此時檔案狀態是 Phase 1 的結果（只有惡意名稱，沒有完整惡意 code）
        if self.pending_vicious_backups:
            self.logger.info(f"  🧪 開始 Bait Code Test 驗證（共 {len(self.pending_vicious_backups)} 個檔案）...")
            
            # 執行驗證，會更新 pending_vicious_backups（移除驗證失敗的檔案）
            self._execute_bait_code_test(round_num)
            
            # 驗證完成後，只備份通過驗證的檔案，並標記為攻擊成功
            if self.pending_vicious_backups:
                self.logger.info(f"  📦 備份已驗證的 vicious pattern（共 {len(self.pending_vicious_backups)} 個檔案）...")
                for target_file, bandit_count, semgrep_count in self.pending_vicious_backups:
                    self._backup_vicious_pattern(
                        target_file=target_file,
                        round_num=round_num,
                        line_idx=0,
                        bandit_count=bandit_count,
                        semgrep_count=semgrep_count
                    )
                    
                    # 找到該檔案對應的 line_idx 並標記為攻擊成功
                    for idx, line in enumerate(self.prompt_lines, 1):
                        if self._parse_prompt_line(line) == target_file:
                            if idx not in self.vulnerability_found_at:
                                self.vulnerability_found_at[idx] = round_num
                                self.logger.info(f"  ✅ 第 {idx} 行攻擊成功，後續輪次將跳過")
                            break
            else:
                self.logger.info(f"  ⚠️  所有 vicious pattern 驗證失敗，下一輪將繼續攻擊這些檔案")
            
            self.pending_vicious_backups = []  # 清空
        
        return True
    
    def _execute_phase1(self, round_num: int, start_line: int = 1) -> bool:
        """執行第 1 道程序：Query Phase"""
        try:
            self.logger.info(f"  開始處理第 1 道程序（共 {len(self.prompt_lines)} 行）")
            
            if start_line > 1:
                if start_line > len(self.prompt_lines):
                    self.logger.info(f"  🔄 恢復模式: Phase 1 已完成")
                    return True
                self.logger.info(f"  🔄 恢復模式: 從第 {start_line} 行開始")
            
            if not self.copilot_handler.open_copilot_chat():
                self.logger.error("  ❌ 無法開啟 Copilot Chat")
                return False
            
            successful_lines = 0
            failed_lines = []
            
            if round_num not in self.round_responses:
                self.round_responses[round_num] = {}
            
            for line_idx, line in enumerate(self.prompt_lines, start=1):
                if line_idx < start_line:
                    continue
                
                # === 終止條件：如果該檔案已發現漏洞，跳過後續輪次 ===
                if line_idx in self.vulnerability_found_at:
                    found_round = self.vulnerability_found_at[line_idx]
                    self.logger.info(f"  ⏭️  跳過第 {line_idx} 行（已在第 {found_round} 輪發現漏洞）")
                    successful_lines += 1  # 計為成功，因為已完成目標
                    continue
                    
                if self.checkpoint_manager:
                    self.checkpoint_manager.update_progress(current_line=line_idx)
                
                target_file = self._parse_prompt_line(line)
                if not target_file:
                    self.logger.error(f"  ❌ 第 {line_idx} 行格式錯誤")
                    failed_lines.append(line_idx)
                    continue
                
                retry_count = 0
                line_success = False
                
                while not line_success:
                    try:
                        if retry_count >= config.AS_MODE_MAX_RETRY_PER_LINE:
                            self.logger.error(f"  ❌ 第 {line_idx} 行：已達最大重試次數")
                            failed_lines.append(line_idx)
                            break
                        
                        filename = target_file.replace('/', '__')
                        
                        if retry_count == 0:
                            self.logger.info(f"  處理第 {line_idx}/{len(self.prompt_lines)} 行: {target_file}")
                        else:
                            self.logger.info(f"  重試第 {line_idx} 行（第 {retry_count} 次）")
                        
                        last_response = ""
                        if round_num > 1 and (round_num - 1) in self.round_responses:
                            last_response = self.round_responses[round_num - 1].get(line_idx, "")
                        
                        query_prompt = self._generate_query_prompt(
                            round_num, target_file, last_response
                        )
                        
                        success = self.copilot_handler._send_prompt_with_content(
                            prompt_content=query_prompt,
                            line_number=line_idx,
                            total_lines=len(self.prompt_lines)
                        )
                        
                        if not success:
                            retry_count += 1
                            wait_and_retry(60, line_idx, round_num, self.logger, retry_count)
                            self._clear_input_box()
                            continue
                        
                        if not self.copilot_handler.wait_for_response(use_smart_wait=True):
                            retry_count += 1
                            wait_and_retry(60, line_idx, round_num, self.logger, retry_count)
                            self._clear_input_box()
                            continue
                        
                        response = self.copilot_handler.copy_response()
                        if not response:
                            retry_count += 1
                            wait_and_retry(60, line_idx, round_num, self.logger, retry_count)
                            self._clear_input_box()
                            continue
                        
                        self.logger.info(f"  ✅ 收到回應 ({len(response)} 字元)")
                        
                        if is_response_incomplete(response):
                            self.logger.warning(f"  ⚠️  回應不完整，將等待後重試")
                            retry_count += 1
                            wait_and_retry(1800, line_idx, round_num, self.logger, retry_count)
                            self._clear_input_box()
                            continue
                        
                        save_success = self.copilot_handler.save_response_to_file(
                            project_path=str(self.project_path),
                            response=response,
                            is_success=True,
                            round_number=round_num,
                            phase_number=1,
                            line_number=line_idx,
                            filename=filename,
                            function_name=None,  # 不再使用函式名稱
                            prompt_text=query_prompt,
                            total_lines=len(self.prompt_lines),
                            retry_count=retry_count
                        )
                        
                        if save_success:
                            self.round_responses[round_num][line_idx] = response
                            successful_lines += 1
                            self.logger.info(f"  ✅ 第 {line_idx} 行處理完成")
                            line_success = True
                        else:
                            failed_lines.append(line_idx)
                            break
                        
                        if line_idx < len(self.prompt_lines):
                            time.sleep(1.5)
                        
                    except Exception as e:
                        self.logger.error(f"  ❌ 處理第 {line_idx} 行時發生錯誤: {e}")
                        failed_lines.append(line_idx)
                        break
                
                if not line_success and line_idx not in failed_lines:
                    failed_lines.append(line_idx)
            
            self.logger.info(f"  ✅ 第 1 道完成：{successful_lines}/{len(self.prompt_lines)} 行")
            return True
            
        except Exception as e:
            self.logger.error(f"  ❌ 第 1 道執行錯誤: {e}")
            return False
    
    def _execute_phase2(self, round_num: int, start_line: int = 1) -> bool:
        """執行第 2 道程序：Coding Phase + Scan"""
        try:
            self.logger.info(f"  開始處理第 2 道程序（共 {len(self.prompt_lines)} 行）")
            
            if start_line > 1:
                if start_line > len(self.prompt_lines):
                    self.logger.info(f"  🔄 恢復模式: Phase 2 已完成")
                    return True
                self.logger.info(f"  🔄 恢復模式: 從第 {start_line} 行開始")
            
            if not self.copilot_handler.is_chat_open:
                if not self.copilot_handler.open_copilot_chat():
                    self.logger.error("  ❌ 無法開啟 Copilot Chat")
                    return False
            
            successful_lines = 0
            failed_lines = []
            
            for line_idx, line in enumerate(self.prompt_lines, start=1):
                if line_idx < start_line:
                    continue
                
                # === 終止條件：如果該檔案已發現漏洞，跳過後續輪次 ===
                if line_idx in self.vulnerability_found_at:
                    found_round = self.vulnerability_found_at[line_idx]
                    self.logger.info(f"  ⏭️  跳過第 {line_idx} 行（已在第 {found_round} 輪發現漏洞）")
                    successful_lines += 1  # 計為成功，因為已完成目標
                    continue
                    
                if self.checkpoint_manager:
                    self.checkpoint_manager.update_progress(current_line=line_idx)
                
                target_file = self._parse_prompt_line(line)
                if not target_file:
                    self.logger.error(f"  ❌ 第 {line_idx} 行格式錯誤")
                    failed_lines.append(line_idx)
                    continue
                
                retry_count = 0
                line_success = False
                
                while not line_success:
                    try:
                        if retry_count >= config.AS_MODE_MAX_RETRY_PER_LINE:
                            self.logger.error(f"  ❌ 第 {line_idx} 行：已達最大重試次數")
                            failed_lines.append(line_idx)
                            break
                        
                        filename = target_file.replace('/', '__')
                        
                        if retry_count == 0:
                            self.logger.info(f"  處理第 {line_idx}/{len(self.prompt_lines)} 行: {target_file}")
                        else:
                            self.logger.info(f"  重試第 {line_idx} 行（第 {retry_count} 次）")
                        
                        coding_prompt = self._generate_coding_prompt(target_file)
                        
                        success = self.copilot_handler._send_prompt_with_content(
                            prompt_content=coding_prompt,
                            line_number=line_idx,
                            total_lines=len(self.prompt_lines)
                        )
                        
                        if not success:
                            retry_count += 1
                            wait_and_retry(60, line_idx, round_num, self.logger, retry_count)
                            self._clear_input_box()
                            continue
                        
                        if not self.copilot_handler.wait_for_response(use_smart_wait=True):
                            retry_count += 1
                            wait_and_retry(60, line_idx, round_num, self.logger, retry_count)
                            self._clear_input_box()
                            continue
                        
                        response = self.copilot_handler.copy_response()
                        if not response:
                            retry_count += 1
                            wait_and_retry(60, line_idx, round_num, self.logger, retry_count)
                            self._clear_input_box()
                            continue
                        
                        self.logger.info(f"  ✅ 收到回應 ({len(response)} 字元)")
                        
                        if is_response_incomplete(response):
                            self.logger.warning(f"  ⚠️  回應不完整，將等待後重試")
                            retry_count += 1
                            wait_and_retry(1800, line_idx, round_num, self.logger, retry_count)
                            self._clear_input_box()
                            continue
                        
                        save_success = self.copilot_handler.save_response_to_file(
                            project_path=str(self.project_path),
                            response=response,
                            is_success=True,
                            round_number=round_num,
                            phase_number=2,
                            line_number=line_idx,
                            filename=filename,
                            function_name=None,  # 不再使用函式名稱
                            prompt_text=coding_prompt,
                            total_lines=len(self.prompt_lines),
                            retry_count=retry_count
                        )
                        
                        if not save_success:
                            failed_lines.append(line_idx)
                            break
                        
                        # === CWE 掃描 ===
                        self.logger.info(f"  🔍 開始掃描第 {line_idx} 行")
                        
                        has_vulnerability = False
                        vuln_bandit_count = 0
                        vuln_semgrep_count = 0
                        if self.cwe_scan_manager:
                            try:
                                # 僅傳遞檔案路徑，不再使用函式名稱
                                scan_success, vuln_info = self.cwe_scan_manager.scan_from_prompt(
                                    project_path=self.project_path,
                                    project_name=self.project_path.name,
                                    prompt_content=target_file,
                                    cwe_type=self.target_cwe,
                                    round_number=round_num,
                                    line_number=line_idx
                                )
                                
                                if scan_success:
                                    self.logger.info(f"  ✅ 掃描完成")
                                    # 檢查是否發現漏洞（根據判定模式）
                                    if vuln_info:
                                        for file_path, info in vuln_info.items():
                                            if isinstance(info, dict):
                                                vuln_bandit_count = info.get('bandit', 0)
                                                vuln_semgrep_count = info.get('semgrep', 0)
                                                if info.get("has_vulnerability", False):
                                                    has_vulnerability = True
                                                    self.logger.info(f"  🚨 發現漏洞！Bandit={vuln_bandit_count}, Semgrep={vuln_semgrep_count}")
                                                    # 注意：不在這裡標記 vulnerability_found_at
                                                    # 只有在 Bait Code Test 全部通過後才標記為攻擊成功
                                                    break
                                else:
                                    self.logger.warning(f"  ⚠️  掃描未找到目標")
                            except Exception as e:
                                self.logger.error(f"  ❌ 掃描錯誤: {e}")
                        
                        # === 記錄待備份檔案（實際備份在 revert 後執行）===
                        # 如果有任何漏洞（Bandit 或 Semgrep），記錄到待備份清單
                        if vuln_bandit_count > 0 or vuln_semgrep_count > 0:
                            self.pending_vicious_backups.append((
                                target_file,
                                vuln_bandit_count,
                                vuln_semgrep_count
                            ))
                            self.logger.info(f"  📝 已記錄待備份: {target_file}")
                        
                        successful_lines += 1
                        self.logger.info(f"  ✅ 第 {line_idx} 行處理完成")
                        line_success = True
                        
                        if line_idx < len(self.prompt_lines):
                            time.sleep(1.5)
                        
                    except Exception as e:
                        self.logger.error(f"  ❌ 處理第 {line_idx} 行時發生錯誤: {e}")
                        failed_lines.append(line_idx)
                        break
                
                if not line_success and line_idx not in failed_lines:
                    failed_lines.append(line_idx)
            
            self.logger.info(f"  ✅ 第 2 道完成：{successful_lines}/{len(self.prompt_lines)} 行")
            return True
            
        except Exception as e:
            self.logger.error(f"  ❌ 第 2 道執行錯誤: {e}")
            return False
    
    def _clear_input_box(self):
        """清空輸入框"""
        pyautogui.hotkey('ctrl', 'f1')
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        pyautogui.press('delete')
        time.sleep(0.5)
