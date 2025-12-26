#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試函式名稱追蹤器功能
"""

import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent))

from src.function_name_tracker import create_function_name_tracker


def test_basic_functionality():
    """測試基本功能"""
    print("=" * 60)
    print("測試 1：基本初始化和記錄功能（使用行號定位）")
    print("=" * 60)
    
    # 建立追蹤器
    tracker = create_function_name_tracker("test_project")
    
    # 記錄第 1 輪的函式變更
    print("\n記錄第 1 輪函式變更...")
    tracker.record_function_change(
        filepath="airflow-core/src/airflow/models/dagbag.py",
        original_name="generate_fernet_key()",
        modified_name="generate_encryption_key()",
        round_num=1,
        original_line=100,
        modified_line=100
    )
    
    tracker.record_function_change(
        filepath="airflow-core/src/airflow/lineage/hook.py",
        original_name="_generate_key()",
        modified_name="_create_secure_key()",
        round_num=1,
        original_line=50,
        modified_line=50
    )
    
    # 記錄第 2 輪的函式變更
    print("\n記錄第 2 輪函式變更...")
    tracker.record_function_change(
        filepath="airflow-core/src/airflow/models/dagbag.py",
        original_name="generate_fernet_key()",
        modified_name="generate_secure_encryption_key()",
        round_num=2,
        original_line=100,
        modified_line=100
    )
    
    print("\n✅ 測試 1 完成")


def test_query_functionality():
    """測試查詢功能"""
    print("\n" + "=" * 60)
    print("測試 2：查詢功能")
    print("=" * 60)
    
    # 建立追蹤器並載入現有資料
    tracker = create_function_name_tracker("test_project")
    
    # 測試查詢最新函式名稱
    print("\n查詢最新函式名稱...")
    latest_name, latest_line = tracker.get_latest_function_name(
        filepath="airflow-core/src/airflow/models/dagbag.py",
        original_name="generate_fernet_key()"
    )
    print(f"  最新名稱: {latest_name}（行 {latest_line}）")
    assert latest_name == "generate_secure_encryption_key()", f"錯誤：應為 'generate_secure_encryption_key()'，實際為 '{latest_name}'"
    
    # 測試查詢特定輪次的函式名稱
    # 注意：get_function_name_for_round 返回的是「該輪 Phase 1 完成後」的名稱
    # 這是因為在 AS 模式中，Phase 2 開始時 Phase 1 已經完成
    print("\n查詢第 1 輪 Phase 1 完成後的函式名稱...")
    round1_name, round1_line = tracker.get_function_name_for_round(
        filepath="airflow-core/src/airflow/models/dagbag.py",
        original_name="generate_fernet_key()",
        target_round=1
    )
    print(f"  第 1 輪名稱: {round1_name}（行 {round1_line}）")
    assert round1_name == "generate_encryption_key()", f"錯誤：第 1 輪 Phase 1 完成後應為 'generate_encryption_key()'，實際為 '{round1_name}'"
    
    print("\n查詢第 2 輪 Phase 1 完成後的函式名稱...")
    round2_name, round2_line = tracker.get_function_name_for_round(
        filepath="airflow-core/src/airflow/models/dagbag.py",
        original_name="generate_fernet_key()",
        target_round=2
    )
    print(f"  第 2 輪名稱: {round2_name}（行 {round2_line}）")
    assert round2_name == "generate_secure_encryption_key()", f"錯誤：第 2 輪 Phase 1 完成後應為 'generate_secure_encryption_key()'，實際為 '{round2_name}'"
    
    print("\n查詢第 3 輪 Phase 1 完成後的函式名稱（無第 3 輪記錄）...")
    round3_name, round3_line = tracker.get_function_name_for_round(
        filepath="airflow-core/src/airflow/models/dagbag.py",
        original_name="generate_fernet_key()",
        target_round=3
    )
    print(f"  第 3 輪名稱: {round3_name}（行 {round3_line}）")
    assert round3_name == "generate_secure_encryption_key()", f"錯誤：第 3 輪應使用第 2 輪的名稱（無第 3 輪記錄），實際為 '{round3_name}'"
    
    print("\n✅ 測試 2 完成")


def test_csv_output():
    """檢查 CSV 輸出"""
    print("\n" + "=" * 60)
    print("測試 3：檢查 CSV 輸出（資料夾結構）")
    print("=" * 60)
    
    csv_dir = Path("ExecutionResult/Success/test_project/FunctionName_query")
    
    if csv_dir.exists():
        print(f"\n✅ CSV 資料夾已建立: {csv_dir}")
        
        # 列出所有 CSV 檔案
        csv_files = list(csv_dir.glob("round*.csv"))
        print(f"\n找到 {len(csv_files)} 個 CSV 檔案:")
        for csv_file in sorted(csv_files):
            print(f"  - {csv_file.name}")
            print(f"\n{csv_file.name} 內容:")
            with open(csv_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(content)
    else:
        print(f"\n❌ CSV 資料夾不存在: {csv_dir}")
    
    print("\n✅ 測試 3 完成")


def main():
    """主測試函數"""
    print("\n" + "=" * 60)
    print("開始測試函式名稱追蹤器")
    print("=" * 60)
    
    try:
        # 測試 1：基本功能
        test_basic_functionality()
        
        # 測試 2：查詢功能
        test_query_functionality()
        
        # 測試 3：CSV 輸出
        test_csv_output()
        
        print("\n" + "=" * 60)
        print("✅ 所有測試通過")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 測試過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
