"""
Unit tests for Issue model and IssueStore.

Run with: python -m pytest models/test_issue.py -v
"""

import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from models.issue import Issue, IssueStore, IssueType, RiskLevel


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def sample_issue_data():
    """Sample issue data for testing."""
    return {
        "location": "auth.py:15",
        "type": IssueType.SECURITY,
        "risk_level": RiskLevel.HIGH,
        "title": "SQL Injection Vulnerability",
        "description": "User input is directly interpolated into SQL query without sanitization.",
        "code_snippet": 'query = f"SELECT * FROM users WHERE name = \'{user_input}\'"',
        "solution": "Use parameterized queries with placeholders instead of string interpolation.",
    }


@pytest.fixture
def sample_issue(sample_issue_data):
    """Create a sample Issue instance."""
    return Issue(**sample_issue_data)


@pytest.fixture
def temp_issue_store():
    """Create a temporary IssueStore for testing."""
    temp_dir = tempfile.mkdtemp()
    store = IssueStore(temp_dir)
    yield store
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_issues():
    """Create multiple sample issues for testing."""
    return [
        Issue(
            location="auth.py:15",
            type=IssueType.SECURITY,
            risk_level=RiskLevel.CRITICAL,
            title="SQL Injection",
            description="SQL injection vulnerability in auth module",
            code_snippet='query = f"SELECT * FROM users WHERE id={user_id}"',
            solution="Use parameterized queries",
        ),
        Issue(
            location="api.py:42",
            type=IssueType.PERFORMANCE,
            risk_level=RiskLevel.HIGH,
            title="N+1 Query Pattern",
            description="Loop performs individual database queries",
            code_snippet="for user in users:\n    posts = db.query(f'SELECT * FROM posts WHERE user_id={user.id}')",
            solution="Use eager loading or batch queries",
        ),
        Issue(
            location="utils.py:100",
            type=IssueType.ARCHITECTURE,
            risk_level=RiskLevel.MEDIUM,
            title="Missing Error Handling",
            description="Function does not handle file operation exceptions",
            code_snippet="def read_config():\n    return open('config.json').read()",
            solution="Add try/except block and proper error handling",
        ),
    ]


# =============================================================================
# Issue Model Tests
# =============================================================================

