import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
from pathlib import Path
import sys
import threading

# 設定模組搜尋路徑
sys.path.append(str(Path(__file__).parent.parent))

from config.config import config

class UIManager:
    """UI 管理器 - 提供簡單的選項選擇介面"""
    
    def __init__(self):
        """初始化 UI 管理器"""
        self.reset_selected = False
        self.smart_wait_selected = True
        self.choice_made = False
        
    def show_options_dialog(self) -> tuple:
        """
        顯示選項對話框，讓使用者選擇執行選項
        
        Returns:
            tuple: (是否重置狀態, 是否使用智能等待)
        """
        root = tk.Tk()
        root.title("自動化腳本設定")
        root.geometry("480x450")  # 增加視窗尺寸，確保所有內容可見
        root.resizable(False, False)  # 固定視窗大小，防止使用者調整大小
        
        # 設定視窗樣式
        style = ttk.Style()
        style.configure("TButton", font=("Arial", 10))
        style.configure("TCheckbutton", font=("Arial", 10))
        style.configure("TLabel", font=("Arial", 10))
        style.configure("Header.TLabel", font=("Arial", 12, "bold"))
        
        # 創建框架
        frame = ttk.Frame(root, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 標題
        title_label = ttk.Label(frame, text="VSCode Copilot Chat 自動化腳本設定", style="Header.TLabel")
        title_label.pack(pady=10)
        
        # 重置選項
        reset_var = tk.BooleanVar(value=False)
        reset_check = ttk.Checkbutton(
            frame, 
            text="執行前重置專案狀態 (清除過去的執行紀錄)", 
            variable=reset_var
        )
        reset_check.pack(anchor=tk.W, pady=5)
        
        # 等待模式選擇
        wait_frame = ttk.LabelFrame(frame, text="選擇等待 Copilot 回應的方式")
        wait_frame.pack(fill=tk.X, pady=10)
        
        wait_var = tk.BooleanVar(value=True)
        smart_radio = ttk.Radiobutton(
            wait_frame, 
            text="智能等待 (檢查回應是否完整，建議選項)", 
            variable=wait_var, 
            value=True
        )
        smart_radio.pack(anchor=tk.W, padx=10, pady=5)
        
        fixed_radio = ttk.Radiobutton(
            wait_frame, 
            text="固定時間等待 (使用設定的固定秒數)", 
            variable=wait_var, 
            value=False
        )
        fixed_radio.pack(anchor=tk.W, padx=10, pady=5)
        
        # 說明文字
        description = """
        • 重置專案狀態: 
          清除所有過去的執行紀錄，重設專案為待處理狀態
        • 智能等待: 
          檢查 Copilot 回應是否完整，可能比較準確但稍慢
        • 固定時間等待: 
          使用設定的固定時間等待，較快但可能不準確
        """
        desc_label = ttk.Label(frame, text=description, wraplength=430)
        desc_label.pack(pady=10, fill=tk.X)
        
        # 按鈕
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=10, side=tk.BOTTOM)
        
        def on_start():
            self.reset_selected = reset_var.get()
            self.smart_wait_selected = wait_var.get()
            self.choice_made = True
            root.destroy()
        
        def on_cancel():
            if messagebox.askyesno("確認取消", "確定要取消執行嗎?"):
                root.destroy()
                sys.exit(0)
        
        start_btn = ttk.Button(btn_frame, text="開始執行", command=on_start, width=15)
        start_btn.pack(side=tk.LEFT, padx=10, expand=True)
        
        cancel_btn = ttk.Button(btn_frame, text="取消", command=on_cancel, width=15)
        cancel_btn.pack(side=tk.RIGHT, padx=10, expand=True)
        
        # 顯示對話框並等待
        root.protocol("WM_DELETE_WINDOW", on_cancel)  # 處理視窗關閉
        root.mainloop()
        
        # 檢查是否做出選擇
        if not self.choice_made:
            sys.exit(0)
            
        return (self.reset_selected, self.smart_wait_selected)
    
    def execute_reset_if_needed(self, should_reset: bool) -> bool:
        """
        如果需要，執行專案狀態重置
        
        Args:
            should_reset: 是否需要重置
            
        Returns:
            bool: 執行是否成功
        """
        if not should_reset:
            return True
            
        try:
            # 直接執行重置腳本，不使用多執行緒
            reset_script = Path(__file__).parent.parent / "src" / "ProjectStatusReset.py"
            result = subprocess.run(
                [sys.executable, str(reset_script)], 
                capture_output=True, 
                text=True
            )
            
            # 輸出重置結果到控制台，而不是使用訊息框
            if "所有專案狀態已重設為 pending" in result.stdout:
                print("✅ 所有專案狀態已重設為 pending，並清除執行結果")
                return True
            else:
                print(f"⚠️ 重置訊息: {result.stdout}")
                return True
                
        except Exception as e:
            print(f"❌ 重置專案狀態時發生錯誤: {str(e)}")
            return False

# 創建全域實例
ui_manager = UIManager()

# 便捷函數
def show_options_dialog() -> tuple:
    """顯示選項對話框的便捷函數"""
    return ui_manager.show_options_dialog()

def execute_reset_if_needed(should_reset: bool) -> bool:
    """執行重置的便捷函數"""
    return ui_manager.execute_reset_if_needed(should_reset)