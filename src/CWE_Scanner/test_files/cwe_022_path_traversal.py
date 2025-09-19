
# 路徑遍歷測試
import os
filename = input("Enter filename: ")
with open(filename, 'r') as f:
    content = f.read()

# 危險的路徑拼接
file_path = "../../../etc/passwd"
