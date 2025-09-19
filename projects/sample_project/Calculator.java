// Sample Java Class
public class Calculator {
    
    /**
     * 傳回兩整數相加的結果。
     */
    public int add(int a, int b) {
        return a + b;
    }

    /**
     * 傳回兩整數相乘的結果。
     */
    public int multiply(int a, int b) {
        return a * b;
    }
    
    public static void main(String[] args) {
        Calculator calc = new Calculator();
        int a = 5, b = 3;
        System.out.println("加法: " + a + " + " + b + " = " + calc.add(a, b));
        System.out.println("乘法: " + a + " * " + b + " = " + calc.multiply(a, b));
    }
}