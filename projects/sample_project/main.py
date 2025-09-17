# Sample Python Project

def calculate_fibonacci(n):
    """Calculate fibonacci sequence up to n terms"""
    if not isinstance(n, int) or n <= 0:
        raise ValueError("n 必須為正整數")
    if n == 1:
        return [0]
    sequence = [0, 1]
    for i in range(2, n):
        sequence.append(sequence[-1] + sequence[-2])
    return sequence[:n]

def main():
    """Main function"""
    try:
        n = 10
        fib_seq = calculate_fibonacci(n)
        print(f"Fibonacci sequence ({n} terms): {fib_seq}")
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()