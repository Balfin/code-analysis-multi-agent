"""
Issue Model and IssueStore for the Code Analysis Multi-Agent System.

This module defines:
- RiskLevel: Enum for issue severity (critical, high, medium, low)
- IssueType: Enum for issue categories (security, performance, architecture)
- Issue: Pydantic model representing a detected code issue
- IssueStore: Class for persisting and retrieving issues
"""

import hashlib
import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List

from pydantic import BaseModel, Field, computed_field


class RiskLevel(str, Enum):
    """Risk level severity for detected issues."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IssueType(str, Enum):
    """Category of the detected issue."""
    SECURITY = "security"
    PERFORMANCE = "performance"
    ARCHITECTURE = "architecture"


class Issue(BaseModel):
    """
    Represents a detected code issue.
    
    The issue ID is automatically generated as a deterministic hash
    based on location, title, and code snippet to ensure uniqueness
    while allowing duplicate detection.
    """
    
    # Required fields
    location: str = Field(
        ...,
        description="File path and line number (e.g., 'auth.py:15')"
    )
    type: IssueType = Field(
        ...,
        description="Category of the issue"
    )
    risk_level: RiskLevel = Field(
        ...,
        description="Severity level of the issue"
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Short descriptive title of the issue"
    )
    description: str = Field(
        ...,
        min_length=1,
        description="Detailed description of the issue"
    )
    code_snippet: str = Field(
        ...,
        description="Relevant code snippet demonstrating the issue"
    )
    solution: str = Field(
        ...,
        min_length=1,
        description="Recommended solution or fix"
    )
    
    # Optional fields
    related_issues: Optional[List[str]] = Field(
        default=None,
        description="List of related issue IDs (for duplicated code or patterns)"
    )
    author: Optional[str] = Field(
        default=None,
        description="Agent or user that identified the issue"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when the issue was created"
    )
    
    @computed_field
    @property
    def id(self) -> str:
        """
        Generate a deterministic 12-character hash ID based on issue content.
        
        Uses SHA-256 hash of location + title + code_snippet to ensure:
        - Same issue always gets same ID (deterministic)
        - Different issues get different IDs (unique)
        - 12 chars provides ~68 billion unique combinations
        """
        content = f"{self.location}|{self.title}|{self.code_snippet}"
        hash_bytes = hashlib.sha256(content.encode('utf-8')).hexdigest()
        return hash_bytes[:12]
    
    def to_markdown(self) -> str:
        """
        Convert the issue to a formatted markdown report.
        
        Returns:
            Formatted markdown string with all issue details
        """
        risk_emoji = {
            RiskLevel.CRITICAL: "🔴",
            RiskLevel.HIGH: "🟠",
            RiskLevel.MEDIUM: "🟡",
            RiskLevel.LOW: "🟢",
        }
        
        type_emoji = {
            IssueType.SECURITY: "🔒",
            IssueType.PERFORMANCE: "⚡",
            IssueType.ARCHITECTURE: "🏗️",
        }
        
        md = f"""# {type_emoji.get(self.type, '📋')} {self.title}

## Overview

| Property | Value |
|----------|-------|
| **ID** | `{self.id}` |
| **Type** | {self.type.value.capitalize()} |
| **Risk Level** | {risk_emoji.get(self.risk_level, '⚪')} {self.risk_level.value.capitalize()} |
| **Location** | `{self.location}` |
| **Created** | {self.created_at.strftime('%Y-%m-%d %H:%M:%S')} |
{f'| **Author** | {self.author} |' if self.author else ''}

## Description

{self.description}

## Code Snippet

```python
{self.code_snippet}
```

## Recommended Solution

{self.solution}
"""
        
        if self.related_issues:
            md += f"""
## Related Issues

{chr(10).join(f'- `{issue_id}`' for issue_id in self.related_issues)}
"""
        
        return md
    
    def to_dict(self) -> dict:
        """Convert issue to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "location": self.location,
            "type": self.type.value,
            "risk_level": self.risk_level.value,
            "title": self.title,
            "description": self.description,
            "code_snippet": self.code_snippet,
            "solution": self.solution,
            "related_issues": self.related_issues,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
        }


