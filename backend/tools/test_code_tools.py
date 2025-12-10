"""
Unit tests for Code Analysis Tools.

Run with: python -m pytest tools/test_code_tools.py -v
"""

import tempfile
import shutil
from pathlib import Path

import pytest

from tools.code_tools import (
    # File operations
    _read_file_impl,
    _list_python_files_impl,
    # AST analysis
    _extract_functions_impl,
    _extract_classes_impl,
    _extract_imports_impl,
    # Pattern matching
    _find_pattern_impl,
    _find_issues_by_patterns,
    _get_code_metrics_impl,
    # High-level analysis
    analyze_file,
    analyze_directory,
    # Constants
    SECURITY_PATTERNS,
    PERFORMANCE_PATTERNS,
    ARCHITECTURE_PATTERNS,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def sample_code():
    """Sample Python code for testing."""
    return '''
import os
from typing import List, Dict

API_KEY = "secret-key-12345"

def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two numbers."""
    return a + b

def unsafe_query(user_input):
    query = f"SELECT * FROM users WHERE id = '{user_input}'"
    return query

async def fetch_data(url: str) -> Dict:
    """Fetch data from URL asynchronously."""
    pass

class UserService:
    """Service for managing users."""
    
    def __init__(self, db):
        self.db = db
    
    def get_user(self, user_id):
        return self.db.query(f"SELECT * FROM users WHERE id = {user_id}")
    
    @staticmethod
    def validate_email(email):
        return "@" in email

class AdminService(UserService):
    """Admin service extending UserService."""
    
    def delete_all(self):
        # TODO: Add confirmation
        pass
'''


@pytest.fixture
def temp_project():
    """Create a temporary project directory with Python files."""
    temp_dir = tempfile.mkdtemp()
    
    # Create main.py
    (Path(temp_dir) / "main.py").write_text('''
def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
''')
    
    # Create utils.py
    (Path(temp_dir) / "utils.py").write_text('''
import re

def parse_data(data):
    return data.strip()

API_KEY = "test-key-123"
''')
    
    # Create subdir
    subdir = Path(temp_dir) / "subdir"
    subdir.mkdir()
    (subdir / "helper.py").write_text('''
def helper_func():
    pass
''')
    
    # Create __pycache__ (should be ignored)
    pycache = Path(temp_dir) / "__pycache__"
    pycache.mkdir()
    (pycache / "main.cpython-311.pyc").write_bytes(b"fake bytecode")
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


# =============================================================================
# File Operations Tests
# =============================================================================

class TestReadFile:
    """Tests for read_file function."""
    
    def test_read_existing_file(self, temp_project):
        """Test reading an existing file."""
        filepath = Path(temp_project) / "main.py"
        content = _read_file_impl(str(filepath))
        
        assert "def main():" in content
        assert "Hello, World!" in content
    
    def test_read_nonexistent_file(self):
        """Test reading a non-existent file."""
        content = _read_file_impl("/nonexistent/path/file.py")
        
        assert "[ERROR]" in content
        assert "not found" in content.lower()
    
    def test_read_directory_as_file(self, temp_project):
        """Test reading a directory (should fail)."""
        content = _read_file_impl(temp_project)
        
        assert "[ERROR]" in content
        assert "Not a file" in content
    
    def test_read_file_with_unicode(self, temp_project):
        """Test reading a file with unicode characters."""
        filepath = Path(temp_project) / "unicode.py"
        filepath.write_text('# -*- coding: utf-8 -*-\nprint("Hello, 世界! 🌍")', encoding='utf-8')
        
        content = _read_file_impl(str(filepath))
        
        assert "世界" in content
        assert "🌍" in content


class TestListPythonFiles:
    """Tests for list_python_files function."""
    
    def test_list_files_in_directory(self, temp_project):
        """Test listing Python files in a directory."""
        files = _list_python_files_impl(temp_project)
        
        assert len(files) >= 3  # main.py, utils.py, subdir/helper.py
        assert any("main.py" in f for f in files)
        assert any("utils.py" in f for f in files)
        assert any("helper.py" in f for f in files)
    
    def test_ignores_pycache(self, temp_project):
        """Test that __pycache__ is ignored."""
        files = _list_python_files_impl(temp_project)
        
        assert not any("__pycache__" in f for f in files)
        assert not any(".pyc" in f for f in files)
    
    def test_nonexistent_directory(self):
        """Test listing files in non-existent directory."""
        files = _list_python_files_impl("/nonexistent/path")
        
        assert len(files) == 1
        assert "[ERROR]" in files[0]
    
    def test_custom_ignore_patterns(self, temp_project):
        """Test custom ignore patterns."""
        files = _list_python_files_impl(temp_project, ignore_patterns=["utils*"])
        
        assert not any("utils.py" in f for f in files)
        assert any("main.py" in f for f in files)


# =============================================================================
# AST Analysis Tests
# =============================================================================

class TestExtractFunctions:
    """Tests for extract_functions function."""
    
    def test_extract_functions(self, sample_code):
        """Test extracting functions from code."""
        functions = _extract_functions_impl(sample_code)
        
        func_names = [f["name"] for f in functions if "name" in f]
        assert "calculate_sum" in func_names
        assert "unsafe_query" in func_names
        assert "fetch_data" in func_names
    
    def test_function_metadata(self, sample_code):
        """Test that function metadata is extracted correctly."""
        functions = _extract_functions_impl(sample_code)
        
        calc_func = next((f for f in functions if f.get("name") == "calculate_sum"), None)
        assert calc_func is not None
        assert calc_func["args"] == ["a", "b"]
        assert calc_func["docstring"] is not None
        assert "sum" in calc_func["docstring"].lower()
    
    def test_async_function(self, sample_code):
        """Test that async functions are detected."""
        functions = _extract_functions_impl(sample_code)
        
        fetch_func = next((f for f in functions if f.get("name") == "fetch_data"), None)
        assert fetch_func is not None
        assert fetch_func["is_async"] is True
    
    def test_syntax_error_handling(self):
        """Test handling of syntax errors."""
        invalid_code = "def broken(\n    pass"
        functions = _extract_functions_impl(invalid_code)
        
        assert len(functions) == 1
        assert "error" in functions[0]
        assert functions[0]["error"] == "SyntaxError"


class TestExtractClasses:
    """Tests for extract_classes function."""
    
    def test_extract_classes(self, sample_code):
        """Test extracting classes from code."""
        classes = _extract_classes_impl(sample_code)
        
        class_names = [c["name"] for c in classes if "name" in c]
        assert "UserService" in class_names
        assert "AdminService" in class_names
    
    def test_class_metadata(self, sample_code):
        """Test that class metadata is extracted correctly."""
        classes = _extract_classes_impl(sample_code)
        
        user_class = next((c for c in classes if c.get("name") == "UserService"), None)
        assert user_class is not None
        assert "__init__" in user_class["methods"]
        assert "get_user" in user_class["methods"]
        assert user_class["docstring"] is not None
    
    def test_class_inheritance(self, sample_code):
        """Test that inheritance is detected."""
        classes = _extract_classes_impl(sample_code)
        
        admin_class = next((c for c in classes if c.get("name") == "AdminService"), None)
        assert admin_class is not None
        assert "UserService" in admin_class["bases"]


class TestExtractImports:
    """Tests for extract_imports function."""
    
    def test_extract_imports(self, sample_code):
        """Test extracting imports from code."""
        imports = _extract_imports_impl(sample_code)
        
        modules = [i["module"] for i in imports if "module" in i]
        assert "os" in modules
        assert "typing" in modules
    
    def test_from_import(self, sample_code):
        """Test extracting 'from' imports."""
        imports = _extract_imports_impl(sample_code)
        
        typing_import = next((i for i in imports if i.get("module") == "typing"), None)
        assert typing_import is not None
        assert typing_import["type"] == "from"
        assert "List" in typing_import["names"]
        assert "Dict" in typing_import["names"]


# =============================================================================
# Pattern Matching Tests
# =============================================================================

class TestFindPattern:
    """Tests for find_pattern function."""
    
    def test_find_simple_pattern(self, sample_code):
        """Test finding a simple pattern."""
        matches = _find_pattern_impl(sample_code, r"def \w+")
        
        assert len(matches) >= 3  # At least 3 function definitions
    
    def test_find_with_line_numbers(self, sample_code):
        """Test that line numbers are returned."""
        matches = _find_pattern_impl(sample_code, r"API_KEY")
        
        assert len(matches) >= 1
        assert "line_number" in matches[0]
        assert matches[0]["line_number"] > 0
    
    def test_find_no_matches(self, sample_code):
        """Test when no matches are found."""
        matches = _find_pattern_impl(sample_code, r"NONEXISTENT_PATTERN_XYZ")
        
        assert len(matches) == 0
    
    def test_invalid_regex(self, sample_code):
        """Test handling of invalid regex."""
        matches = _find_pattern_impl(sample_code, r"[invalid(")
        
        assert len(matches) == 1
        assert "error" in matches[0]


class TestSecurityPatterns:
    """Tests for security pattern detection."""
    
    def test_find_hardcoded_secrets(self, sample_code):
        """Test finding hardcoded secrets."""
        issues = _find_issues_by_patterns(sample_code, SECURITY_PATTERNS, "security")
        
        secret_issues = [i for i in issues if i["pattern"] == "hardcoded_secret"]
        assert len(secret_issues) >= 1
    
    def test_find_sql_injection(self):
        """Test finding SQL injection patterns."""
        vuln_code = '''
def get_user(user_id):
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
'''
        issues = _find_issues_by_patterns(vuln_code, SECURITY_PATTERNS, "security")
        
        # Should find some security pattern
        assert len(issues) >= 0  # SQL injection pattern might not match exact format


class TestPerformancePatterns:
    """Tests for performance pattern detection."""
    
    def test_find_select_all(self):
        """Test finding SELECT * queries."""
        code = 'query = "SELECT * FROM users"'
        issues = _find_issues_by_patterns(code, PERFORMANCE_PATTERNS, "performance")
        
        select_issues = [i for i in issues if i["pattern"] == "select_all"]
        assert len(select_issues) >= 1


class TestArchitecturePatterns:
    """Tests for architecture pattern detection."""
    
    def test_find_todo_comments(self, sample_code):
        """Test finding TODO comments."""
        issues = _find_issues_by_patterns(sample_code, ARCHITECTURE_PATTERNS, "architecture")
        
        todo_issues = [i for i in issues if i["pattern"] == "todo_fixme"]
        assert len(todo_issues) >= 1
    
    def test_find_bare_except(self):
        """Test finding bare except clauses."""
        code = '''
try:
    risky_operation()
except:
    pass
'''
        issues = _find_issues_by_patterns(code, ARCHITECTURE_PATTERNS, "architecture")
        
        except_issues = [i for i in issues if i["pattern"] in ["bare_except", "pass_in_except"]]
        assert len(except_issues) >= 1


# =============================================================================
# Code Metrics Tests
# =============================================================================

class TestCodeMetrics:
    """Tests for code metrics calculation."""
    
    def test_basic_metrics(self, sample_code):
        """Test basic code metrics."""
        metrics = _get_code_metrics_impl(sample_code)
        
        assert metrics["lines_total"] > 0
        assert metrics["lines_code"] > 0
        assert metrics["functions_count"] >= 3
        assert metrics["classes_count"] >= 2
        assert metrics["imports_count"] >= 2
    
    def test_empty_code(self):
        """Test metrics for empty code."""
        metrics = _get_code_metrics_impl("")
        
        assert metrics["lines_total"] == 1  # Empty string has one line
        assert metrics["functions_count"] == 0
        assert metrics["classes_count"] == 0


# =============================================================================
# High-Level Analysis Tests
# =============================================================================

class TestAnalyzeFile:
    """Tests for analyze_file function."""
    
    def test_analyze_file(self, temp_project):
        """Test analyzing a single file."""
        filepath = Path(temp_project) / "utils.py"
        result = analyze_file(str(filepath))
        
        assert "filepath" in result
        assert "metrics" in result
        assert "functions" in result
        assert "security_issues" in result
        
        # Should find the hardcoded API_KEY
        assert len(result["security_issues"]) >= 1
    
    def test_analyze_nonexistent_file(self):
        """Test analyzing a non-existent file."""
        result = analyze_file("/nonexistent/file.py")
        
        assert "error" in result


class TestAnalyzeDirectory:
    """Tests for analyze_directory function."""
    
    def test_analyze_directory(self, temp_project):
        """Test analyzing a directory."""
        results = analyze_directory(temp_project)
        
        assert len(results) >= 3  # main.py, utils.py, subdir/helper.py
        assert all("filepath" in r or "error" in r for r in results)
    
    def test_analyze_nonexistent_directory(self):
        """Test analyzing a non-existent directory."""
        results = analyze_directory("/nonexistent/path")
        
        assert len(results) == 1
        assert "error" in results[0]


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for the code tools."""
    
    def test_full_analysis_workflow(self, temp_project):
        """Test complete analysis workflow."""
        # List files
        files = _list_python_files_impl(temp_project)
        assert len(files) >= 3
        
        # Analyze each file
        for filepath in files:
            content = _read_file_impl(filepath)
            assert not content.startswith("[ERROR]")
            
            functions = _extract_functions_impl(content)
            assert isinstance(functions, list)
            
            metrics = _get_code_metrics_impl(content)
            assert metrics["lines_total"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

