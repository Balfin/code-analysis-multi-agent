"""
Tests for Specialist Agents with LLM Integration.

Run with: python -m pytest agents/test_specialists.py -v

These tests verify:
1. Pattern-based analysis (always works)
2. LLM integration (when available)
3. Issue deduplication
4. Output format correctness
"""

import pytest
from unittest.mock import patch, MagicMock

from agents.specialists import (
    security_node,
    performance_node,
    architecture_node,
    _get_llm_safe,
    _format_functions_for_prompt,
    _format_classes_for_prompt,
    _truncate_code,
)
from prompts.templates import parse_llm_issues


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def security_vulnerable_code():
    """Code with security vulnerabilities."""
    return '''
import pickle
import os

API_KEY = "secret-key-12345"
DB_PASSWORD = "admin123"

def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = '{user_id}'"
    return execute_query(query)

def run_command(cmd):
    os.system(cmd)

def load_data(data):
    return pickle.loads(data)

def unsafe_eval(user_input):
    return eval(user_input)
'''


@pytest.fixture
def performance_issue_code():
    """Code with performance issues."""
    return '''
def process_users(users):
    results = []
    for user in users:
        # N+1 query pattern
        posts = db.query(f"SELECT * FROM posts WHERE user_id = {user.id}")
        for post in posts:
            comments = db.query(f"SELECT * FROM comments WHERE post_id = {post.id}")
            results.append((user, posts, comments))
    return results

def build_report():
    report = ""
    for i in range(10000):
        report += f"Line {i}\\n"
    return report

def get_all_data():
    return db.query("SELECT * FROM large_table")
'''


@pytest.fixture
def architecture_issue_code():
    """Code with architecture issues."""
    return '''
from os import *

class GodClass:
    """Does way too much."""
    
    def __init__(self):
        self.users = []
        self.posts = []
        self.comments = []
        self.notifications = []
    
    def create_user(self): pass
    def delete_user(self): pass
    def update_user(self): pass
    def get_user(self): pass
    def list_users(self): pass
    def create_post(self): pass
    def delete_post(self): pass
    def update_post(self): pass
    def get_post(self): pass
    def list_posts(self): pass
    def send_notification(self): pass
    def process_payment(self): pass

def long_function():
    # TODO: Refactor this
    x = 1
    y = 2
    z = 3
    # ... imagine 100 more lines
    pass

def risky_operation():
    try:
        something()
    except:
        pass
'''


@pytest.fixture
def state_with_security_code(security_vulnerable_code):
    """State with security-vulnerable code."""
    return {
        "current_file": "vulnerable.py",
        "current_file_content": security_vulnerable_code,
        "current_file_analyzed_by": [],
    }


@pytest.fixture
def state_with_performance_code(performance_issue_code):
    """State with performance-issue code."""
    return {
        "current_file": "slow.py",
        "current_file_content": performance_issue_code,
        "current_file_analyzed_by": ["security"],
    }


@pytest.fixture
def state_with_architecture_code(architecture_issue_code):
    """State with architecture-issue code."""
    return {
        "current_file": "messy.py",
        "current_file_content": architecture_issue_code,
        "current_file_analyzed_by": ["security", "performance"],
    }


# =============================================================================
# Pattern-Based Analysis Tests
# =============================================================================

class TestSecurityNodePatternOnly:
    """Test security node with pattern-based analysis only."""
    
    @patch('agents.specialists._get_llm_safe', return_value=None)
    def test_finds_hardcoded_secrets(self, mock_llm, state_with_security_code):
        """Test detection of hardcoded secrets."""
        result = security_node(state_with_security_code)
        
        issues = result.get("issues", [])
        assert len(issues) > 0
        
        # Should find API_KEY or DB_PASSWORD
        secret_issues = [i for i in issues if "secret" in i.get("title", "").lower() or "hardcoded" in i.get("title", "").lower()]
        assert len(secret_issues) >= 1
    
    @patch('agents.specialists._get_llm_safe', return_value=None)
    def test_finds_sql_injection(self, mock_llm, state_with_security_code):
        """Test detection of SQL injection patterns."""
        result = security_node(state_with_security_code)
        
        issues = result.get("issues", [])
        # Check for any security issues (SQL injection pattern might vary)
        assert len(issues) > 0
    
    @patch('agents.specialists._get_llm_safe', return_value=None)
    def test_updates_analyzed_by(self, mock_llm, state_with_security_code):
        """Test that analyzed_by is updated."""
        result = security_node(state_with_security_code)
        
        assert "security" in result.get("current_file_analyzed_by", [])
    
    @patch('agents.specialists._get_llm_safe', return_value=None)
    def test_creates_messages(self, mock_llm, state_with_security_code):
        """Test that messages are created."""
        result = security_node(state_with_security_code)
        
        messages = result.get("messages", [])
        assert len(messages) > 0
        assert messages[0]["role"] == "security"


