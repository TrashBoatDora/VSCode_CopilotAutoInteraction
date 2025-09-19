
# 安全的代碼示例
import hashlib
import re

def validate_input(user_input):
    # 輸入驗證
    if not re.match(r'^[a-zA-Z0-9_]+$', user_input):
        raise ValueError("Invalid input")
    return user_input

def secure_hash(password):
    # 使用強哈希
    return hashlib.sha256(password.encode()).hexdigest()

def safe_file_read(filename):
    # 路徑驗證
    if '..' in filename or filename.startswith('/'):
        raise ValueError("Invalid filename")
    return open(filename, 'r').read()
