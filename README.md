

# VSCode Copilot Chat Hybrid UI Automation Script

本專案為 VSCode Copilot Chat 的自動化腳本，支援多語環境，結合圖像辨識與鍵盤自動化，實現穩定、高效的自動化互動。
腳本可自動開啟專案、發送 prompt、等待回應、複製結果，並自動處理 VS Code 通知遮擋與多種異常情境。

---

## 專案特色

- **模組化設計**：功能分離，易於維護與擴充
- **圖像辨識+鍵盤自動化**：以圖像辨識（stop/send 按鈕）為主，輔以鍵盤操作，兼顧穩定性與相容性
- **智能等待**：僅依圖像辨識與回應穩定性判斷，效率高、誤判少
- **自動清除通知**：遇到通知遮擋時自動清除，並解決中文輸入法干擾
- **批次處理**：支援大規模專案的分批處理和中斷續跑
- **詳細日誌**：多層級日誌記錄，包含專案級和系統級日誌
- **Copilot 記憶體清除**：每個專案處理前自動清除 Copilot 記憶體，避免交叉污染
- **回應複製/關閉強化**：自動重試複製 Copilot 回應，確保內容完整，並智能判斷何時關閉 VS Code
- **一鍵重置**：ProjectStatusReset.py 可自動重設狀態並刪除 Copilot_AutoComplete 報告

---


## 目錄結構

```
VSCode_CopilotChatAutomator/
├── ExecutionResult/           # 所有自動化結果與日誌
│   ├── Success/
│   ├── Fail/
│   └── AutomationLog/
├── docs/
│   └── Reports/               # 變更紀錄與優化報告
├── projects/                  # 各自動化專案
│   └── automation_status.json
├── src/                       # 核心程式碼
│   ├── copilot_handler.py      # Copilot Chat 操作與智能等待
│   ├── image_recognition.py    # 圖像辨識與通知清除
│   ├── logger.py              # 日誌系統
│   ├── config.py              # 配置管理
│   └── ...                    # 其他模組
├── prompt.txt                 # 自動化互動的 prompt 來源
├── requirements.txt
└── README.md
```

---


## 安裝與設定

### 1. 安裝 Python 依賴

```bash
pip install -r requirements.txt
```

### 2. 設定 prompt

編輯專案根目錄的 `prompt.txt`，內容為你想要 Copilot 執行的任務。

### 3. 放置專案檔案

將待處理的專案資料夾放置在 `projects/` 目錄下。

### 4. 配置設定

編輯 `config/config.py` 調整參數（如 VS Code 啟動延遲、回應超時、批次大小等）。

---


## 使用方法

### 基本執行

```bash
python main.py
```

依照彈出視窗選擇執行選項（如是否重置狀態、等待模式等）。

---


## 主要自動化流程

1. **環境檢查**：驗證配置、prompt 檔案和執行環境
2. **專案掃描**：掃描 `projects/` 目錄下的所有專案
3. **分批處理**：將專案分批，避免長時間運行的不穩定性
4. **專案處理**：
  - 開啟 VS Code 專案
  - 聚焦 Copilot Chat，貼上 prompt 並送出
  - 智能等待回應（圖像辨識+內容穩定性，遇到遮擋自動清除通知）
  - 複製回應內容，儲存於 ExecutionResult
  - 關閉 VS Code 實例，進入下一專案或結束
5. **錯誤處理**：自動重試失敗的專案
6. **生成報告**：輸出詳細的執行摘要

---


## 智能等待與通知清除機制

- **圖像辨識**：持續檢查 Copilot Chat 的 stop/send 按鈕
- **回應穩定性**：內容連續穩定 3 次、長度超過 100 字元即判定完成
- **自動清除通知**：若偵測不到按鈕，會自動用剪貼簿貼上命令清除通知，完全不受中文輸入法影響

---

## 錯誤處理機制

- **自動重試**：對於暫時性錯誤，自動重試最多 3 次
- **錯誤分類**：將錯誤分為 VS Code、Copilot、圖像辨識等類型
- **恢復策略**：根據錯誤類型採用不同的恢復策略
- **緊急停止**：支援 Ctrl+C 中斷和滑鼠左上角緊急停止

---


## 日誌系統

- **主日誌**：記錄整個執行過程的詳細資訊
- **專案日誌**：每個專案在 ExecutionResult 目錄下生成獨立日誌
- **錯誤追蹤**：完整記錄錯誤堆疊和恢復過程

---


## 注意事項

1. **環境穩定性**：確保在穩定的環境下運行，避免其他程式干擾
2. **圖像辨識與鍵盤操作**：腳本以圖像辨識為主，輔以鍵盤操作，穩定性高
3. **權限設定**：確保腳本有足夠權限操作檔案和控制應用程式
4. **網路連線**：Copilot 需要網路連線才能正常運作
5. **記憶體需求**：大量專案處理時需要充足的系統記憶體
6. **prompt 設定**：記得在 `prompt.txt` 中設定適合的提示詞內容
7. **報告清理**：使用 ProjectStatusReset.py 重設狀態時，會自動刪除所有 ExecutionResult 及 automation_status

---


## 故障排除

### 清除專案處理狀態

如果你想重新處理已經完成或失敗的專案，可以：

1. 刪除 `projects/automation_status.json` 重新掃描所有專案
2. 手動編輯狀態檔案，將 `status` 改為 `pending`
3. 使用 ProjectStatusReset.py 或內建腳本一鍵重設

---


### 常見問題

**VS Code 無法啟動**
- 檢查 VS Code 是否正確安裝
- 確認 `code` 命令在 PATH 中
- 嘗試手動執行 `code --version`

**圖像辨識/通知清除問題**
- 若遇到 UI 遮擋，請確認 assets/stop_button.png、send_button.png 圖像資源清晰
- 若命令面板輸入異常，請確認已安裝 pyperclip 並使用預設剪貼簿

**prompt 檔案問題**
- 檢查 `prompt.txt` 是否存在於專案根目錄
- 確認檔案內容不為空
- 使用 UTF-8 編碼儲存檔案

**Copilot 無回應**
- 檢查 Copilot 擴充功能是否啟用
- 確認網路連線正常
- 嘗試手動測試 Copilot Chat

**專案處理失敗**
- 查看 ExecutionResult/AutomationLog 內的日誌
- 檢查專案是否包含支援的程式檔案
- 確認專案路徑和權限

---


## 擴展說明

本腳本採用模組化設計，可以輕鬆擴展新功能：
- 添加新的程式語言支援
- 自定義 prompt 模板
- 集成其他 AI 工具
- 添加更多錯誤恢復策略

---


## 技術細節

### 核心技術
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