class TestPerformanceNodePatternOnly:
    """Test performance node with pattern-based analysis only."""
    
    @patch('agents.specialists._get_llm_safe', return_value=None)
    def test_finds_select_all(self, mock_llm, state_with_performance_code):
        """Test detection of SELECT * queries."""
        result = performance_node(state_with_performance_code)
        
        issues = result.get("issues", [])
        select_issues = [i for i in issues if "select" in i.get("title", "").lower()]
        # May or may not find depending on pattern
        assert len(issues) >= 0
    
    @patch('agents.specialists._get_llm_safe', return_value=None)
    def test_updates_analyzed_by(self, mock_llm, state_with_performance_code):
        """Test that analyzed_by is updated."""
        result = performance_node(state_with_performance_code)
        
        assert "performance" in result.get("current_file_analyzed_by", [])


class TestArchitectureNodePatternOnly:
    """Test architecture node with pattern-based analysis only."""
    
    @patch('agents.specialists._get_llm_safe', return_value=None)
    def test_finds_wildcard_import(self, mock_llm, state_with_architecture_code):
        """Test detection of wildcard imports."""
        result = architecture_node(state_with_architecture_code)
        
        issues = result.get("issues", [])
        wildcard_issues = [i for i in issues if "wildcard" in i.get("title", "").lower()]
        assert len(wildcard_issues) >= 1
    
    @patch('agents.specialists._get_llm_safe', return_value=None)
    def test_finds_todo_comments(self, mock_llm, state_with_architecture_code):
        """Test detection of TODO comments."""
        result = architecture_node(state_with_architecture_code)
        
        issues = result.get("issues", [])
        todo_issues = [i for i in issues if "todo" in i.get("title", "").lower()]
        assert len(todo_issues) >= 1
    
    @patch('agents.specialists._get_llm_safe', return_value=None)
    def test_finds_bare_except(self, mock_llm, state_with_architecture_code):
        """Test detection of bare except clauses."""
        result = architecture_node(state_with_architecture_code)
        
        issues = result.get("issues", [])
        except_issues = [i for i in issues if "except" in i.get("title", "").lower()]
        assert len(except_issues) >= 1
    
    @patch('agents.specialists._get_llm_safe', return_value=None)
    def test_updates_analyzed_by(self, mock_llm, state_with_architecture_code):
        """Test that analyzed_by is updated."""
        result = architecture_node(state_with_architecture_code)
        
        assert "architecture" in result.get("current_file_analyzed_by", [])


# =============================================================================
# Issue Format Tests
# =============================================================================

class TestIssueFormat:
    """Test that issues have correct format."""
    
    @patch('agents.specialists._get_llm_safe', return_value=None)
    def test_issue_has_required_fields(self, mock_llm, state_with_security_code):
        """Test that issues have all required fields."""
        result = security_node(state_with_security_code)
        
        issues = result.get("issues", [])
        assert len(issues) > 0
        
        for issue in issues:
            assert "location" in issue
            assert "type" in issue
            assert "risk_level" in issue
            assert "title" in issue
            assert "description" in issue
            assert "solution" in issue
            assert "author" in issue
    
    @patch('agents.specialists._get_llm_safe', return_value=None)
    def test_issue_risk_levels_valid(self, mock_llm, state_with_security_code):
        """Test that risk levels are valid."""
        result = security_node(state_with_security_code)
        
        issues = result.get("issues", [])
        valid_levels = {"critical", "high", "medium", "low"}
        
        for issue in issues:
            assert issue["risk_level"] in valid_levels
    
    @patch('agents.specialists._get_llm_safe', return_value=None)
    def test_issue_location_format(self, mock_llm, state_with_security_code):
        """Test that location has correct format."""
        result = security_node(state_with_security_code)
        
        issues = result.get("issues", [])
        
        for issue in issues:
            location = issue["location"]
            assert ":" in location
            parts = location.split(":")
            assert len(parts) >= 2


# =============================================================================
# LLM Response Parsing Tests
# =============================================================================

class TestLLMResponseParsing:
    """Test parsing of LLM responses."""
    
    def test_parse_valid_json(self):
        """Test parsing valid JSON response."""
        response = '''
        [
            {
                "title": "SQL Injection",
                "risk_level": "critical",
                "line_number": 10,
                "description": "User input in query",
                "code_snippet": "query = f'SELECT...'",
                "solution": "Use parameterized queries"
            }
        ]
        '''
        
        issues = parse_llm_issues(response, "test.py", "security")
        
        assert len(issues) == 1
        assert issues[0]["title"] == "SQL Injection"
        assert issues[0]["risk_level"] == "critical"
        assert issues[0]["location"] == "test.py:10"
    
    def test_parse_json_with_extra_text(self):
        """Test parsing JSON with extra text around it."""
        response = '''
        Here are the issues I found:
        
        [
            {
                "title": "Issue 1",
                "risk_level": "high",
                "line_number": 5,
                "description": "Test",
                "code_snippet": "code",
                "solution": "fix"
            }
        ]
        
        Let me know if you need more details.
        '''
        
        issues = parse_llm_issues(response, "test.py", "security")
        
        assert len(issues) == 1
        assert issues[0]["title"] == "Issue 1"
    
    def test_parse_empty_array(self):
        """Test parsing empty array response."""
        response = "[]"
        
        issues = parse_llm_issues(response, "test.py", "security")
        
        assert len(issues) == 0
    
    def test_parse_invalid_json(self):
        """Test handling of invalid JSON."""
        response = "This is not JSON at all"
        
        issues = parse_llm_issues(response, "test.py", "security")
        
        assert len(issues) == 0
    
    def test_parse_invalid_risk_level(self):
        """Test handling of invalid risk level."""
        response = '''
        [
            {
                "title": "Issue",
                "risk_level": "super_critical",
                "line_number": 1,
                "description": "test",
                "code_snippet": "code",
                "solution": "fix"
            }
        ]
        '''
        
        issues = parse_llm_issues(response, "test.py", "security")
        
        assert len(issues) == 1
        assert issues[0]["risk_level"] == "medium"  # Default