class TestIssueModel:
    """Tests for the Issue Pydantic model."""
    
    def test_create_valid_issue(self, sample_issue_data):
        """Test creating an issue with valid data."""
        issue = Issue(**sample_issue_data)
        
        assert issue.location == "auth.py:15"
        assert issue.type == IssueType.SECURITY
        assert issue.risk_level == RiskLevel.HIGH
        assert issue.title == "SQL Injection Vulnerability"
        assert issue.description is not None
        assert issue.code_snippet is not None
        assert issue.solution is not None
    
    def test_issue_id_generation(self, sample_issue):
        """Test that issue ID is generated correctly."""
        assert sample_issue.id is not None
        assert len(sample_issue.id) == 12
        assert sample_issue.id.isalnum()
    
    def test_issue_id_deterministic(self, sample_issue_data):
        """Test that same content produces same ID."""
        issue1 = Issue(**sample_issue_data)
        issue2 = Issue(**sample_issue_data)
        
        assert issue1.id == issue2.id
    
    def test_issue_id_unique_for_different_content(self, sample_issue_data):
        """Test that different content produces different IDs."""
        issue1 = Issue(**sample_issue_data)
        
        modified_data = sample_issue_data.copy()
        modified_data["title"] = "Different Title"
        issue2 = Issue(**modified_data)
        
        assert issue1.id != issue2.id
    
    def test_issue_validation_missing_required_field(self):
        """Test that missing required fields raise validation error."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            Issue(
                location="test.py:1",
                type=IssueType.SECURITY,
                risk_level=RiskLevel.HIGH,
                title="Test",
                # Missing: description, code_snippet, solution
            )
    
    def test_issue_validation_empty_title(self, sample_issue_data):
        """Test that empty title raises validation error."""
        sample_issue_data["title"] = ""
        with pytest.raises(Exception):
            Issue(**sample_issue_data)
    
    def test_issue_optional_fields(self, sample_issue_data):
        """Test that optional fields work correctly."""
        sample_issue_data["related_issues"] = ["abc123def456"]
        sample_issue_data["author"] = "SecurityAgent"
        
        issue = Issue(**sample_issue_data)
        
        assert issue.related_issues == ["abc123def456"]
        assert issue.author == "SecurityAgent"
    
    def test_issue_created_at_default(self, sample_issue):
        """Test that created_at is set by default."""
        assert sample_issue.created_at is not None
        assert isinstance(sample_issue.created_at, datetime)
    
    def test_issue_to_markdown(self, sample_issue):
        """Test markdown generation."""
        markdown = sample_issue.to_markdown()
        
        assert "# " in markdown  # Has title
        assert sample_issue.title in markdown
        assert sample_issue.id in markdown
        assert "Security" in markdown
        assert "High" in markdown
        assert sample_issue.location in markdown
        assert sample_issue.description in markdown
        assert sample_issue.code_snippet in markdown
        assert sample_issue.solution in markdown
        assert "```python" in markdown  # Code block
    
    def test_issue_to_dict(self, sample_issue):
        """Test dictionary conversion."""
        data = sample_issue.to_dict()
        
        assert isinstance(data, dict)
        assert data["id"] == sample_issue.id
        assert data["location"] == sample_issue.location
        assert data["type"] == "security"
        assert data["risk_level"] == "high"
        assert data["title"] == sample_issue.title
        assert "created_at" in data
    
    def test_all_risk_levels(self, sample_issue_data):
        """Test all risk level enum values."""
        for risk_level in RiskLevel:
            sample_issue_data["risk_level"] = risk_level
            issue = Issue(**sample_issue_data)
            assert issue.risk_level == risk_level
    
    def test_all_issue_types(self, sample_issue_data):
        """Test all issue type enum values."""
        for issue_type in IssueType:
            sample_issue_data["type"] = issue_type
            issue = Issue(**sample_issue_data)
            assert issue.type == issue_type


# =============================================================================
# IssueStore Tests
# =============================================================================

class TestIssueStore:
    """Tests for the IssueStore class."""
    
    def test_store_creates_directory(self):
        """Test that IssueStore creates directory if it doesn't exist."""
        temp_dir = tempfile.mkdtemp()
        store_path = Path(temp_dir) / "new_issues"
        
        try:
            store = IssueStore(str(store_path))
            assert store_path.exists()
            assert store_path.is_dir()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_save_issue(self, temp_issue_store, sample_issue):
        """Test saving an issue."""
        path = temp_issue_store.save(sample_issue)
        
        assert path.exists()
        assert path.suffix == ".md"
        assert sample_issue.id in path.name
    
    def test_save_creates_index(self, temp_issue_store, sample_issue):
        """Test that saving creates/updates index.json."""
        temp_issue_store.save(sample_issue)
        
        index_path = temp_issue_store.directory / "index.json"
        assert index_path.exists()
        
        with open(index_path) as f:
            index = json.load(f)
        
        assert len(index) == 1
        assert index[0]["id"] == sample_issue.id
    
    def test_save_multiple_issues(self, temp_issue_store, sample_issues):
        """Test saving multiple issues."""
        for issue in sample_issues:
            temp_issue_store.save(issue)
        
        assert temp_issue_store.count() == 3
    
    def test_save_overwrites_duplicate(self, temp_issue_store, sample_issue):
        """Test that saving same issue overwrites existing."""
        temp_issue_store.save(sample_issue)
        temp_issue_store.save(sample_issue)
        
        assert temp_issue_store.count() == 1
    
    def test_get_all(self, temp_issue_store, sample_issues):
        """Test retrieving all issues."""
        for issue in sample_issues:
            temp_issue_store.save(issue)
        
        all_issues = temp_issue_store.get_all()
        
        assert len(all_issues) == 3
        assert all(isinstance(i, dict) for i in all_issues)
    
    def test_get_by_id(self, temp_issue_store, sample_issue):
        """Test retrieving issue by ID."""
        temp_issue_store.save(sample_issue)
        
        retrieved = temp_issue_store.get_by_id(sample_issue.id)
        
        assert retrieved is not None
        assert retrieved["id"] == sample_issue.id
        assert retrieved["title"] == sample_issue.title
    
    def test_get_by_id_not_found(self, temp_issue_store):
        """Test retrieving non-existent issue."""
        result = temp_issue_store.get_by_id("nonexistent")
        assert result is None
    
    def test_get_by_type(self, temp_issue_store, sample_issues):
        """Test filtering issues by type."""
        for issue in sample_issues:
            temp_issue_store.save(issue)
        
        security_issues = temp_issue_store.get_by_type(IssueType.SECURITY)
        
        assert len(security_issues) == 1
        assert security_issues[0]["type"] == "security"
    
    def test_get_by_risk_level(self, temp_issue_store, sample_issues):
        """Test filtering issues by risk level."""
        for issue in sample_issues:
            temp_issue_store.save(issue)
        
        critical_issues = temp_issue_store.get_by_risk_level(RiskLevel.CRITICAL)
        
        assert len(critical_issues) == 1
        assert critical_issues[0]["risk_level"] == "critical"
    
    def test_get_markdown(self, temp_issue_store, sample_issue):
        """Test retrieving markdown content."""
        temp_issue_store.save(sample_issue)
        
        markdown = temp_issue_store.get_markdown(sample_issue.id)
        
        assert markdown is not None
        assert sample_issue.title in markdown
    
    def test_get_markdown_not_found(self, temp_issue_store):
        """Test retrieving non-existent markdown."""
        result = temp_issue_store.get_markdown("nonexistent")
        assert result is None
    
    def test_delete_issue(self, temp_issue_store, sample_issue):
        """Test deleting an issue."""
        temp_issue_store.save(sample_issue)
        assert temp_issue_store.count() == 1
        
        result = temp_issue_store.delete(sample_issue.id)
        
        assert result is True
        assert temp_issue_store.count() == 0
        assert temp_issue_store.get_by_id(sample_issue.id) is None
    
    def test_delete_not_found(self, temp_issue_store):
        """Test deleting non-existent issue."""
        result = temp_issue_store.delete("nonexistent")
        assert result is False
    
    def test_clear_all(self, temp_issue_store, sample_issues):
        """Test clearing all issues."""
        for issue in sample_issues:
            temp_issue_store.save(issue)
        
        count = temp_issue_store.clear()
        
        assert count == 3
        assert temp_issue_store.count() == 0
    
    def test_summary(self, temp_issue_store, sample_issues):
        """Test getting summary statistics."""
        for issue in sample_issues:
            temp_issue_store.save(issue)
        
        summary = temp_issue_store.summary()
        
        assert summary["total"] == 3
        assert summary["by_type"]["security"] == 1
        assert summary["by_type"]["performance"] == 1
        assert summary["by_type"]["architecture"] == 1
        assert summary["by_risk_level"]["critical"] == 1
        assert summary["by_risk_level"]["high"] == 1
        assert summary["by_risk_level"]["medium"] == 1
    
    def test_hierarchical_structure(self, temp_issue_store, sample_issues):
        """Test that issues are saved in hierarchical directory structure."""
        for issue in sample_issues:
            temp_issue_store.save(issue)
        
        # Check security/critical directory exists
        security_critical_dir = temp_issue_store.directory / "security" / "critical"
        assert security_critical_dir.exists()
        assert security_critical_dir.is_dir()
        
        # Check performance/high directory exists
        performance_high_dir = temp_issue_store.directory / "performance" / "high"
        assert performance_high_dir.exists()
        
        # Check architecture/medium directory exists
        architecture_medium_dir = temp_issue_store.directory / "architecture" / "medium"
        assert architecture_medium_dir.exists()
        
        # Check that markdown files exist in correct locations
        security_files = list(security_critical_dir.glob("*.md"))
        assert len(security_files) == 1
        
        performance_files = list(performance_high_dir.glob("*.md"))
        assert len(performance_files) == 1


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for Issue and IssueStore working together."""
    
    def test_full_workflow(self, temp_issue_store):
        """Test complete workflow: create, save, retrieve, update, delete."""
        # Create issue
        issue = Issue(
            location="app.py:50",
            type=IssueType.SECURITY,
            risk_level=RiskLevel.CRITICAL,
            title="Hardcoded Secret",
            description="API key is hardcoded in source code",
            code_snippet='API_KEY = "sk-secret-123456"',
            solution="Use environment variables for secrets",
        )
        
        # Save
        path = temp_issue_store.save(issue)
        assert path.exists()
        
        # Retrieve
        retrieved = temp_issue_store.get_by_id(issue.id)
        assert retrieved["title"] == issue.title
        
        # Get markdown
        markdown = temp_issue_store.get_markdown(issue.id)
        assert "Hardcoded Secret" in markdown
        
        # Get summary
        summary = temp_issue_store.summary()
        assert summary["total"] == 1
        
        # Delete
        deleted = temp_issue_store.delete(issue.id)
        assert deleted is True
        assert temp_issue_store.count() == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

