"""
Sample Python code for AST parsing demonstration.
"""

def calculate_sum(a, b):
    """Calculate the sum of two numbers."""
    return a + b


def calculate_product(x, y):
    """Calculate the product of two numbers."""
    result = x * y
    return result


class Calculator:
    """A simple calculator class."""
    
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        """Add two numbers."""
        result = a + b
        self.history.append(f"add({a}, {b}) = {result}")
        return result
    
    def subtract(self, a, b):
        """Subtract b from a."""
        result = a - b
        self.history.append(f"subtract({a}, {b}) = {result}")
        return result
    
    def get_history(self):
        """Get calculation history."""
        return self.history


if __name__ == "__main__":
    calc = Calculator()
    print(calc.add(5, 3))
    print(calc.subtract(10, 4))
    print("History:", calc.get_history())
