import hashlib

def hash_password(password: str) -> str:
    """將密碼以 MD5 雜湊後回傳十六進位字串"""
    md5 = hashlib.md5()
    md5.update(password.encode('utf-8'))
    return md5.hexdigest()

if __name__ == "__main__":
    pwd = input("請輸入密碼: ")
    hashed = hash_password(pwd)
    print(f"MD5 雜湊值: {hashed}")
