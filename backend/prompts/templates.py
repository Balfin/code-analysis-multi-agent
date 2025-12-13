"""
Prompt Templates for Specialist Agents.

This module contains carefully crafted prompts for each specialist agent:
- Security Expert: Finds vulnerabilities and security risks
- Performance Analyst: Identifies performance bottlenecks
- Architecture Specialist: Detects design and code quality issues

Each prompt is designed to:
1. Establish the agent's expert role
2. Provide clear analysis criteria
3. Request structured JSON output
4. Include examples for better responses

Prompts are loaded from prompts_config.yaml for centralized configuration.
"""

import os
import yaml
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any, Optional

from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate


# =============================================================================
# Configuration Loading
# =============================================================================

def _get_config_path() -> Path:
    """Get the path to the prompts configuration file."""
    # Get the directory where this file is located (backend/prompts/)
    current_dir = Path(__file__).parent
    # Look in parent directory (backend/) for prompts_config.yaml
    config_path = current_dir.parent / "prompts_config.yaml"
    
    if not config_path.exists():
        # Fallback: try in current directory
        config_path = current_dir / "prompts_config.yaml"
    
    return config_path


@lru_cache(maxsize=1)
def _load_prompts_config() -> Dict[str, Any]:
    """Load prompts configuration from YAML file. Cached for performance."""
    config_path = _get_config_path()
    
    if not config_path.exists():
        raise FileNotFoundError(
            f"Prompts configuration file not found at {config_path}. "
            "Please ensure prompts_config.yaml exists in the backend directory."
        )
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    if not config or 'roles' not in config:
        raise ValueError("Invalid prompts configuration: 'roles' key not found")
    
    return config


def _get_role_config(role_type: str) -> Dict[str, Any]:
    """Get configuration for a specific role type."""
    config = _load_prompts_config()
    
    for role in config.get('roles', []):
        if role.get('type') == role_type:
            return role
    
    raise ValueError(f"Role type '{role_type}' not found in configuration")


# =============================================================================
# Prompt String Accessors (for backward compatibility)
# =============================================================================

def _get_prompt_string(role_type: str, prompt_type: str) -> str:
    """Get a prompt string from configuration."""
    role_config = _get_role_config(role_type)
    
    if prompt_type == 'system':
        return role_config.get('system_prompt', '')
    elif prompt_type == 'human':
        return role_config.get('human_prompt_template', '')
    else:
        raise ValueError(f"Invalid prompt type: {prompt_type}")


# Exported constants for backward compatibility
def _get_security_system_prompt() -> str:
    """Get security system prompt from config."""
    return _get_prompt_string('security', 'system')


def _get_security_human_prompt() -> str:
    """Get security human prompt from config."""
    return _get_prompt_string('security', 'human')


def _get_performance_system_prompt() -> str:
    """Get performance system prompt from config."""
    return _get_prompt_string('performance', 'system')


def _get_performance_human_prompt() -> str:
    """Get performance human prompt from config."""
    return _get_prompt_string('performance', 'human')


def _get_architecture_system_prompt() -> str:
    """Get architecture system prompt from config."""
    return _get_prompt_string('architecture', 'system')


def _get_architecture_human_prompt() -> str:
    """Get architecture human prompt from config."""
    return _get_prompt_string('architecture', 'human')


# Backward compatibility: Export as module-level constants (lazy-loaded)
# These are accessed via __getattr__ to load from config on first access

def __getattr__(name: str) -> str:
    """Dynamic attribute access for prompt constants (lazy loading from config)."""
    prompt_map = {
        'SECURITY_SYSTEM_PROMPT': _get_security_system_prompt,
        'SECURITY_HUMAN_PROMPT': _get_security_human_prompt,
        'PERFORMANCE_SYSTEM_PROMPT': _get_performance_system_prompt,
        'PERFORMANCE_HUMAN_PROMPT': _get_performance_human_prompt,
        'ARCHITECTURE_SYSTEM_PROMPT': _get_architecture_system_prompt,
        'ARCHITECTURE_HUMAN_PROMPT': _get_architecture_human_prompt,
    }
    
    if name in prompt_map:
        return prompt_map[name]()
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# =============================================================================
# Prompt Template Builders
# =============================================================================

def get_security_prompt() -> ChatPromptTemplate:
    """Get the security analysis prompt template."""
    system_prompt = _get_security_system_prompt()
    human_prompt = _get_security_human_prompt()
    return ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_prompt),
        HumanMessagePromptTemplate.from_template(human_prompt),
    ])


def get_performance_prompt() -> ChatPromptTemplate:
    """Get the performance analysis prompt template."""
    system_prompt = _get_performance_system_prompt()
    human_prompt = _get_performance_human_prompt()
    return ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_prompt),
        HumanMessagePromptTemplate.from_template(human_prompt),
    ])


def get_architecture_prompt() -> ChatPromptTemplate:
    """Get the architecture analysis prompt template."""
    system_prompt = _get_architecture_system_prompt()
    human_prompt = _get_architecture_human_prompt()
    return ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_prompt),
        HumanMessagePromptTemplate.from_template(human_prompt),
    ])