class IssueStore:
    """
    Manages persistence of issues to the filesystem.
    
    Issues are stored in a hierarchical structure:
    - {base_dir}/{type}/{risk_level}/{issue_id}.md
    - Index file: {base_dir}/index.json (for quick lookups)
    
    Example structure:
        issues/
        ├── security/
        │   ├── critical/
        │   │   └── abc123.md
        │   └── high/
        │       └── def456.md
        ├── performance/
        │   └── medium/
        │       └── ghi789.md
        └── index.json
    
    The store automatically creates directories as needed.
    """
    
    def __init__(self, directory: str = "./issues"):
        """
        Initialize the IssueStore.
        
        Args:
            directory: Path to the base directory for storing issues
        """
        self.directory = Path(directory)
        self._ensure_directory()
    
    def _ensure_directory(self) -> None:
        """Create the base issues directory if it doesn't exist."""
        self.directory.mkdir(parents=True, exist_ok=True)
    
    def _get_issue_dir(self, issue_type: str, risk_level: str) -> Path:
        """Get the directory path for an issue based on type and risk level."""
        return self.directory / issue_type / risk_level
    
    def _get_issue_path(self, issue_id: str, issue_type: str, risk_level: str) -> Path:
        """Get the full path for an issue markdown file."""
        return self._get_issue_dir(issue_type, risk_level) / f"{issue_id}.md"
    
    def _find_issue_file(self, issue_id: str) -> Optional[Path]:
        """
        Find an issue file by ID, searching through all type/risk directories.
        
        Args:
            issue_id: The issue ID to find
            
        Returns:
            Path to the file if found, None otherwise
        """
        # First check index for type/risk_level info
        index = self._load_index()
        for entry in index:
            if entry.get('id') == issue_id:
                issue_type = entry.get('type')
                risk_level = entry.get('risk_level')
                if issue_type and risk_level:
                    path = self._get_issue_path(issue_id, issue_type, risk_level)
                    if path.exists():
                        return path
        
        # Fallback: search all directories
        for type_dir in self.directory.iterdir():
            if type_dir.is_dir() and type_dir.name != '.git':
                for risk_dir in type_dir.iterdir():
                    if risk_dir.is_dir():
                        md_path = risk_dir / f"{issue_id}.md"
                        if md_path.exists():
                            return md_path
        
        # Also check flat structure for backward compatibility
        flat_path = self.directory / f"{issue_id}.md"
        if flat_path.exists():
            return flat_path
        
        return None
    
    def _get_index_path(self) -> Path:
        """Get the path to the index file."""
        return self.directory / "index.json"
    
    def _load_index(self) -> List[dict]:
        """Load the index file, creating it if it doesn't exist."""
        index_path = self._get_index_path()
        if index_path.exists():
            try:
                with open(index_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []
    
    def _save_index(self, index: List[dict]) -> None:
        """Save the index file."""
        index_path = self._get_index_path()
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
    
    def save(self, issue: Issue) -> Path:
        """
        Save an issue to the filesystem in hierarchical structure.
        
        Creates directories as needed: {base}/{type}/{risk_level}/
        Creates both a markdown file and updates the index.
        If an issue with the same ID already exists, it will be overwritten.
        
        Args:
            issue: The Issue to save
            
        Returns:
            Path to the saved markdown file
        """
        # Get issue type and risk level values
        issue_type = issue.type.value if isinstance(issue.type, IssueType) else issue.type
        risk_level = issue.risk_level.value if isinstance(issue.risk_level, RiskLevel) else issue.risk_level
        
        # Create directory structure: issues/{type}/{risk_level}/
        issue_dir = self._get_issue_dir(issue_type, risk_level)
        issue_dir.mkdir(parents=True, exist_ok=True)
        
        # Save markdown file
        md_path = issue_dir / f"{issue.id}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(issue.to_markdown())
        
        # Update index
        index = self._load_index()
        
        # Remove existing entry with same ID if present (might be in different location)
        old_entry = None
        for entry in index:
            if entry.get('id') == issue.id:
                old_entry = entry
                break
        
        if old_entry:
            # Delete old file if it exists in a different location
            old_type = old_entry.get('type')
            old_risk = old_entry.get('risk_level')
            if old_type != issue_type or old_risk != risk_level:
                old_path = self._get_issue_path(issue.id, old_type, old_risk)
                if old_path.exists():
                    old_path.unlink()
            
            index = [entry for entry in index if entry.get('id') != issue.id]
        
        # Add new entry
        index.append(issue.to_dict())
        
        self._save_index(index)
        
        return md_path
    
    def get_all(self) -> List[dict]:
        """
        Get all issues from the index.
        
        Returns:
            List of issue dictionaries
        """
        return self._load_index()
    
    def get_by_id(self, issue_id: str) -> Optional[dict]:
        """
        Get a specific issue by ID.
        
        Args:
            issue_id: The 12-character issue ID
            
        Returns:
            Issue dictionary if found, None otherwise
        """
        index = self._load_index()
        for entry in index:
            if entry.get('id') == issue_id:
                return entry
        return None
    
    def get_by_type(self, issue_type: IssueType) -> List[dict]:
        """
        Get all issues of a specific type.
        
        Args:
            issue_type: The IssueType to filter by
            
        Returns:
            List of matching issue dictionaries
        """
        index = self._load_index()
        return [
            entry for entry in index 
            if entry.get('type') == issue_type.value
        ]
    
    def get_by_risk_level(self, risk_level: RiskLevel) -> List[dict]:
        """
        Get all issues of a specific risk level.
        
        Args:
            risk_level: The RiskLevel to filter by
            
        Returns:
            List of matching issue dictionaries
        """
        index = self._load_index()
        return [
            entry for entry in index 
            if entry.get('risk_level') == risk_level.value
        ]
    
    def get_markdown(self, issue_id: str) -> Optional[str]:
        """
        Get the markdown content for a specific issue.
        
        Args:
            issue_id: The 12-character issue ID
            
        Returns:
            Markdown content if found, None otherwise
        """
        md_path = self._find_issue_file(issue_id)
        if md_path and md_path.exists():
            with open(md_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None
    
    def delete(self, issue_id: str) -> bool:
        """
        Delete an issue by ID.
        
        Args:
            issue_id: The 12-character issue ID
            
        Returns:
            True if deleted, False if not found
        """
        # Find and remove from index
        index = self._load_index()
        issue_entry = None
        for entry in index:
            if entry.get('id') == issue_id:
                issue_entry = entry
                break
        
        if not issue_entry:
            return False
        
        # Remove from index
        index = [entry for entry in index if entry.get('id') != issue_id]
        self._save_index(index)
        
        # Remove markdown file from hierarchical location
        issue_type = issue_entry.get('type')
        risk_level = issue_entry.get('risk_level')
        if issue_type and risk_level:
            md_path = self._get_issue_path(issue_id, issue_type, risk_level)
            if md_path.exists():
                md_path.unlink()
                
                # Clean up empty directories
                parent_dir = md_path.parent
                if parent_dir.exists() and not any(parent_dir.iterdir()):
                    parent_dir.rmdir()
                    # Also try to remove type directory if empty
                    type_dir = parent_dir.parent
                    if type_dir.exists() and type_dir != self.directory and not any(type_dir.iterdir()):
                        type_dir.rmdir()
        
        # Also check flat structure for backward compatibility
        flat_path = self.directory / f"{issue_id}.md"
        if flat_path.exists():
            flat_path.unlink()
        
        return True
    
    def clear(self) -> int:
        """
        Delete all issues and clean up directory structure.
        
        Returns:
            Number of issues deleted
        """
        index = self._load_index()
        count = len(index)
        
        # Delete all markdown files from hierarchical structure
        for entry in index:
            issue_id = entry.get('id')
            issue_type = entry.get('type')
            risk_level = entry.get('risk_level')
            
            # Try hierarchical path first
            if issue_type and risk_level:
                md_path = self._get_issue_path(issue_id, issue_type, risk_level)
                if md_path.exists():
                    md_path.unlink()
            
            # Also check flat structure for backward compatibility
            flat_path = self.directory / f"{issue_id}.md"
            if flat_path.exists():
                flat_path.unlink()
        
        # Clean up empty directories
        for type_dir in list(self.directory.iterdir()):
            if type_dir.is_dir() and type_dir.name not in ('.git', '__pycache__'):
                for risk_dir in list(type_dir.iterdir()):
                    if risk_dir.is_dir() and not any(risk_dir.iterdir()):
                        risk_dir.rmdir()
                # Remove type dir if empty
                if not any(type_dir.iterdir()):
                    type_dir.rmdir()
        
        # Clear the index
        self._save_index([])
        
        return count
    
    def count(self) -> int:
        """Get the total number of issues."""
        return len(self._load_index())
    
    def summary(self) -> dict:
        """
        Get a summary of issues by type and risk level.
        
        Returns:
            Dictionary with counts by category
        """
        index = self._load_index()
        
        by_type = {t.value: 0 for t in IssueType}
        by_risk = {r.value: 0 for r in RiskLevel}
        
        for entry in index:
            issue_type = entry.get('type')
            risk_level = entry.get('risk_level')
            
            if issue_type in by_type:
                by_type[issue_type] += 1
            if risk_level in by_risk:
                by_risk[risk_level] += 1
        
        return {
            "total": len(index),
            "by_type": by_type,
            "by_risk_level": by_risk,
        }

