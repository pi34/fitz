import unittest
import coverage
import tempfile
import os
import sys
from dataclasses import dataclass
from typing import List

@dataclass
class TestResult:
    score: float
    feedback: List[str]

def run_practice():
    print("🎓 Welcome to the Python Testing Practice Tool!")
    
    # The code to test
    code_to_test = """
def validate_password(password: str) -> bool:
    if not isinstance(password, str):
        raise TypeError("Password must be a string")
        
    if len(password) < 8 or len(password) > 20:
        return False
        
    if ' ' in password:
        return False
        
    if not any(c.isupper() for c in password):
        return False
        
    if not any(c.isdigit() for c in password):
        return False
        
    return True
"""
    
    print("\nHere's the code you need to test:")
    print(code_to_test)
    
    print("\nExample test:")
    print("""
class TestPassword(unittest.TestCase):
    def test_valid_password(self):
        self.assertTrue(validate_password("Valid1Password"))
""")
    
    print("\nWrite your tests (type 'DONE' on a new line when finished):")
    
    # Collect test code
    test_lines = []
    while True:
        line = input()
        if line.strip() == 'DONE':
            break
        test_lines.append(line)
    
    test_code = "\n".join(test_lines)
    
    # Create temporary directory and files
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write the module file
        module_path = os.path.join(tmpdir, 'password_validator.py')
        with open(module_path, 'w') as f:
            f.write(code_to_test)
        
        # Write the test file
        test_path = os.path.join(tmpdir, 'test_password.py')
        with open(test_path, 'w') as f:
            f.write(f"""
import unittest
import sys
import os

# Add the temporary directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from password_validator import validate_password

{test_code}

if __name__ == '__main__':
    unittest.main(argv=['dummy'])
""")
        
        # Set up coverage
        cov = coverage.Coverage(data_file=None)
        cov.start()
        
        # Run the tests
        sys.path.insert(0, tmpdir)
        try:
            __import__('test_password')
        except Exception as e:
            print(f"\n❌ Error in your tests: {str(e)}")
            return
        
        # Stop coverage
        cov.stop()
        
        # Get coverage data
        total = cov.report(show_missing=False)
        
        # Print results
        print(f"\n📊 Results:")
        print(f"Coverage: {total:.1f}%")
        
        # Give feedback
        print("\n💡 Feedback:")
        if "assertRaises" in test_code:
            print("✅ Good job testing for exceptions!")
        else:
            print("⚠️ Consider testing for TypeError with invalid inputs")
            
        if "assertTrue" in test_code and "assertFalse" in test_code:
            print("✅ Good mix of positive and negative test cases!")
        else:
            print("⚠️ Consider testing both valid and invalid passwords")
            
        if total < 80:
            print("\n📝 Suggestions to improve coverage:")
            print("- Test passwords with no uppercase letters")
            print("- Test passwords with no numbers")
            print("- Test passwords with spaces")
            print("- Test passwords that are too short or too long")

if __name__ == "__main__":
    run_practice()