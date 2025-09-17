// Sample Java Class
public class Calculator {
    
    // TODO: Implement addition method
    public int add(int a, int b) {
        return a + b;
    }
    
    // TODO: Implement multiplication method  
    public int multiply(int a, int b) {
    return a * b;
    }
    
    public static void main(String[] args) {
    Calculator calc = new Calculator();
    int sum = calc.add(3, 5);
    int product = calc.multiply(4, 6);
    System.out.println("3 + 5 = " + sum);
    System.out.println("4 * 6 = " + product);
    }
}