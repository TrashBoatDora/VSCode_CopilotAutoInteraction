# VSCode Copilot Chat Hybrid UI Automation Script (CWE 分離架構版)

本專案為 VSCode Copilot Chat 的多輪互動自動化腳本，結合圖像辨識、智能等待、CWE 安全掃描分離架構，實現高效、穩定且安全的自動化程式碼生成與風險分析。

---

## 主要特色

- **多輪互動自動化**：支援多輪 prompt 互動，完整模擬 Copilot Chat 對話流程
- **智能等待與圖像辨識**：以 send/stop 按鈕與內容穩定性判斷回應完成，並自動清除 VS Code 通知遮擋
- **CWE 安全掃描分離**：每輪回應完成後立即執行 8 類 CWE 安全掃描，並將結果獨立分類於 Safe/Vulnerable 目錄
- **自動化與安全結果完全分離**：自動化流程的成功/失敗與安全風險分類互不干擾
- **智能終止**：發現高風險漏洞即時終止後續輪次，但已完成輪次仍保留
- **批次處理與日誌追蹤**：支援大規模專案批次處理、詳細日誌與全域統計

---

## 目錄結構

```
VSCode_CopilotAutoInteraction/
├── ExecutionResult/
│   ├── Success/           # 自動化成功結果
│   ├── Fail/              # 自動化失敗結果
│   ├── CWE_Results/       # 安全風險獨立分類
│   │   ├── Safe/
│   │   └── Vulnerable/
│   └── CWEScanner_UpdateReport/ # 全域統計與警報
├── projects/              # 原始專案，僅存原始碼與狀態檔
├── src/                   # 核心程式碼
├── docs/                  # 技術報告與設計說明
├── requirements.txt
└── README.md
```

---

## 安裝與設定

1. 安裝 Python 依賴
  ```bash
  pip install -r requirements.txt
  ```
2. 將待處理專案放入 `projects/` 目錄
3. 編輯 `prompts/` 內的 prompt 檔案（多輪互動可用 prompt1.txt、prompt2.txt ...）
4. 調整 `config/config.py` 參數（如等待時間、批次大小等）

---

## 執行方式

```bash
python main.py
```
依照互動式視窗選擇執行選項。

---

## 自動化與安全掃描流程

1. 掃描 `projects/` 目錄下所有專案
2. 每個專案進行多輪 Copilot Chat 互動
3. 每輪流程：
  - 發送 prompt
  - 智能等待回應完成
  - **立即執行 CWE 安全掃描**
  - 複製回應並儲存
  - 生成安全報告到獨立目錄
  - 若發現高風險漏洞，終止後續輪次
4. 所有結果自動分類儲存，並產生全域統計

---

## 安全掃描與目錄分類

- **Success/Fail**：純粹反映自動化流程技術狀態
- **CWE_Results/Safe/Vulnerable**：純粹反映安全風險等級
- **CWEScanner_UpdateReport/**：全域統計與高風險警報

---

## 常見問題與故障排除

- 請參考 `docs/Reports/` 及日誌檔案獲取詳細錯誤說明與解決方案
- 若需重置狀態，請執行 `ProjectStatusReset.py`

---

## 技術報告與設計依據

本專案架構與邏輯完全依據下列技術報告設計與驗證：
- `20250919_cwe_logic_correction_report.md`
- `20250919_cwe_path_structure_fix_report.md`
- `20250919_cwe_separation_architecture_report.md`
- `20250919_cwe_architecture_and_logic_summary.md`

---

## 授權

MIT License

---

如需進一步技術細節、架構說明或貢獻指南，請參閱 `docs/` 目錄下相關文件。