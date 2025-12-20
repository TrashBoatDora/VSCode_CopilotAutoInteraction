#!/bin/bash
# =============================================================================
# Copilot Auto Interaction 環境安裝腳本
# =============================================================================
# 此腳本用於在新機器上重建 copilot_py310 環境
#
# 使用方式:
#   chmod +x install_env.sh
#   ./install_env.sh
#
# 必要條件:
#   - 已安裝 Anaconda/Miniconda
#   - 位於專案根目錄
# =============================================================================

set -e  # 遇到錯誤立即退出

echo "=========================================="
echo "Copilot Auto Interaction 環境安裝程式"
echo "=========================================="
echo ""

# 檢查是否有 conda
if ! command -v conda &> /dev/null; then
    echo "❌ 錯誤: 未找到 conda 命令"
    echo "請先安裝 Anaconda 或 Miniconda:"
    echo "  https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# 初始化 conda
echo "📌 初始化 conda..."
CONDA_BASE=$(conda info --base)
source "${CONDA_BASE}/etc/profile.d/conda.sh"

# 檢查環境是否已存在
if conda env list | grep -q "^copilot_py310"; then
    echo "⚠️  警告: copilot_py310 環境已存在"
    read -p "是否要刪除並重建? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  移除舊環境..."
        conda env remove -n copilot_py310 -y
    else
        echo "❌ 已取消安裝"
        exit 0
    fi
fi

# 方法 1: 使用 environment.yml (推薦)
if [ -f "environment.yml" ]; then
    echo "✅ 找到 environment.yml，使用此檔案建立環境..."
    echo "📦 正在建立 copilot_py310 環境 (這可能需要幾分鐘)..."
    conda env create -f environment.yml
    
    echo ""
    echo "✅ 環境建立成功！"
    
else
    # 方法 2: 使用 requirements.txt (備用方案)
    echo "⚠️  未找到 environment.yml，使用 requirements.txt..."
    
    if [ ! -f "requirements.txt" ]; then
        echo "❌ 錯誤: 找不到 environment.yml 或 requirements.txt"
        exit 1
    fi
    
    echo "📦 建立基礎 Python 3.10.12 環境..."
    conda create -n copilot_py310 python=3.10.12 -y
    
    echo "📦 啟動環境並安裝套件..."
    conda activate copilot_py310
    pip install -r requirements.txt
    
    echo ""
    echo "✅ 環境建立成功！"
fi

# 檢查並安裝 Linux 剪貼簿工具 (xclip)
# 這是 Pyperclip 在 Linux 上正常運作所必需的
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo ""
    echo "🔍 檢查 Linux 剪貼簿工具..."
    
    # 先啟動環境以檢查環境內的工具
    conda activate copilot_py310
    
    if ! command -v xclip &> /dev/null && ! command -v xsel &> /dev/null && ! command -v wl-copy &> /dev/null; then
        echo "⚠️  未檢測到剪貼簿工具 (xclip, xsel, 或 wl-clipboard)"
        echo "📦 嘗試透過 conda 安裝 xclip..."
        
        if conda install -c conda-forge xclip -y; then
            echo "✅ xclip 安裝成功"
        else
            echo "❌ conda 安裝 xclip 失敗"
            echo "📌 建議手動安裝系統套件: sudo apt-get install xclip"
            echo "   或者: sudo apt-get install xsel"
        fi
    else
        echo "✅ 檢測到剪貼簿工具"
    fi
fi

# 驗證安裝
echo ""
echo "=========================================="
echo "驗證安裝結果"
echo "=========================================="

conda activate copilot_py310

echo "✓ Python 版本:"
python --version

echo ""
echo "✓ 關鍵套件版本:"
echo "  - Bandit:  $(bandit --version | head -n1)"
echo "  - Semgrep: $(semgrep --version)"
echo "  - NumPy:   $(python -c 'import numpy; print(numpy.__version__)')"
echo "  - OpenCV:  $(python -c 'import cv2; print(cv2.__version__)')"

echo ""
echo "=========================================="
echo "安裝完成！"
echo "=========================================="
echo ""
echo "現在可以使用以下命令啟動環境:"
echo "  source activate_env.sh"
echo ""
echo "或手動啟動:"
echo "  conda activate copilot_py310"
echo ""
echo "然後執行主程式:"
echo "  python main.py"
echo ""
echo "=========================================="
