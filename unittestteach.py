import inspect
import unittest
import coverage
import tempfile
import os
from dataclasses import dataclass
from typing import List, Dict, Any
import ast

@dataclass
class TestResult:
    coverage_score: float
    quality_score: float
    total_score: float
    coverage_report: str
    quality_feedback: List[str]

class TestQualityChecker:
    def __init__(self, test_code: str):
        self.test_code = test_code
        self.tree = ast.parse(test_code)
        
    def check_assertions(self) -> List[str]:
        feedback = []
        assertion_count = 0
        unique_assertions = set()
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr.startswith('assert'):
                        assertion_count += 1
                        unique_assertions.add(node.func.attr)
        
        if assertion_count == 0:
            feedback.append("❌ No assertions found in tests")
        else:
            feedback.append(f"✅ Found {assertion_count} assertions")
        
        if len(unique_assertions) == 1:
            feedback.append("⚠️ Consider using different types of assertions")
        elif len(unique_assertions) > 1:
            feedback.append(f"✅ Good variety of assertions: {', '.join(unique_assertions)}")
            
        return feedback
    
    def check_edge_cases(self) -> List[str]:
        feedback = []
        
        # Look for common edge case patterns
        edge_case_patterns = {
            'zero': ['0', '0.0'],
            'negative': ['-', 'negative'],
            'empty': ['empty', '[]', '""', "''"],
            'none': ['None'],
            'large': ['sys.maxsize', 'float("inf")'],
        }
        
        found_patterns = set()
        code_str = self.test_code.lower()
        
        for case, patterns in edge_case_patterns.items():
            if any(pattern.lower() in code_str for pattern in patterns):
                found_patterns.add(case)
        
        if found_patterns:
            feedback.append(f"✅ Testing edge cases: {', '.join(found_patterns)}")
        else:
            feedback.append("⚠️ Consider testing edge cases (zero, negative, empty, None, etc.)")
            
        return feedback

class TestingEducator:
    def __init__(self, code_to_test: str, module_name: str = 'code_under_test'):
        self.code_to_test = code_to_test
        self.module_name = module_name
        
    def evaluate_tests(self, student_tests: str) -> TestResult:
        # Create temporary directory for test files
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Write code under test
            code_path = os.path.join(tmp_dir, f"{self.module_name}.py")
            with open(code_path, 'w') as f:
                f.write(self.code_to_test)
                
            # Write student tests
            test_path = os.path.join(tmp_dir, f"test_{self.module_name}.py")
            with open(test_path, 'w') as f:
                f.write(f"""
import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from {self.module_name} import *

{student_tests}
""")
            
            # Run coverage
            cov = coverage.Coverage(source=[code_path])
            cov.start()
            
            # Run tests
            loader = unittest.TestLoader()
            tests = loader.discover(tmp_dir)
            runner = unittest.TextTestRunner(stream=None)
            test_result = runner.run(tests)
            
            cov.stop()
            
            # Get coverage data
            coverage_percentage = cov.report(show_missing=True)
            
            # Quality checks
            quality_checker = TestQualityChecker(student_tests)
            quality_feedback = (
                quality_checker.check_assertions() +
                quality_checker.check_edge_cases()
            )
            
            # Calculate scores
            coverage_score = coverage_percentage / 100 * 50  # 50% of total score
            
            # Quality score based on feedback
            positive_feedback = len([f for f in quality_feedback if f.startswith('✅')])
            quality_score = (positive_feedback / 4) * 50  # 50% of total score
            
            total_score = coverage_score + quality_score
            
            return TestResult(
                coverage_score=coverage_score,
                quality_score=quality_score,
                total_score=total_score,
                coverage_report=cov.report(show_missing=True),
                quality_feedback=quality_feedback
            )

# Example usage
def main():
    # Example code to test
    code_to_test = """
def calculate_grade(score):
    if not isinstance(score, (int, float)):
        raise TypeError("Score must be a number")
    if score < 0 or score > 100:
        raise ValueError("Score must be between 0 and 100")
    if score >= 90:
        return 'A'
    elif score >= 80:
        return 'B'
    elif score >= 70:
        return 'C'
    elif score >= 60:
        return 'D'
    else:
        return 'F'
"""

    # Example student test
    student_test = """
class TestCalculateGrade(unittest.TestCase):
    def test_grade_a(self):
        self.assertEqual(calculate_grade(95), 'A')
        
    def test_invalid_input(self):
        with self.assertRaises(TypeError):
            calculate_grade("invalid")
            
    def test_negative_score(self):
        with self.assertRaises(ValueError):
            calculate_grade(-1)
"""

    educator = TestingEducator(code_to_test)
    result = educator.evaluate_tests(student_test)
    
    print(f"\nTest Evaluation Results:")
    print(f"Coverage Score: {result.coverage_score:.1f}/50")
    print(f"Quality Score: {result.quality_score:.1f}/50")
    print(f"Total Score: {result.total_score:.1f}/100")
    print("\nQuality Feedback:")
    for feedback in result.quality_feedback:
        print(feedback)

if __name__ == "__main__":
    main()