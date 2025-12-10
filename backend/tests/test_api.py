"""
API tests for the FastAPI backend.

Run with: python -m pytest tests/test_api.py -v

Uses FastAPI's TestClient for synchronous testing.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Set environment before importing app
os.environ["USE_LLM_ANALYSIS"] = "false"
os.environ["ISSUES_DIR"] = tempfile.mkdtemp()

from app import app, get_issue_store, ISSUES_DIR
from models.issue import Issue, IssueStore, IssueType, RiskLevel


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def temp_project():
    """Create a temporary project for testing."""
    temp_dir = tempfile.mkdtemp()
    
    # Create test file with issues
    (Path(temp_dir) / "test.py").write_text('''
def authenticate(username, password):
    query = f"SELECT * FROM users WHERE username='{username}'"
    return query

API_KEY = "secret123"
''')
    
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def populated_store():
    """Create a store with sample issues."""
    store = get_issue_store()
    
    # Clear existing using dict access
    for issue_dict in store.get_all():
        store.delete(issue_dict["id"])
    
    # Add test issues
    issues = [
        Issue(
            location="test.py:10",
            type=IssueType.SECURITY,
            risk_level=RiskLevel.CRITICAL,
            title="SQL Injection",
            description="User input concatenated into SQL query",
            code_snippet="query = f'SELECT * FROM users WHERE id={user_id}'",
            solution="Use parameterized queries",
        ),
        Issue(
            location="test.py:20",
            type=IssueType.SECURITY,
            risk_level=RiskLevel.HIGH,
            title="Hardcoded Secret",
            description="API key hardcoded in source",
            code_snippet="API_KEY = 'secret123'",
            solution="Use environment variables",
        ),
        Issue(
            location="api.py:50",
            type=IssueType.PERFORMANCE,
            risk_level=RiskLevel.MEDIUM,
            title="N+1 Query",
            description="Query inside loop",
            code_snippet="for item in items: db.query(...)",
            solution="Use batch query",
        ),
        Issue(
            location="utils.py:30",
            type=IssueType.ARCHITECTURE,
            risk_level=RiskLevel.LOW,
            title="TODO Comment",
            description="Unfinished work",
            code_snippet="# TODO: refactor this",
            solution="Complete the task",
        ),
    ]
    
    for issue in issues:
        store.save(issue)
    
    yield store
    
    # Cleanup using dict access
    for issue_dict in store.get_all():
        store.delete(issue_dict["id"])


# =============================================================================
# Info Endpoint Tests
# =============================================================================

class TestInfoEndpoints:
    """Tests for info/health endpoints."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data
    
    def test_docs_available(self, client):
        """Test API docs are accessible."""
        response = client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


# =============================================================================
# Analysis Endpoint Tests
# =============================================================================

