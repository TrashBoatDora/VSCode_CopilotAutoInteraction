# -*- coding: utf-8 -*-
"""
簡單測試腳本，驗證各模組基本功能
"""

import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_imports():
    """測試所有模組是否能正確導入"""
    print("測試模組導入...")
    
    try:
        from config.config import config
        print("✓ config 模組導入成功")
    except Exception as e:
        print(f"✗ config 模組導入失敗: {e}")
        return False
    
    try:
        from src.logger import get_logger
        print("✓ logger 模組導入成功")
    except Exception as e:
        print(f"✗ logger 模組導入失敗: {e}")
        return False
    
    try:
        from src.project_manager import ProjectManager
        print("✓ project_manager 模組導入成功")
    except Exception as e:
        print(f"✗ project_manager 模組導入失敗: {e}")
        return False
    
    try:
        from src.vscode_controller import VSCodeController
        print("✓ vscode_controller 模組導入成功")
    except Exception as e:
        print(f"✗ vscode_controller 模組導入失敗: {e}")
        return False
    
    try:
        from src.copilot_handler import CopilotHandler
        print("✓ copilot_handler 模組導入成功")
    except Exception as e:
        print(f"✗ copilot_handler 模組導入失敗: {e}")
        return False
    
    try:
        from src.image_recognition import ImageRecognition
        print("✓ image_recognition 模組導入成功")
    except Exception as e:
        print(f"✗ image_recognition 模組導入失敗: {e}")
        return False
    
    try:
        from src.error_handler import ErrorHandler
        print("✓ error_handler 模組導入成功")
    except Exception as e:
        print(f"✗ error_handler 模組導入失敗: {e}")
        return False
    
    return True

def test_basic_functionality():
    """測試基本功能"""
    print("\n測試基本功能...")
    
    try:
        from config.config import config
        from src.logger import get_logger
        from src.project_manager import ProjectManager
        
        # 測試日誌
        logger = get_logger("TestLogger")
        logger.info("測試日誌功能")
        print("✓ 日誌功能正常")
        
        # 測試配置
        config.ensure_directories()
        print("✓ 配置和目錄創建正常")
        
        # 測試專案管理器
        pm = ProjectManager()
        projects = pm.scan_projects()
        print(f"✓ 專案掃描正常，發現 {len(projects)} 個專案")
        
        return True
        
    except Exception as e:
        print(f"✗ 基本功能測試失敗: {e}")
        return False

def test_dependencies():
    """測試依賴套件"""
    print("\n測試依賴套件...")
    
    dependencies = [
        ("pyautogui", "UI 自動化"),
        ("pyperclip", "剪貼簿操作"),
        ("cv2", "OpenCV 圖像處理"),
        ("psutil", "進程管理"),
        ("numpy", "數值計算")
    ]
    
    all_ok = True
    
    for module, description in dependencies:
        try:
            __import__(module)
            print(f"✓ {module} ({description}) 可用")
        except ImportError:
            print(f"✗ {module} ({description}) 未安裝")
            all_ok = False
    
    return all_ok

def main():
    """主測試函數"""
    print("=" * 50)
    print("Hybrid UI Automation Script - 基本測試")
    print("=" * 50)
    
    # 測試導入
    if not test_imports():
        print("\n❌ 模組導入測試失敗")
        return False
    
    # 測試依賴
    if not test_dependencies():
        print("\n❌ 依賴套件測試失敗")
        print("請執行: pip install -r requirements.txt")
        return False
    
    # 測試基本功能
    if not test_basic_functionality():
        print("\n❌ 基本功能測試失敗")
        return False
    
    print("\n" + "=" * 50)
    print("✅ 所有基本測試通過！")
    print("腳本已準備就緒，可以執行 python main.py")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)