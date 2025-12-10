# Tools module
"""
Contains LangChain tools for code analysis:
- File reading and directory traversal
- AST parsing for Python code
- Pattern matching for issue detection
"""

from tools.code_tools import (
    # LangChain tools (decorated with @tool)
    read_file,
    list_python_files,
    extract_functions,
    extract_classes,
    extract_imports,
    find_pattern,
    find_security_issues,
    find_performance_issues,
    find_architecture_issues,
    get_code_metrics,
    # High-level analysis functions
    analyze_file,
    analyze_directory,
    # Constants
    DEFAULT_IGNORE_PATTERNS,
    SECURITY_PATTERNS,
    PERFORMANCE_PATTERNS,
    ARCHITECTURE_PATTERNS,
    MAX_FILE_SIZE,
)

__all__ = [
    # Tools
    "read_file",
    "list_python_files",
    "extract_functions",
    "extract_classes",
    "extract_imports",
    "find_pattern",
    "find_security_issues",
    "find_performance_issues",
    "find_architecture_issues",
    "get_code_metrics",
    # Functions
    "analyze_file",
    "analyze_directory",
    # Constants
    "DEFAULT_IGNORE_PATTERNS",
    "SECURITY_PATTERNS",
    "PERFORMANCE_PATTERNS",
    "ARCHITECTURE_PATTERNS",
    "MAX_FILE_SIZE",
]
