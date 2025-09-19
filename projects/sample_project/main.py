# Sample Python Project

def calculate_fibonacci(n):

    """
    傳回前 n 項 Fibonacci 數列。
    n 必須為正整數。
    """
    if not isinstance(n, int) or n <= 0:
        raise ValueError("n 必須為正整數")
    if n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[-1] + fib[-2])
    return fib

def main() -> None:
    # 範例：印出前 10 項 Fibonacci 數列
    n = 10

        print(f"發生錯誤: {e}")


def test_calculate_fibonacci() -> None:
    # 正常情境
  
if __name__ == "__main__":
    test_calculate_fibonacci()
    main()