# -*- coding: utf-8 -*-
"""
CWE 掃描設定 UI 模組
提供獨立的 CWE 掃描設定介面
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional
from pathlib import Path

from src.logger import get_logger

logger = get_logger("CWEScanUI")


class CWEScanSettingsUI:
    """CWE 掃描設定介面"""
    
    # 支援的 CWE 類型列表（與 CWEDetector 保持一致）
    SUPPORTED_CWES = [
        ("CWE-022", "Path Traversal - 路徑遍歷"),
        ("CWE-078", "OS Command Injection - 命令注入"),
        ("CWE-079", "Cross-site Scripting (XSS) - 跨站腳本"),
        ("CWE-095", "Code Injection - 程式碼注入"),
        ("CWE-113", "HTTP Response Splitting - HTTP 回應分割"),
        ("CWE-117", "Log Injection - 日誌注入"),
        ("CWE-326", "Weak Encryption - 弱加密"),
        ("CWE-327", "Broken Cryptography - 損壞的加密"),
        ("CWE-329", "CBC without Random IV - CBC 無隨機初始化向量"),
        ("CWE-347", "JWT Vulnerabilities - JWT 漏洞"),
        ("CWE-377", "Insecure Temporary File - 不安全的臨時檔案"),
        ("CWE-502", "Deserialization - 反序列化"),
        ("CWE-643", "XPath Injection - XPath 注入"),
        ("CWE-760", "Predictable Salt - 可預測的鹽值"),
        ("CWE-918", "SSRF - 伺服器端請求偽造"),
        ("CWE-943", "SQL Injection - SQL 注入"),
        ("CWE-1333", "ReDoS - 正則表達式阻斷服務"),
    ]
    
    def __init__(self, default_settings: Dict = None):
        """
        初始化 UI
        
        Args:
            default_settings: 預設設定
        """
        self.default_settings = default_settings or {}
        self.result = None
        self.root = None
        
        # UI 元件
        self.enabled_var = None
        self.cwe_type_var = None
        self.output_dir_var = None
    
    def show(self) -> Optional[Dict]:
        """
        顯示設定對話框
        
        Returns:
            Optional[Dict]: 使用者的設定，若取消則返回 None
        """
        self.root = tk.Tk()
        self.root.title("CWE 掃描設定")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # 設定視窗置中
        self._center_window()
        
        # 建立 UI 元件
        self._create_widgets()
        
        # 載入預設值
        self._load_defaults()
        
        # 執行主迴圈
        self.root.mainloop()
        
        return self.result
    
    def _center_window(self):
        """將視窗置中"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def _create_widgets(self):
        """建立 UI 元件"""
        # 創建主容器框架
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)

        # 創建 Canvas 和 Scrollbar
        canvas = tk.Canvas(main_container)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        
        # 創建可滾動的框架
        main_frame = ttk.Frame(canvas, padding="20")
        
        # 設定 Canvas 滾動
        main_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # 在 Canvas 中創建視窗
        canvas_window = canvas.create_window((0, 0), window=main_frame, anchor="nw")
        
        # 配置 Canvas 尺寸調整
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind('<Configure>', on_canvas_configure)

        # 配置滾輪綁定
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 放置 Canvas 和 Scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 綁定滑鼠滾輪
        def on_mousewheel(event):
            try:
                if event.delta:
                    delta = -1 * (event.delta / 120)
                else:
                    delta = -1 if event.num == 4 else 1
                canvas.yview_scroll(int(delta), "units")
                return "break"
            except:
                pass

        canvas.bind("<MouseWheel>", on_mousewheel)
        canvas.bind("<Button-4>", on_mousewheel)
        canvas.bind("<Button-5>", on_mousewheel)
        
        # 遞迴綁定所有子元件
        def bind_mousewheel_to_children(parent):
            for child in parent.winfo_children():
                # 跳過 Listbox 和它的 Scrollbar，讓它們自己處理滾動
                if isinstance(child, (tk.Listbox, ttk.Scrollbar)):
                    continue
                    
                try:
                    child.bind("<MouseWheel>", on_mousewheel)
                    child.bind("<Button-4>", on_mousewheel)
                    child.bind("<Button-5>", on_mousewheel)
                    if hasattr(child, 'winfo_children'):
                        bind_mousewheel_to_children(child)
                except:
                    pass
        
        # 確保在元件創建後綁定滾輪事件
        self.root.after(100, lambda: bind_mousewheel_to_children(main_frame))

        # 標題
        title_label = ttk.Label(
            main_frame,
            text="CWE 漏洞掃描設定",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 啟用掃描
        self.enabled_var = tk.BooleanVar(value=False)
        enabled_check = ttk.Checkbutton(
            main_frame,
            text="啟用 CWE 掃描功能",
            variable=self.enabled_var,
            command=self._toggle_scan_enabled
        )
        enabled_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # 分隔線
        separator1 = ttk.Separator(main_frame, orient='horizontal')
        separator1.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # CWE 類型選擇
        cwe_label = ttk.Label(main_frame, text="選擇要掃描的 CWE 類型:")
        cwe_label.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        
        # 建立 CWE 類型清單框架
        cwe_frame = ttk.Frame(main_frame)
        cwe_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 建立 Listbox 和滾動條
        scrollbar = ttk.Scrollbar(cwe_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.cwe_listbox = tk.Listbox(
            cwe_frame,
            height=12,
            yscrollcommand=scrollbar.set,
            selectmode=tk.SINGLE,
            font=("Courier", 10)
        )
        self.cwe_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.cwe_listbox.yview)
        
        # 填充 CWE 類型
        for cwe_id, description in self.SUPPORTED_CWES:
            display_text = f"{cwe_id:<12} - {description}"
            self.cwe_listbox.insert(tk.END, display_text)
        
        # 說明文字
        info_label = ttk.Label(
            main_frame,
            text="📌 提示: 掃描會在 Copilot 完成回應後自動執行\n"
                 "掃描目標為 prompt 中提到的檔案",
            foreground="gray",
            justify=tk.LEFT
        )
        info_label.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        # 輸出目錄 - 使用 config 中的路徑
        output_label = ttk.Label(main_frame, text="掃描結果輸出目錄:")
        output_label.grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(15, 5))
        
        # 從 config 獲取預設輸出目錄
        try:
            from config.config import config
            default_output_dir = str(config.CWE_RESULT_DIR)
        except ImportError:
            default_output_dir = "./output/CWE_Result"
        
        self.output_dir_var = tk.StringVar(value=default_output_dir)
        output_entry = ttk.Entry(main_frame, textvariable=self.output_dir_var, width=60)
        output_entry.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 分隔線
        separator2 = ttk.Separator(main_frame, orient='horizontal')
        separator2.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15)
        
        # 按鈕框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=9, column=0, columnspan=2)
        
        # 確認按鈕
        ok_button = ttk.Button(
            button_frame,
            text="確認",
            command=self._on_ok,
            width=15
        )
        ok_button.pack(side=tk.LEFT, padx=5)
        
        # 取消按鈕
        cancel_button = ttk.Button(
            button_frame,
            text="取消",
            command=self._on_cancel,
            width=15
        )
        cancel_button.pack(side=tk.LEFT, padx=5)
        
        # 初始狀態：停用 CWE 選擇
        self._toggle_scan_enabled()
    
    def _toggle_scan_enabled(self):
        """切換掃描啟用狀態時的處理"""
        enabled = self.enabled_var.get()
        
        # 啟用或停用 CWE 選擇
        state = tk.NORMAL if enabled else tk.DISABLED
        self.cwe_listbox.config(state=state)
    
    def _load_defaults(self):
        """載入預設值"""
        if not self.default_settings:
            return
        
        # 載入啟用狀態
        if "enabled" in self.default_settings:
            self.enabled_var.set(self.default_settings["enabled"])
        
        # 載入 CWE 類型
        if "cwe_type" in self.default_settings:
            cwe_type = self.default_settings["cwe_type"]
            # 在列表中選中對應的 CWE
            for i, (cwe_id, _) in enumerate(self.SUPPORTED_CWES):
                if cwe_id == f"CWE-{cwe_type}":
                    self.cwe_listbox.selection_clear(0, tk.END)
                    self.cwe_listbox.selection_set(i)
                    self.cwe_listbox.see(i)
                    break
        
        # 載入輸出目錄
        if "output_dir" in self.default_settings:
            self.output_dir_var.set(self.default_settings["output_dir"])
        
        # 更新元件狀態
        self._toggle_scan_enabled()
    
    def _on_ok(self):
        """確認按鈕點擊處理"""
        enabled = self.enabled_var.get()
        
        if enabled:
            # 檢查是否選擇了 CWE 類型
            selection = self.cwe_listbox.curselection()
            if not selection:
                messagebox.showwarning(
                    "未選擇 CWE 類型",
                    "請選擇要掃描的 CWE 類型"
                )
                return
            
            # 取得選中的 CWE 類型
            selected_index = selection[0]
            cwe_id, description = self.SUPPORTED_CWES[selected_index]
            cwe_type = cwe_id.replace("CWE-", "")  # 移除前綴，只保留數字
        else:
            cwe_type = None
        
        # 取得輸出目錄
        output_dir = self.output_dir_var.get().strip()
        if not output_dir:
            try:
                from config.config import config
                output_dir = str(config.CWE_RESULT_DIR)
            except ImportError:
                output_dir = "./output/CWE_Result"
        
        # 建立結果
        self.result = {
            "enabled": enabled,
            "cwe_type": cwe_type,
            "output_dir": output_dir
        }
        
        logger.info(f"CWE 掃描設定: {self.result}")
        
        self.root.destroy()
    
    def _on_cancel(self):
        """取消按鈕點擊處理"""
        self.result = None
        logger.info("使用者取消了 CWE 掃描設定")
        self.root.destroy()


def show_cwe_scan_settings(default_settings: Dict = None) -> Optional[Dict]:
    """
    顯示 CWE 掃描設定對話框（便捷函數）
    
    Args:
        default_settings: 預設設定
        
    Returns:
        Optional[Dict]: 使用者的設定，若取消則返回 None
    """
    ui = CWEScanSettingsUI(default_settings)
    return ui.show()


# 測試用主函數
if __name__ == "__main__":
    # 測試預設值
    try:
        from config.config import config
        default_output_dir = str(config.CWE_RESULT_DIR)
    except ImportError:
        default_output_dir = "./output/CWE_Result"
    
    default = {
        "enabled": True,
        "cwe_type": "022",
        "output_dir": default_output_dir
    }
    
    result = show_cwe_scan_settings(default)
    
    if result:
        print("使用者設定:")
        print(f"  啟用: {result['enabled']}")
        print(f"  CWE 類型: {result['cwe_type']}")
        print(f"  輸出目錄: {result['output_dir']}")
    else:
        print("使用者取消了設定")
