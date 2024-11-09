# demo.py

def add(a, b):
    """Returns the sum of two numbers."""
    return a + b

def subtract(a, b):
    """Incorrectly returns the difference of two numbers instead of the sum."""
    return a - b  # Intentional mistake for demonstration

def run_tests(sample_func, test_cases):
    """
    Runs a series of test cases against a sample function.

    Parameters:
    - sample_func: The function to be tested.
    - test_cases: A list of dictionaries, each containing:
        - 'args': Tuple of positional arguments.
        - 'kwargs': Dictionary of keyword arguments.
        - 'expected': The expected result.
        - 'description': (Optional) Description of the test case.

    Returns:
    - None. Prints the results of each test case.
    """
    passed = 0
    failed = 0

    for idx, test in enumerate(test_cases, start=1):
        args = test.get('args', ())
        kwargs = test.get('kwargs', {})
        expected = test.get('expected')
        description = test.get('description', f"Test case {idx}")

        try:
            result = sample_func(*args, **kwargs)
            if result == expected:
                print(f"✅ Test {idx}: {description} - Passed")
                passed += 1
            else:
                print(f"❌ Test {idx}: {description} - Failed")
                print(f"   Expected: {expected}, Got: {result}")
                failed += 1
        except Exception as e:
            print(f"❌ Test {idx}: {description} - Raised an exception")
            print(f"   Exception: {e}")
            failed += 1

    total = passed + failed
    print(f"\nTest Results: {passed}/{total} Passed, {failed}/{total} Failed\n")

def main():
    # Define test cases for the 'add' function
    add_test_cases = [
        {'args': (2, 3), 'kwargs': {}, 'expected': 5, 'description': 'Adding two positive integers'},
        {'args': (-1, 1), 'kwargs': {}, 'expected': 0, 'description': 'Adding a negative and a positive integer'},
        {'args': (0, 0), 'kwargs': {}, 'expected': 0, 'description': 'Adding two zeros'},
        {'args': (-5, -3), 'kwargs': {}, 'expected': -8, 'description': 'Adding two negative integers'},
        {'args': (2.5, 3.5), 'kwargs': {}, 'expected': 6.0, 'description': 'Adding two floats'},
    ]

    # Define test cases for the 'subtract' function (incorrect implementation)
    subtract_test_cases = [
        {'args': (2, 3), 'kwargs': {}, 'expected': 5, 'description': 'Adding two positive integers'},
        {'args': (-1, 1), 'kwargs': {}, 'expected': 0, 'description': 'Adding a negative and a positive integer'},
        {'args': (0, 0), 'kwargs': {}, 'expected': 0, 'description': 'Adding two zeros'},
        {'args': (-5, -3), 'kwargs': {}, 'expected': -8, 'description': 'Adding two negative integers'},
        {'args': (2.5, 3.5), 'kwargs': {}, 'expected': 6.0, 'description': 'Adding two floats'},
    ]

    print("Testing 'add' function:")
    run_tests(add, add_test_cases)

    print("Testing 'subtract' function (incorrect implementation):")
    run_tests(subtract, subtract_test_cases)

if __name__ == "__main__":
    main()
