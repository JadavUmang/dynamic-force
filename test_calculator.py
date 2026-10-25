import unittest
from calculator import add, multiply

class TestCalculator(unittest.TestCase):
    def test_addition(self):
        self.assertEqual(add(2, 3), 5, "2 + 3 should equal 5")
        self.assertEqual(add(10, -4), 6, "10 + (-4) should equal 6")

    def test_multiplication(self):
        self.assertEqual(multiply(4, 5), 20, "4 * 5 should equal 20")

if __name__ == "__main__":
    unittest.main()
