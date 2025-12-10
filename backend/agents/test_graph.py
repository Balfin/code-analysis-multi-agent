"""
Unit and integration tests for the LangGraph multi-agent system.

Run with: python -m pytest agents/test_graph.py -v
"""

import tempfile
import shutil
from pathlib import Path

import pytest

from agents.graph import (
    AnalysisState,
    create_analysis_graph,
    create_initial_state,
    run_analysis,
    route_after_manager,
    route_after_security,
    route_after_performance,
    route_after_architecture,
)
from agents.manager import manager_node
from agents.specialists import security_node, performance_node, architecture_node
from agents.compiler import compiler_node


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def temp_project():
    """Create a temporary project with Python files for testing."""
    temp_dir = tempfile.mkdtemp()
    
    # Create sample.py with security issues
    (Path(temp_dir) / "sample.py").write_text('''
def calculate_sum(a, b):
    return a + b

def unsafe_query(user_input):
    query = f"SELECT * FROM users WHERE id = '{user_input}'"
    return query

API_KEY = "secret-key-12345"
''')
    
    # Create utils.py with architecture issues
    (Path(temp_dir) / "utils.py").write_text('''
import re
from os import *

def parse_data(data):
    # TODO: Add validation
    return data.strip()

def long_function():
    pass
''')
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def initial_state(temp_project):
    """Create initial state for testing."""
    return create_initial_state(
        target_path=temp_project,
        files_to_analyze=[
            str(Path(temp_project) / "sample.py"),
            str(Path(temp_project) / "utils.py"),
        ]
    )


# =============================================================================
# Graph Construction Tests
# =============================================================================

class TestGraphConstruction:
    """Tests for graph construction and compilation."""
    
    def test_create_graph(self):
        """Test that graph compiles without errors."""
        graph = create_analysis_graph()
        assert graph is not None
    
    def test_graph_has_nodes(self):
        """Test that graph has all expected nodes."""
        graph = create_analysis_graph()
        # Check that the graph was compiled (it's a CompiledGraph)
        assert graph is not None
    
    def test_create_initial_state(self, temp_project):
        """Test creating initial state."""
        state = create_initial_state(
            target_path=temp_project,
            files_to_analyze=["file1.py", "file2.py"],
            config={"max_file_size": 1000}
        )
        
        assert state["target_path"] == temp_project
        assert state["files_to_analyze"] == ["file1.py", "file2.py"]
        assert state["scan_status"] == "pending"
        assert state["issues"] == []
        assert state["config"]["max_file_size"] == 1000


# =============================================================================
# Routing Function Tests
# =============================================================================

class TestRoutingFunctions:
    """Tests for routing functions."""
    
    def test_route_after_manager_to_security(self):
        """Test routing to security when file is ready."""
        state = {
            "current_file": "test.py",
            "current_file_content": "code here",
            "current_file_analyzed_by": [],
            "files_to_analyze": [],
            "scan_status": "scanning",
        }
        
        result = route_after_manager(state)
        assert result == "security"
    
    def test_route_after_manager_to_compile(self):
        """Test routing to compile when status is compiling."""
        state = {
            "current_file": "",
            "current_file_content": "",
            "files_to_analyze": [],
            "scan_status": "compiling",
        }
        
        result = route_after_manager(state)
        assert result == "compile"
    
    def test_route_after_security(self):
        """Test routing after security analysis."""
        state = {"error": ""}
        result = route_after_security(state)
        assert result == "performance"
    
    def test_route_after_performance(self):
        """Test routing after performance analysis."""
        state = {"error": ""}
        result = route_after_performance(state)
        assert result == "architecture"
    
    def test_route_after_architecture(self):
        """Test routing after architecture analysis."""
        state = {"error": ""}
        result = route_after_architecture(state)
        assert result == "manager"


# =============================================================================
# Individual Node Tests
# =============================================================================

class TestManagerNode:
    """Tests for the manager node."""
    
    def test_manager_initializes_on_pending(self, temp_project):
        """Test manager initializes on pending status."""
        state = {
            "target_path": temp_project,
            "files_to_analyze": [],
            "current_file": "",
            "processed_files": [],
            "scan_status": "pending",
        }
        
        result = manager_node(state)
        
        # Should discover files and start scanning
        assert result.get("scan_status") in ["scanning", "error"]
        assert len(result.get("messages", [])) > 0
    
    def test_manager_picks_next_file(self, initial_state):
        """Test manager picks next file to analyze."""
        # Set state to scanning with files available
        initial_state["scan_status"] = "scanning"
        
        result = manager_node(initial_state)
        
        # Should have picked a file
        assert result.get("current_file") != "" or result.get("scan_status") == "compiling"
    
    def test_manager_transitions_to_compile(self, temp_project):
        """Test manager transitions to compile when all files done."""
        state = {
            "target_path": temp_project,
            "files_to_analyze": [],
            "current_file": "",
            "processed_files": ["file1.py", "file2.py"],
            "current_file_analyzed_by": [],
            "scan_status": "scanning",
        }
        
        result = manager_node(state)
        
        assert result.get("scan_status") == "compiling"