# =============================================================================
# Configuration Access Functions
# =============================================================================

def get_prompts_config() -> Dict[str, Any]:
    """Get the full prompts configuration."""
    return _load_prompts_config()


def get_all_roles() -> list[Dict[str, Any]]:
    """Get all role configurations."""
    config = _load_prompts_config()
    return config.get('roles', [])


# =============================================================================
# Issue Parsing
# =============================================================================

def parse_llm_issues(response: str, file_path: str, issue_type: str) -> list:
    """
    Parse LLM response into structured issues.
    
    Handles malformed JSON from LLM responses, including:
    - Smart quotes (curly quotes)
    - Unescaped quotes in string values
    - Trailing commas
    
    Args:
        response: Raw LLM response text
        file_path: Path to the analyzed file
        issue_type: Type of issue (security, performance, architecture)
        
    Returns:
        List of issue dictionaries
    """
    import json
    import re
    
    if not response or not response.strip():
        return []
    
    # Replace smart quotes with regular quotes
    cleaned_response = response
    cleaned_response = cleaned_response.replace('"', '"').replace('"', '"')
    cleaned_response = cleaned_response.replace(''', "'").replace(''', "'")
    
    # Try to extract JSON from the response
    json_match = re.search(r'\[[\s\S]*\]', cleaned_response)
    if not json_match:
        json_match = re.search(r'\{[\s\S]*\}', cleaned_response)
    
    if not json_match:
        return []
    
    json_str = json_match.group()
    
    # Try standard JSON parsing first
    try:
        issues_data = json.loads(json_str)
        if isinstance(issues_data, dict):
            issues_data = [issues_data]
        if isinstance(issues_data, list):
            return _convert_to_issue_format(issues_data, file_path, issue_type)
    except json.JSONDecodeError:
        pass
    
    # Try with common fixes
    try:
        cleaned = json_str
        cleaned = re.sub(r',\s*]', ']', cleaned)  # Remove trailing commas
        cleaned = re.sub(r',\s*}', '}', cleaned)
        cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', cleaned)
        
        issues_data = json.loads(cleaned)
        if isinstance(issues_data, dict):
            issues_data = [issues_data]
        if isinstance(issues_data, list):
            return _convert_to_issue_format(issues_data, file_path, issue_type)
    except json.JSONDecodeError:
        pass
    
    # Fall back to regex-based extraction for malformed JSON
    issues_data = _extract_issues_with_regex(cleaned_response)
    return _convert_to_issue_format(issues_data, file_path, issue_type)


def _extract_issues_with_regex(response: str) -> list:
    """Extract issues using regex when JSON parsing fails."""
    import re
    
    issues = []
    
    # Split into potential objects by looking for title field starts
    parts = re.split(r'(?=\{\s*"title")', response)
    
    for part in parts:
        if '"title"' not in part:
            continue
            
        issue = {}
        
        # Extract each field with patterns
        field_patterns = {
            'title': r'"title"\s*:\s*"([^"]+)"',
            'risk_level': r'"risk_level"\s*:\s*"([^"]+)"',
            'line_number': r'"line_number"\s*:\s*(\d+)',
            'description': r'"description"\s*:\s*"((?:[^"\\]|\\.)*)"',
            'solution': r'"solution"\s*:\s*"((?:[^"\\]|\\.)*)"',
        }
        
        for field, pattern in field_patterns.items():
            match = re.search(pattern, part)
            if match:
                value = match.group(1)
                if field == 'line_number':
                    value = int(value)
                issue[field] = value
        
        # For code_snippet, use a more permissive pattern
        snippet_match = re.search(r'"code_snippet"\s*:\s*"(.+?)"\s*[,}]', part, re.DOTALL)
        if snippet_match:
            issue['code_snippet'] = snippet_match.group(1)
        
        if issue.get('title'):
            issues.append(issue)
    
    return issues


def _convert_to_issue_format(issues_data: list, file_path: str, issue_type: str) -> list:
    """Convert raw parsed data to our issue format."""
    issues = []
    
    for item in issues_data:
        if not isinstance(item, dict):
            continue
        
        # Get line number, defaulting to 1
        line_num = item.get("line_number", item.get("line", 1))
        if not isinstance(line_num, int):
            try:
                line_num = int(line_num)
            except (ValueError, TypeError):
                line_num = 1
        
        # Validate risk level
        risk_level = str(item.get("risk_level", "medium")).lower()
        if risk_level not in ("critical", "high", "medium", "low"):
            risk_level = "medium"
        
        # Ensure non-empty values for required fields (empty string should use default)
        title = str(item.get("title") or "Unnamed Issue")[:200]
        description = str(item.get("description") or "No description provided")
        solution = str(item.get("solution") or "Review and fix the issue")
        
        issue = {
            "location": f"{file_path}:{line_num}",
            "type": issue_type,
            "risk_level": risk_level,
            "title": title,
            "description": description,
            "code_snippet": str(item.get("code_snippet", ""))[:500],
            "solution": solution,
            "author": f"{issue_type.capitalize()}Agent (LLM)",
        }
        issues.append(issue)
    
    return issues

