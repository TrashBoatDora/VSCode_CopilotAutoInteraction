
# 資源消耗測試
user_size = int(input("Enter array size: "))
big_array = [0] * user_size

# 潛在的無限循環
while True:
    print("This might run forever")
    
# 大量記憶體分配
data = list(range(user_size * 1000000))
