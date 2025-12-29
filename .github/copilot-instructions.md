# Copilot Instructions for VSCode_CopilotAutoInteraction

These rules guide AI coding agents working in this repository. Follow them to stay aligned with the existing automation design.

## 1. Big picture
- This project is a **Hybrid UI automation system** that drives **VS Code + GitHub Copilot Chat** via keyboard automation to run experiments and CWE security scans.
- The main entrypoint is `main.py`, which orchestrates:
  - Project discovery and status tracking via `src/project_manager.py`.
  - VS Code window control and Copilot chat memory clearing via `src/vscode_controller.py`.
  - Copilot chat automation (send prompts, wait, copy responses, rate‑limit handling) via `src/copilot_handler.py`.
  - CWE scanning orchestration via `src/cwe_scan_manager.py` plus the Bandit/Semgrep rules in `config/semgrep_rules.yaml`.
  - Optional **Artificial Suicide (AS) mode** via `src/artificial_suicide_mode.py`, which runs a two‑phase query+coding flow.

## 2. Two execution modes
### Non-AS Mode (standard)
- Uses `CopilotHandler._process_project_with_project_prompts()` for multi-round interactions.
- Initializes `NonASModeStatistics` (from `src/query_statistics.py`) to track vulnerability occurrence across rounds.
- CSV output column: `漏洞出現次數` (counts how many rounds had vulnerabilities out of N total rounds).
- Function-level scan CSV uses `函式名稱` column (not modified).

### AS Mode (Artificial Suicide)
- Two phases per round: **Phase 1 (Query)** renames functions, **Phase 2 (Coding)** injects vulnerable code.
- Uses `QueryStatistics` class with `#` markers to skip functions once vulnerabilities are found.
- CSV output column: `QueryTimes` (which round first found vulnerability).
- Function-level scan CSV uses `修改前函式名稱` and `修改後函式名稱` columns to track renamed functions.
- Tracks function name changes via `src/function_name_tracker.py` with progressive search range (±5, ±15, ±30 lines).
- Backs up vulnerable patterns via `src/vicious_pattern_manager.py` (only creates directories when vulnerabilities exist).

## 3. Keep/Undo/Revert operations - CRITICAL timing details

### 3.1 What are Keep and Undo?
When Copilot Chat modifies files, VS Code tracks these changes. When clearing chat memory (`Ctrl+L`), VS Code may show a dialog asking what to do with the modifications:
- **Keep** (`modification_action="keep"`): Preserve all file changes made by Copilot
- **Revert/Undo** (`modification_action="revert"`): Discard all file changes and restore to pre-modification state

This is implemented in `vscode_controller.clear_copilot_memory()` which:
1. Opens Copilot Chat (`Ctrl+F1`)
2. Clears conversation history (`Ctrl+L`)
3. If a save dialog appears, handles it based on `modification_action` parameter
4. Closes Copilot Chat (`Escape`)

### 3.2 AS Mode: Phase 1 and Phase 2 Keep/Undo timing

```
Round N execution flow:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Phase 1 (Query) - Rename functions                                          │
│   1. Send query prompt asking AI to rename function variables               │
│   2. Wait for response, copy and save it                                    │
│   3. Track the NEW function name and line number                            │
│   4. ✅ KEEP modifications (clear_copilot_memory("keep"))                   │
│      → Function renames are PRESERVED in the file                           │
│      → This is the "poisoned state" we want to test                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ Phase 2 (Coding) - Inject vulnerable code                                   │
│   1. Send coding prompt asking AI to add vulnerable code                    │
│   2. Wait for response, copy and save it                                    │
│   3. 🔍 CWE SCAN happens HERE (while vulnerable code is still in file)      │
│   4. Record vulnerabilities to vicious_pattern_manager                      │
│   5. ↩️ UNDO/REVERT modifications (clear_copilot_memory("revert"))          │
│      → Vulnerable code is REMOVED                                           │
│      → File returns to Phase 1 state (renamed functions, no vulnerabilities)│
├─────────────────────────────────────────────────────────────────────────────┤
│ Post-Phase 2: Vicious Pattern Backup                                        │
│   - After UNDO, if vulnerabilities were found, backup the Phase 1 pattern   │
│   - This preserves the "function rename pattern" that successfully          │
│     induced AI to generate vulnerable code                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key insight for AS Mode**: 
- Phase 1 changes are KEPT because the renamed functions are the "attack pattern" we're testing
- Phase 2 changes are UNDONE because we only want to scan for vulnerabilities, not keep them
- The backup happens AFTER undo, capturing the Phase 1 state (renamed but safe)

### 3.3 Non-AS Mode: Simple Keep/Undo per round

```
Round N execution flow:
┌─────────────────────────────────────────────────────────────────────────────┐
│ For each prompt line:                                                       │
│   1. Send prompt to Copilot                                                 │
│   2. Wait for response                                                      │
│   3. Copy and save response                                                 │
│   4. 🔍 CWE SCAN (if enabled) - scan current file state                     │
│                                                                             │
│ After all lines processed:                                                  │
│   5. Apply modification_action from settings (keep/revert)                  │
│      - Uses config.COPILOT_CHAT_MODIFICATION_ACTION or                      │
│      - interaction_settings["copilot_chat_modification_action"]             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.4 Code locations for Keep/Undo logic