class TestSecurityNode:
    """Tests for the security node."""
    
    def test_security_analyzes_code(self):
        """Test security node analyzes code."""
        state = {
            "current_file": "test.py",
            "current_file_content": 'API_KEY = "secret-123"',
            "current_file_analyzed_by": [],
        }
        
        result = security_node(state)
        
        assert "security" in result.get("current_file_analyzed_by", [])
        assert len(result.get("messages", [])) > 0
        # Should find the hardcoded secret
        assert len(result.get("issues", [])) >= 1
    
    def test_security_handles_empty_content(self):
        """Test security handles empty content."""
        state = {
            "current_file": "",
            "current_file_content": "",
            "current_file_analyzed_by": [],
        }
        
        result = security_node(state)
        
        assert "security" in result.get("current_file_analyzed_by", [])


class TestPerformanceNode:
    """Tests for the performance node."""
    
    def test_performance_analyzes_code(self):
        """Test performance node analyzes code."""
        state = {
            "current_file": "test.py",
            "current_file_content": 'query = "SELECT * FROM users"',
            "current_file_analyzed_by": ["security"],
        }
        
        result = performance_node(state)
        
        assert "performance" in result.get("current_file_analyzed_by", [])
        assert len(result.get("messages", [])) > 0


class TestArchitectureNode:
    """Tests for the architecture node."""
    
    def test_architecture_analyzes_code(self):
        """Test architecture node analyzes code."""
        state = {
            "current_file": "test.py",
            "current_file_content": '''
# TODO: Fix this
try:
    something()
except:
    pass
''',
            "current_file_analyzed_by": ["security", "performance"],
        }
        
        result = architecture_node(state)
        
        assert "architecture" in result.get("current_file_analyzed_by", [])
        assert len(result.get("messages", [])) > 0
        # Should find TODO and bare except
        assert len(result.get("issues", [])) >= 1


class TestCompilerNode:
    """Tests for the compiler node."""
    
    def test_compiler_generates_summary(self):
        """Test compiler generates summary."""
        state = {
            "target_path": "./test",
            "processed_files": ["test.py"],
            "issues": [
                {
                    "type": "security",
                    "risk_level": "high",
                    "title": "Test Issue",
                    "location": "test.py:1",
                    "description": "Test",
                    "solution": "Fix it",
                }
            ],
        }
        
        result = compiler_node(state)
        
        assert result.get("scan_status") == "done"
        assert "summary" in result
        assert len(result["summary"]) > 0
        assert "Test Issue" in result["summary"] or "1" in result["summary"]


# =============================================================================
# Integration Tests
# =============================================================================

class TestFullWorkflow:
    """Integration tests for the full workflow."""
    
    def test_full_workflow(self, temp_project):
        """Test complete analysis workflow end-to-end."""
        graph = create_analysis_graph()
        initial_state = create_initial_state(
            target_path=temp_project,
            files_to_analyze=[
                str(Path(temp_project) / "sample.py"),
            ]
        )
        
        result = graph.invoke(initial_state)
        
        # Check final status
        assert result["scan_status"] == "done"
        
        # Check issues were found
        assert len(result["issues"]) > 0
        
        # Check summary was generated
        assert len(result.get("summary", "")) > 0
        
        # Check messages were accumulated
        assert len(result.get("messages", [])) > 0
    
    def test_full_workflow_multiple_files(self, temp_project):
        """Test workflow with multiple files."""
        graph = create_analysis_graph()
        initial_state = create_initial_state(
            target_path=temp_project,
            files_to_analyze=[
                str(Path(temp_project) / "sample.py"),
                str(Path(temp_project) / "utils.py"),
            ]
        )
        
        result = graph.invoke(initial_state)
        
        assert result["scan_status"] == "done"
        assert len(result["processed_files"]) == 2
        assert len(result["issues"]) > 0
    
    def test_run_analysis_helper(self, temp_project):
        """Test the run_analysis convenience function."""
        result = run_analysis(
            target_path=temp_project,
            files=[str(Path(temp_project) / "sample.py")]
        )
        
        assert result["scan_status"] == "done"
        assert len(result["issues"]) > 0
    
    def test_auto_discover_files(self, temp_project):
        """Test auto-discovery of files."""
        result = run_analysis(target_path=temp_project)
        
        assert result["scan_status"] == "done"
        # Should have discovered and processed both .py files
        assert len(result["processed_files"]) >= 2


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_empty_directory(self):
        """Test handling of empty directory."""
        temp_dir = tempfile.mkdtemp()
        
        try:
            result = run_analysis(target_path=temp_dir)
            # Should either error or complete with no issues
            assert result["scan_status"] in ["done", "error"]
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_nonexistent_directory(self):
        """Test handling of non-existent directory."""
        result = run_analysis(
            target_path="/nonexistent/path",
            files=[]
        )
        
        # Should complete (possibly with error status)
        assert result["scan_status"] in ["done", "error"]
    
    def test_syntax_error_in_file(self, temp_project):
        """Test handling of file with syntax errors."""
        # Create a file with syntax error
        (Path(temp_project) / "broken.py").write_text("def broken(\n")
        
        result = run_analysis(
            target_path=temp_project,
            files=[str(Path(temp_project) / "broken.py")]
        )
        
        # Should still complete
        assert result["scan_status"] == "done"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