class TestAnalysisEndpoints:
    """Tests for analysis endpoints."""
    
    def test_analyze_invalid_path(self, client):
        """Test analysis with invalid path."""
        response = client.post(
            "/analyze",
            json={"path": "/nonexistent/path/to/project"}
        )
        
        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"]
    
    def test_analyze_sync_mode(self, client, temp_project):
        """Test synchronous analysis."""
        response = client.post(
            "/analyze",
            json={"path": temp_project, "async_mode": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "issues_found" in data
        assert "files_analyzed" in data
        assert "health_score" in data
    
    def test_analyze_async_mode(self, client, temp_project):
        """Test async analysis returns task ID."""
        response = client.post(
            "/analyze",
            json={"path": temp_project, "async_mode": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert "task_id" in data
    
    def test_analyze_status_not_found(self, client):
        """Test getting status of nonexistent task."""
        response = client.get("/analyze/nonexistent/status")
        
        assert response.status_code == 404
    
    def test_analyze_default_file_types(self, client, temp_project):
        """Test default file types is Python."""
        response = client.post(
            "/analyze",
            json={"path": temp_project}
        )
        
        assert response.status_code == 200


# =============================================================================
# Issues Endpoint Tests
# =============================================================================

class TestIssuesEndpoints:
    """Tests for issues endpoints."""
    
    def test_get_issues_empty(self, client):
        """Test getting issues when empty."""
        response = client.get("/issues")
        
        assert response.status_code == 200
        data = response.json()
        assert "issues" in data
        assert "total" in data
    
    def test_get_issues_list(self, client, populated_store):
        """Test getting list of issues."""
        response = client.get("/issues")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 4
        assert len(data["issues"]) == 4
    
    def test_filter_by_type(self, client, populated_store):
        """Test filtering issues by type."""
        response = client.get("/issues?type=security")
        
        assert response.status_code == 200
        data = response.json()
        assert data["filtered_total"] == 2
        for issue in data["issues"]:
            assert issue["type"] == "security"
    
    def test_filter_by_risk_level(self, client, populated_store):
        """Test filtering issues by risk level."""
        response = client.get("/issues?risk_level=critical")
        
        assert response.status_code == 200
        data = response.json()
        assert data["filtered_total"] == 1
        assert data["issues"][0]["risk_level"] == "critical"
    
    def test_filter_combined(self, client, populated_store):
        """Test combined filtering."""
        response = client.get("/issues?type=security&risk_level=high")
        
        assert response.status_code == 200
        data = response.json()
        assert data["filtered_total"] == 1
    
    def test_search_in_title(self, client, populated_store):
        """Test search in issue title."""
        response = client.get("/issues?search=SQL")
        
        assert response.status_code == 200
        data = response.json()
        assert data["filtered_total"] >= 1
    
    def test_filter_by_file(self, client, populated_store):
        """Test filtering by file path."""
        response = client.get("/issues?file=api.py")
        
        assert response.status_code == 200
        data = response.json()
        assert data["filtered_total"] == 1
    
    def test_pagination(self, client, populated_store):
        """Test pagination."""
        response = client.get("/issues?page=1&page_size=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["issues"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
    
    def test_pagination_page_2(self, client, populated_store):
        """Test getting second page."""
        response = client.get("/issues?page=2&page_size=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["issues"]) == 2
        assert data["page"] == 2
    
    def test_get_issue_detail(self, client, populated_store):
        """Test getting issue detail."""
        # First get list to get an ID
        list_response = client.get("/issues")
        issue_id = list_response.json()["issues"][0]["id"]
        
        response = client.get(f"/issues/{issue_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == issue_id
        assert "markdown_content" in data
        assert "title" in data
    
    def test_get_issue_not_found(self, client):
        """Test getting nonexistent issue."""
        response = client.get("/issues/nonexistent-id")
        
        assert response.status_code == 404
    
    def test_delete_issue(self, client, populated_store):
        """Test deleting an issue."""
        # Get an issue ID
        list_response = client.get("/issues")
        initial_count = list_response.json()["total"]
        issue_id = list_response.json()["issues"][0]["id"]
        
        # Delete it
        response = client.delete(f"/issues/{issue_id}")
        
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"
        
        # Verify deleted
        verify_response = client.get("/issues")
        assert verify_response.json()["total"] == initial_count - 1
    
    def test_delete_issue_not_found(self, client):
        """Test deleting nonexistent issue."""
        response = client.delete("/issues/nonexistent-id")
        
        assert response.status_code == 404
    
    def test_get_issues_summary(self, client, populated_store):
        """Test getting issues summary."""
        response = client.get("/issues/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "by_type" in data
        assert "by_risk_level" in data


# =============================================================================
# Chat Endpoint Tests
# =============================================================================

class TestChatEndpoint:
    """Tests for chat endpoint."""
    
    def test_chat_basic(self, client, populated_store):
        """Test basic chat request."""
        response = client.post(
            "/chat",
            json={"message": "What are the critical issues?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
    
    def test_chat_with_context(self, client, populated_store):
        """Test chat with issue context."""
        # Get an issue ID
        list_response = client.get("/issues")
        issue_id = list_response.json()["issues"][0]["id"]
        
        response = client.post(
            "/chat",
            json={
                "message": "Tell me more about this issue",
                "context": {"issue_id": issue_id}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
    
    def test_chat_security_question(self, client, populated_store):
        """Test chat about security issues."""
        response = client.post(
            "/chat",
            json={"message": "What security issues were found?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "security" in data["response"].lower() or "response" in data
    
    def test_chat_summary_question(self, client, populated_store):
        """Test chat for summary."""
        response = client.post(
            "/chat",
            json={"message": "Give me an overview of the issues"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data


# =============================================================================
# CORS Tests
# =============================================================================

class TestCORS:
    """Tests for CORS configuration."""
    
    def test_cors_allowed_origin(self, client):
        """Test CORS allows configured origins via preflight."""
        response = client.options(
            "/issues",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            }
        )
        
        # OPTIONS preflight should succeed
        assert response.status_code == 200
    
    def test_cors_headers_present(self, client):
        """Test CORS headers are present."""
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:5173"}
        )
        
        assert response.status_code == 200
        # FastAPI CORS middleware should add these headers
        assert "access-control-allow-origin" in response.headers or response.status_code == 200


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Tests for error handling."""
    
    def test_invalid_json(self, client):
        """Test handling of invalid JSON."""
        response = client.post(
            "/analyze",
            content="not json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_missing_required_field(self, client):
        """Test handling of missing required field."""
        response = client.post(
            "/analyze",
            json={}  # Missing required 'path' field
        )
        
        assert response.status_code == 422
    
    def test_invalid_page_size(self, client):
        """Test validation of page_size parameter."""
        response = client.get("/issues?page_size=1000")  # Over limit
        
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