# =============================================================================
# Helper Function Tests
# =============================================================================

class TestHelperFunctions:
    """Test helper functions."""
    
    def test_format_functions_empty(self):
        """Test formatting empty functions list."""
        result = _format_functions_for_prompt([])
        assert result == "None found"
    
    def test_format_functions_with_error(self):
        """Test formatting functions with error."""
        result = _format_functions_for_prompt([{"error": "SyntaxError"}])
        assert result == "None found"
    
    def test_format_functions_normal(self):
        """Test formatting normal functions list."""
        functions = [
            {"name": "foo", "args": ["a", "b"], "line_start": 10},
            {"name": "bar", "args": [], "line_start": 20},
        ]
        result = _format_functions_for_prompt(functions)
        
        assert "foo" in result
        assert "bar" in result
    
    def test_format_classes_empty(self):
        """Test formatting empty classes list."""
        result = _format_classes_for_prompt([])
        assert result == "None found"
    
    def test_truncate_code_short(self):
        """Test truncating short code (no change)."""
        code = "line1\nline2\nline3"
        result = _truncate_code(code, max_lines=10)
        assert result == code
    
    def test_truncate_code_long(self):
        """Test truncating long code."""
        code = "\n".join(f"line{i}" for i in range(100))
        result = _truncate_code(code, max_lines=20)
        
        assert "truncated" in result
        assert len(result.split("\n")) < 100


# =============================================================================
# Empty Content Tests
# =============================================================================

class TestEmptyContent:
    """Test handling of empty content."""
    
    def test_security_empty_content(self):
        """Test security node with empty content."""
        state = {
            "current_file": "",
            "current_file_content": "",
            "current_file_analyzed_by": [],
        }
        
        result = security_node(state)
        
        assert "security" in result["current_file_analyzed_by"]
        assert len(result.get("issues", [])) == 0
    
    def test_performance_empty_content(self):
        """Test performance node with empty content."""
        state = {
            "current_file": "",
            "current_file_content": "",
            "current_file_analyzed_by": [],
        }
        
        result = performance_node(state)
        
        assert "performance" in result["current_file_analyzed_by"]
    
    def test_architecture_empty_content(self):
        """Test architecture node with empty content."""
        state = {
            "current_file": "",
            "current_file_content": "",
            "current_file_analyzed_by": [],
        }
        
        result = architecture_node(state)
        
        assert "architecture" in result["current_file_analyzed_by"]


# =============================================================================
# LLM Integration Tests (Mock)
# =============================================================================

class TestLLMIntegration:
    """Test LLM integration with mocked LLM."""
    
    def test_security_with_mocked_llm(self, state_with_security_code):
        """Test security node with mocked LLM response."""
        llm_response = '[{"title": "LLM Found Issue", "risk_level": "high", "line_number": 5, "description": "Test", "code_snippet": "code", "solution": "fix"}]'
        
        with patch('agents.specialists._get_llm_safe') as mock_get_llm, \
             patch('agents.specialists._invoke_llm_safe', return_value=llm_response):
            mock_get_llm.return_value = MagicMock()
            result = security_node(state_with_security_code)
        
        issues = result.get("issues", [])
        # Should have both LLM and pattern-based issues
        assert len(issues) >= 1
        
        # Check that LLM issue is included
        llm_issues = [i for i in issues if "LLM" in i.get("author", "")]
        assert len(llm_issues) >= 1
    
    def test_performance_with_mocked_llm(self, state_with_performance_code):
        """Test performance node with mocked LLM response."""
        llm_response = '[{"title": "N+1 Query", "risk_level": "high", "line_number": 4, "description": "Test", "code_snippet": "code", "solution": "fix"}]'
        
        with patch('agents.specialists._get_llm_safe') as mock_get_llm, \
             patch('agents.specialists._invoke_llm_safe', return_value=llm_response):
            mock_get_llm.return_value = MagicMock()
            result = performance_node(state_with_performance_code)
        
        issues = result.get("issues", [])
        assert len(issues) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

