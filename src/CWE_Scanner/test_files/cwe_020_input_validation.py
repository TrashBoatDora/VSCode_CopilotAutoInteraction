
# 不當的輸入驗證測試
user_input = input("Enter your name: ")
exec("print('Hello, " + user_input + "')")

request_data = request.args.get('data')
result = eval(request_data)
