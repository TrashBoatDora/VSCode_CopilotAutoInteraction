
# 弱加密演算法測試
import hashlib
import md5

password = "secret123"
weak_hash = hashlib.md5(password.encode()).hexdigest()
another_weak = hashlib.sha1(password.encode()).hexdigest()

# DES 加密 (已過時)
from Crypto.Cipher import DES
cipher = DES.new(b'key12345', DES.MODE_ECB)