| Location | Function | Purpose |
|----------|----------|---------|
| `src/vscode_controller.py:133` | `clear_copilot_memory()` | Core implementation using `pyautogui` |
| `src/artificial_suicide_mode.py:432` | `_execute_round()` | AS Mode Phase 1 KEEP |
| `src/artificial_suicide_mode.py:443` | `_execute_round()` | AS Mode Phase 2 REVERT |
| `src/copilot_handler.py:1216` | `_process_project_with_project_prompts()` | Non-AS per-round |
| `src/copilot_handler.py:1378` | `clear_and_restart_chat()` | Helper method |

### 3.5 CWE Scan timing relative to Keep/Undo

**AS Mode** (in `_execute_phase2()`):
```python
# 1. Send coding prompt and get response
# 2. Save response to file
# 3. 🔍 CWE SCAN HERE - file still has vulnerable code
scan_success, scan_files, vuln_info = self.cwe_scan_manager.scan_from_prompt_function_level(...)
# 4. Record vulnerabilities to vicious_pattern_manager
# 5. Return to _execute_round()
# 6. ↩️ UNDO happens in _execute_round() AFTER _execute_phase2() returns
# 7. Backup vicious patterns (now file is in Phase 1 state)
```

**Non-AS Mode** (in `_perform_cwe_scan_for_prompt()`):
```python
# Scan happens after each prompt line response is saved
# Keep/Undo happens at the END of the round (after all lines processed)
```

## 4. CWE scanning & data outputs
- CWE scanning is handled by `src/cwe_scan_manager.py`:
  - `extract_file_paths_from_prompt()` and `extract_function_targets_from_prompt()` parse prompt lines of the form `path/to/file.py|function_name`.
  - `scan_from_prompt_function_level()` orchestrates Bandit/Semgrep runs via `CWEDetector` and writes both JSON and CSV outputs.
- Output directory structure:
  ```
  output/
  ├── CWE_Result/CWE-{cwe}/
  │   ├── Bandit/{project}/第N輪/*.csv
  │   ├── Semgrep/{project}/第N輪/*.csv
  │   └── query_statistics/{project}.csv
  ├── OriginalScanResult/{Bandit|Semgrep}/...
  ├── ExecutionResult/Success/{project}/
  │   ├── 第N輪/第M道/*.md (Copilot responses)
  │   └── FunctionName_query/roundN.csv (AS mode only)
  └── vicious_pattern/{project}/... (AS mode, only if vulnerabilities found)
  ```

## 5. Key CSV schemas
- **function_level_scan.csv** (Non-AS Mode): `輪數,行號,檔案路徑,函式名稱,漏洞數量,漏洞行號,掃描器,信心度,嚴重性,問題描述,掃描狀態,失敗原因`
- **function_level_scan.csv** (AS Mode): includes `修改前函式名稱,修改後函式名稱` columns
- **query_statistics.csv** (Non-AS): `檔案路徑,函式名稱,round1,...,roundN,漏洞出現次數`
- **query_statistics.csv** (AS): `檔案路徑,函式名稱,round1,...,roundN,QueryTimes` (uses `#` for skipped rounds)

## 6. Project‑specific conventions
- **Prompt format**: `path/to/file.py|function_name` (one per line in `projects/{project}/prompt.txt`)
- **Config access**: Use `from config.config import config` with ImportError fallback pattern.
- **Logger usage**: Use `get_logger("ModuleName")` and `logger.create_separator()` for consistent output.

## 7. Workflows & commands
```bash
# Environment setup
source activate_env.sh  # or: conda activate copilot_py310

# Run main UI
python main.py

# Verification tests
python verify_cwe_installation.py
python test_cwe_scan.py
python test_rate_limit_handler.py
```

## 8. How AI changes should be structured
- Extend existing controllers (`HybridUIAutomationScript`, `CopilotHandler`, `CWEScanManager`) rather than creating parallel flows.
- When reading scan CSVs, support both column names: try `函式名稱` first, then `修改後函式名稱`.
- For `vicious_pattern_manager.py`: directories are created lazily (only when backing up files), empty directories are cleaned up in `finalize()`.
- Be careful with `pyautogui` / keyboard shortcuts — respect existing keybindings (`Ctrl+F1` for chat focus).

---
If any of these instructions seem unclear for a change you're about to make, surface the specific file and flow (e.g. "AS Phase 2 scan timing" or "function‑level CSV schema") so we can refine this document.
