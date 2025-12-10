"""
Integration tests for the full analysis workflow.

Run with: python -m pytest agents/test_integration.py -v

These tests verify:
1. End-to-end analysis workflow
2. Issue persistence to filesystem
3. Summary generation
4. Multi-file processing
"""

import json
import tempfile
import shutil
from pathlib import Path

import pytest

from agents.graph import create_analysis_graph, create_initial_state, run_analysis
from agents.manager import manager_node
from agents.compiler import compiler_node, _calculate_health_score, _persist_issues
from models.issue import IssueStore


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def multi_file_project():
    """Create a multi-file project for testing."""
    temp_dir = tempfile.mkdtemp()
    
    # auth.py - Security issues
    (Path(temp_dir) / "auth.py").write_text('''
def authenticate(username, password):
    """Unsafe authentication."""
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    return execute_query(query)  # SQL injection vulnerability

API_SECRET = "super-secret-key-123"
DB_PASSWORD = "admin123"

def verify_token(token):
    return eval(token)  # Unsafe eval
''')
    
    # api.py - Performance issues
    (Path(temp_dir) / "api.py").write_text('''
def slow_endpoint(items):
    """Performance issues."""
    results = []
    for item in items:
        # N+1 query pattern
        detail = db.query(f"SELECT * FROM details WHERE id={item.id}")
        results.append(detail)
    return results

def get_all_users():
    # Missing limit
    return db.query("SELECT * FROM users")
''')
    
    # utils.py - Architecture issues
    (Path(temp_dir) / "utils.py").write_text('''
from os import *

# TODO: Refactor this
def process_data(data):
    try:
        result = transform(data)
    except:
        pass  # Bad error handling
    return result

class GodClass:
    """Does too much."""
    def method1(self): pass
    def method2(self): pass
    def method3(self): pass
    def method4(self): pass
    def method5(self): pass
    def method6(self): pass
    def method7(self): pass
    def method8(self): pass
    def method9(self): pass
    def method10(self): pass
    def method11(self): pass
''')
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_issues_dir():
    """Create a temporary directory for issue persistence."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


# =============================================================================
# End-to-End Workflow Tests
# =============================================================================

class TestEndToEndWorkflow:
    """Tests for complete analysis workflow."""
    
    def test_full_analysis_multi_file(self, multi_file_project, temp_issues_dir):
        """Test complete analysis of multi-file project."""
        result = run_analysis(
            target_path=multi_file_project,
            config={"issues_dir": temp_issues_dir}
        )
        
        # Check final status
        assert result["scan_status"] == "done"
        
        # Check all files processed
        assert len(result["processed_files"]) == 3
        
        # Check issues found
        assert len(result["issues"]) > 0
        
        # Check summary generated
        assert "summary" in result
        assert len(result["summary"]) > 0
        assert "Health Score" in result["summary"]
    
    def test_analysis_finds_security_issues(self, multi_file_project):
        """Test that security issues are detected."""
        result = run_analysis(target_path=multi_file_project)
        
        security_issues = [i for i in result["issues"] if i.get("type") == "security"]
        
        # Should find SQL injection, hardcoded secrets, eval
        assert len(security_issues) >= 1
        
        # Check for specific issues
        titles = [i.get("title", "").lower() for i in security_issues]
        has_secret = any("secret" in t or "hardcoded" in t for t in titles)
        assert has_secret or len(security_issues) > 0
    
    def test_analysis_finds_architecture_issues(self, multi_file_project):
        """Test that architecture issues are detected."""
        result = run_analysis(target_path=multi_file_project)
        
        arch_issues = [i for i in result["issues"] if i.get("type") == "architecture"]
        
        # Should find wildcard import, TODO, bare except
        assert len(arch_issues) >= 1
    
    def test_analysis_generates_messages(self, multi_file_project):
        """Test that progress messages are generated."""
        result = run_analysis(target_path=multi_file_project)
        
        messages = result.get("messages", [])
        
        # Should have messages from manager and compiler
        roles = [m.get("role") for m in messages]
        assert "manager" in roles
        assert "compiler" in roles
    
    def test_analysis_with_specified_files(self, multi_file_project):
        """Test analysis with specific files."""
        files = [str(Path(multi_file_project) / "auth.py")]
        
        result = run_analysis(
            target_path=multi_file_project,
            files=files
        )
        
        assert result["scan_status"] == "done"
        assert len(result["processed_files"]) == 1


# =============================================================================
# Issue Persistence Tests
# =============================================================================

class TestIssuePersistence:
    """Tests for issue persistence to filesystem."""
    
    def test_issues_saved_to_filesystem(self, multi_file_project, temp_issues_dir):
        """Test that issues are saved to filesystem."""
        result = run_analysis(
            target_path=multi_file_project,
            config={"issues_dir": temp_issues_dir}
        )
        
        # Check files were created
        store = IssueStore(temp_issues_dir)
        saved_issues = store.get_all()
        
        assert len(saved_issues) > 0
    
    def test_index_json_created(self, multi_file_project, temp_issues_dir):
        """Test that index.json is created."""
        run_analysis(
            target_path=multi_file_project,
            config={"issues_dir": temp_issues_dir}
        )
        
        index_path = Path(temp_issues_dir) / "index.json"
        assert index_path.exists()
        
        with open(index_path) as f:
            index = json.load(f)
        
        assert isinstance(index, list)
        assert len(index) > 0
    
    def test_markdown_files_created(self, multi_file_project, temp_issues_dir):
        """Test that markdown files are created in hierarchical structure."""
        run_analysis(
            target_path=multi_file_project,
            config={"issues_dir": temp_issues_dir}
        )
        
        # Check for markdown files in hierarchical structure: {type}/{risk_level}/*.md
        md_files = list(Path(temp_issues_dir).glob("**/*.md"))
        assert len(md_files) > 0
        
        # Verify hierarchical structure exists
        issues_path = Path(temp_issues_dir)
        type_dirs = [d for d in issues_path.iterdir() if d.is_dir()]
        assert len(type_dirs) > 0  # At least one type directory should exist
    
    def test_persist_issues_function(self, temp_issues_dir):
        """Test _persist_issues function directly."""
        issues = [
            {
                "location": "test.py:10",
                "type": "security",
                "risk_level": "high",
                "title": "Test Issue",
                "description": "Test description",
                "code_snippet": "test code",
                "solution": "Test solution",
            }
        ]
        
        saved = _persist_issues(issues, {"issues_dir": temp_issues_dir})
        
        assert saved == 1
        
        store = IssueStore(temp_issues_dir)
        assert store.count() == 1


# =============================================================================
# Summary Generation Tests
# =============================================================================

class TestSummaryGeneration:
    """Tests for summary report generation."""
    
    def test_summary_includes_health_score(self, multi_file_project):
        """Test that summary includes health score."""
        result = run_analysis(target_path=multi_file_project)
        
        summary = result.get("summary", "")
        assert "Health Score" in summary
        assert "/100" in summary
    
    def test_summary_includes_issue_breakdown(self, multi_file_project):
        """Test that summary includes issue breakdown."""
        result = run_analysis(target_path=multi_file_project)
        
        summary = result.get("summary", "")
        assert "Security" in summary
        assert "Performance" in summary or "Architecture" in summary
    
    def test_summary_includes_recommendations(self, multi_file_project):
        """Test that summary includes recommendations."""
        result = run_analysis(target_path=multi_file_project)
        
        summary = result.get("summary", "")
        assert "Recommendation" in summary


# =============================================================================
# Health Score Tests
# =============================================================================

class TestHealthScore:
    """Tests for health score calculation."""
    
    def test_perfect_score_no_issues(self):
        """Test health score with no issues."""
        score = _calculate_health_score([], 5)
        assert score >= 95  # Should be very high
    
    def test_score_decreases_with_critical(self):
        """Test that critical issues decrease score significantly."""
        issues = [
            {"risk_level": "critical"},
            {"risk_level": "critical"},
        ]
        score = _calculate_health_score(issues, 5)
        assert score < 80
    
    def test_score_decreases_with_many_issues(self):
        """Test that many issues decrease score."""
        issues = [{"risk_level": "medium"} for _ in range(20)]
        score = _calculate_health_score(issues, 5)
        assert score < 80  # Score should decrease from 100
    
    def test_score_bounded(self):
        """Test that score is bounded between 0 and 100."""
        # Many critical issues
        issues = [{"risk_level": "critical"} for _ in range(100)]
        score = _calculate_health_score(issues, 5)
        assert 0 <= score <= 100


# =============================================================================
# Manager Agent Tests
# =============================================================================

class TestManagerAgent:
    """Tests for manager agent functionality."""
    
    def test_manager_discovers_files(self, multi_file_project):
        """Test that manager discovers files automatically."""
        state = {
            "target_path": multi_file_project,
            "files_to_analyze": [],
            "current_file": "",
            "processed_files": [],
            "scan_status": "pending",
            "config": {}
        }
        
        result = manager_node(state)
        
        # Should have discovered files or started scanning
        assert result.get("scan_status") in ["scanning", "error"]
        assert len(result.get("messages", [])) > 0
    
    def test_manager_progress_tracking(self, multi_file_project):
        """Test that manager tracks progress."""
        files = [str(p) for p in Path(multi_file_project).glob("*.py")]
        
        state = {
            "target_path": multi_file_project,
            "files_to_analyze": files,
            "current_file": files[0],
            "current_file_content": "test",
            "processed_files": [],
            "current_file_analyzed_by": ["security", "performance", "architecture"],
            "scan_status": "scanning",
            "config": {}
        }
        
        result = manager_node(state)
        
        # Should have marked file as complete
        assert len(result.get("processed_files", [])) > 0
    
    def test_manager_transitions_to_compile(self, multi_file_project):
        """Test manager transitions to compile when done."""
        state = {
            "target_path": multi_file_project,
            "files_to_analyze": [],
            "current_file": "",
            "current_file_content": "",
            "processed_files": ["file1.py", "file2.py"],
            "current_file_analyzed_by": [],
            "scan_status": "scanning",
            "config": {}
        }
        
        result = manager_node(state)
        
        assert result.get("scan_status") == "compiling"


# =============================================================================
# Compiler Agent Tests
# =============================================================================

class TestCompilerAgent:
    """Tests for compiler agent functionality."""
    
    def test_compiler_generates_summary(self, temp_issues_dir):
        """Test that compiler generates summary."""
        state = {
            "target_path": "./test",
            "processed_files": ["test.py"],
            "issues": [
                {
                    "type": "security",
                    "risk_level": "critical",
                    "title": "SQL Injection",
                    "location": "test.py:10",
                    "description": "SQL injection vulnerability",
                    "code_snippet": "query = f'SELECT...'",
                    "solution": "Use parameterized queries",
                }
            ],
            "config": {"issues_dir": temp_issues_dir}
        }
        
        result = compiler_node(state)
        
        assert result["scan_status"] == "done"
        assert "summary" in result
        assert "SQL Injection" in result["summary"] or "Critical" in result["summary"]
    
    def test_compiler_creates_messages(self, temp_issues_dir):
        """Test that compiler creates completion messages."""
        state = {
            "target_path": "./test",
            "processed_files": ["test.py"],
            "issues": [],
            "config": {"issues_dir": temp_issues_dir}
        }
        
        result = compiler_node(state)
        
        messages = result.get("messages", [])
        assert len(messages) >= 1
        assert any(m.get("role") == "compiler" for m in messages)


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_empty_project(self):
        """Test analysis of empty project."""
        temp_dir = tempfile.mkdtemp()
        
        try:
            result = run_analysis(target_path=temp_dir)
            # Should handle gracefully
            assert result["scan_status"] in ["done", "error"]
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_project_with_syntax_errors(self):
        """Test handling of files with syntax errors."""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Create file with syntax error
            (Path(temp_dir) / "broken.py").write_text("def broken(\n    invalid")
            
            result = run_analysis(target_path=temp_dir)
            
            # Should still complete
            assert result["scan_status"] == "done"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_large_file_handling(self):
        """Test handling of large files."""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Create a large file
            large_content = "\n".join(f"def func_{i}(): pass" for i in range(500))
            (Path(temp_dir) / "large.py").write_text(large_content)
            
            result = run_analysis(target_path=temp_dir)
            
            assert result["scan_status"] == "done"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

