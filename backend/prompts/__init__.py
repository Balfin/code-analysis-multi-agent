# Prompts module
"""
Contains prompt templates for specialist agents:
- Security analysis prompts
- Performance analysis prompts
- Architecture analysis prompts
- Results compilation prompts
"""

from prompts.templates import (
    # Prompt templates
    get_security_prompt,
    get_performance_prompt,
    get_architecture_prompt,
    # Parsing utilities
    parse_llm_issues,
    # Raw prompts (for reference/customization)
    SECURITY_SYSTEM_PROMPT,
    SECURITY_HUMAN_PROMPT,
    PERFORMANCE_SYSTEM_PROMPT,
    PERFORMANCE_HUMAN_PROMPT,
    ARCHITECTURE_SYSTEM_PROMPT,
    ARCHITECTURE_HUMAN_PROMPT,
)

__all__ = [
    "get_security_prompt",
    "get_performance_prompt",
    "get_architecture_prompt",
    "parse_llm_issues",
    "SECURITY_SYSTEM_PROMPT",
    "SECURITY_HUMAN_PROMPT",
    "PERFORMANCE_SYSTEM_PROMPT",
    "PERFORMANCE_HUMAN_PROMPT",
    "ARCHITECTURE_SYSTEM_PROMPT",
    "ARCHITECTURE_HUMAN_PROMPT",
]
