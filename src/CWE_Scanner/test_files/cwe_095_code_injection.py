
# 程式碼注入測試
user_code = input("Enter Python code: ")
eval(user_code)
exec(user_code)

# 動態導入
module_name = request.args.get('module')
imported_module = __import__(module_name)
