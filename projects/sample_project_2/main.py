# Sample Python Project

def calculate_fibonacci():
    """Calculate fibonacci sequence up to n terms"""
    n = 10  # 可改為參數
    sequence = [0, 1]
    for i in range(2, n):
        sequence.append(sequence[-1] + sequence[-2])
    return sequence[:n]

def main():
    """Main function"""
    fib_seq = calculate_fibonacci()
    print(f"Fibonacci sequence (10 terms): {fib_seq}")

if __name__ == "__main__":
    main()