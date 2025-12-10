"""
Code Analysis Tools for the Multi-Agent System.

This module provides LangChain-compatible tools for:
- File reading and directory traversal
- AST parsing for Python code analysis
- Pattern matching for issue detection

Each tool returns structured data and handles errors gracefully.
"""

import ast
import fnmatch
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from langchain_core.tools import tool


# =============================================================================
# Constants
# =============================================================================

# Default patterns to ignore when scanning directories
DEFAULT_IGNORE_PATTERNS = [
    "__pycache__",
    "*.pyc",
    ".git",
    ".git/*",
    "node_modules",
    "node_modules/*",
    "venv",
    "venv/*",
    ".venv",
    ".venv/*",
    "env",
    "env/*",
    ".env",
    "dist",
    "dist/*",
    "build",
    "build/*",
    "*.egg-info",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    ".nox",
    "*.so",
    "*.egg",
]

# Maximum file size to read (1MB)
MAX_FILE_SIZE = 1024 * 1024


# =============================================================================
# File Operations
# =============================================================================

@tool
def read_file(filepath: str) -> str:
    """
    Read the contents of a file.
    
    Args:
        filepath: Path to the file to read
        
    Returns:
        File contents as string, or error message if file cannot be read
    """
    return _read_file_impl(filepath)


def _read_file_impl(filepath: str) -> str:
    """Implementation of read_file (non-tool version for internal use)."""
    try:
        path = Path(filepath)
        
        if not path.exists():
            return f"[ERROR] File not found: {filepath}"
        
        if not path.is_file():
            return f"[ERROR] Not a file: {filepath}"
        
        # Check file size
        file_size = path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            return f"[ERROR] File too large ({file_size} bytes > {MAX_FILE_SIZE} bytes): {filepath}"
        
        # Read file with UTF-8 encoding, falling back to latin-1
        try:
            return path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            return path.read_text(encoding='latin-1')
            
    except PermissionError:
        return f"[ERROR] Permission denied: {filepath}"
    except Exception as e:
        return f"[ERROR] Failed to read file: {filepath} - {str(e)}"


@tool
def list_python_files(
    directory: str,
    ignore_patterns: Optional[List[str]] = None
) -> List[str]:
    """
    List all Python files in a directory, excluding ignored patterns.
    
    Args:
        directory: Path to the directory to scan
        ignore_patterns: List of glob patterns to ignore (uses defaults if None)
        
    Returns:
        List of Python file paths (relative to the directory)
    """
    return _list_python_files_impl(directory, ignore_patterns)


def _list_python_files_impl(
    directory: str,
    ignore_patterns: Optional[List[str]] = None
) -> List[str]:
    """Implementation of list_python_files (non-tool version for internal use)."""
    try:
        base_path = Path(directory)
        
        if not base_path.exists():
            return [f"[ERROR] Directory not found: {directory}"]
        
        if not base_path.is_dir():
            return [f"[ERROR] Not a directory: {directory}"]
        
        patterns = ignore_patterns or DEFAULT_IGNORE_PATTERNS
        python_files = []
        
        for file_path in base_path.rglob("*.py"):
            # Get relative path for pattern matching
            relative_path = str(file_path.relative_to(base_path))
            
            # Check if any part of the path matches ignore patterns
            should_ignore = False
            for pattern in patterns:
                # Check if pattern matches any part of the path
                if fnmatch.fnmatch(relative_path, pattern):
                    should_ignore = True
                    break
                # Also check each path component
                for part in file_path.parts:
                    if fnmatch.fnmatch(part, pattern):
                        should_ignore = True
                        break
                if should_ignore:
                    break
            
            if not should_ignore:
                python_files.append(str(file_path))
        
        return sorted(python_files)
        
    except PermissionError:
        return [f"[ERROR] Permission denied: {directory}"]
    except Exception as e:
        return [f"[ERROR] Failed to list files: {directory} - {str(e)}"]


# =============================================================================
# AST Analysis
# =============================================================================

@tool
def extract_functions(code: str) -> List[Dict[str, Any]]:
    """
    Extract function definitions from Python code using AST parsing.
    
    Args:
        code: Python source code as string
        
    Returns:
        List of dictionaries containing function metadata:
        - name: Function name
        - line_start: Starting line number
        - line_end: Ending line number
        - args: List of argument names
        - decorators: List of decorator names
        - docstring: Function docstring (if present)
        - is_async: Whether the function is async
    """
    return _extract_functions_impl(code)


def _extract_functions_impl(code: str) -> List[Dict[str, Any]]:
    """Implementation of extract_functions (non-tool version for internal use)."""
    try:
        tree = ast.parse(code)
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_info = {
                    "name": node.name,
                    "line_start": node.lineno,
                    "line_end": node.end_lineno or node.lineno,
                    "args": [arg.arg for arg in node.args.args],
                    "decorators": [_get_decorator_name(d) for d in node.decorator_list],
                    "docstring": ast.get_docstring(node),
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                }
                functions.append(func_info)
        
        return functions
        
    except SyntaxError as e:
        return [{
            "error": "SyntaxError",
            "message": str(e),
            "line": e.lineno,
        }]
    except Exception as e:
        return [{
            "error": "ParseError",
            "message": str(e),
        }]


@tool
def extract_classes(code: str) -> List[Dict[str, Any]]:
    """
    Extract class definitions from Python code using AST parsing.
    
    Args:
        code: Python source code as string
        
    Returns:
        List of dictionaries containing class metadata:
        - name: Class name
        - line_start: Starting line number
        - line_end: Ending line number
        - bases: List of base class names
        - methods: List of method names
        - decorators: List of decorator names
        - docstring: Class docstring (if present)
    """
    return _extract_classes_impl(code)


def _extract_classes_impl(code: str) -> List[Dict[str, Any]]:
    """Implementation of extract_classes (non-tool version for internal use)."""
    try:
        tree = ast.parse(code)
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.append(item.name)
                
                class_info = {
                    "name": node.name,
                    "line_start": node.lineno,
                    "line_end": node.end_lineno or node.lineno,
                    "bases": [_get_name(base) for base in node.bases],
                    "methods": methods,
                    "decorators": [_get_decorator_name(d) for d in node.decorator_list],
                    "docstring": ast.get_docstring(node),
                }
                classes.append(class_info)
        
        return classes
        
    except SyntaxError as e:
        return [{
            "error": "SyntaxError",
            "message": str(e),
            "line": e.lineno,
        }]
    except Exception as e:
        return [{
            "error": "ParseError",
            "message": str(e),
        }]


@tool
def extract_imports(code: str) -> List[Dict[str, Any]]:
    """
    Extract import statements from Python code.
    
    Args:
        code: Python source code as string
        
    Returns:
        List of dictionaries containing import information:
        - type: "import" or "from"
        - module: Module name
        - names: List of imported names (for "from" imports)
        - alias: Alias if present
        - line: Line number
    """
    return _extract_imports_impl(code)


def _extract_imports_impl(code: str) -> List[Dict[str, Any]]:
    """Implementation of extract_imports (non-tool version for internal use)."""
    try:
        tree = ast.parse(code)
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        "type": "import",
                        "module": alias.name,
                        "names": [],
                        "alias": alias.asname,
                        "line": node.lineno,
                    })
            elif isinstance(node, ast.ImportFrom):
                imports.append({
                    "type": "from",
                    "module": node.module or "",
                    "names": [alias.name for alias in node.names],
                    "alias": None,
                    "line": node.lineno,
                })
        
        return imports
        
    except SyntaxError as e:
        return [{
            "error": "SyntaxError",
            "message": str(e),
            "line": e.lineno,
        }]
    except Exception as e:
        return [{
            "error": "ParseError",
            "message": str(e),
        }]


def _get_decorator_name(node: ast.expr) -> str:
    """Extract decorator name from AST node."""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return f"{_get_name(node.value)}.{node.attr}"
    elif isinstance(node, ast.Call):
        return _get_decorator_name(node.func)
    return "<unknown>"


def _get_name(node: ast.expr) -> str:
    """Extract name from AST expression node."""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return f"{_get_name(node.value)}.{node.attr}"
    elif isinstance(node, ast.Subscript):
        return f"{_get_name(node.value)}[...]"
    return "<unknown>"


# =============================================================================
# Pattern Matching
# =============================================================================

@tool
def find_pattern(code: str, pattern: str) -> List[Dict[str, Any]]:
    """
    Find regex pattern matches in code with line numbers.
    
    Args:
        code: Source code as string
        pattern: Regular expression pattern to search for
        
    Returns:
        List of dictionaries containing match information:
        - line_number: Line number of the match
        - line_content: Full line containing the match
        - match: The matched text
        - start: Start position in line
        - end: End position in line
    """
    return _find_pattern_impl(code, pattern)


def _find_pattern_impl(code: str, pattern: str) -> List[Dict[str, Any]]:
    """Implementation of find_pattern (non-tool version for internal use)."""
    try:
        regex = re.compile(pattern, re.MULTILINE)
        matches = []
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, start=1):
            for match in regex.finditer(line):
                matches.append({
                    "line_number": line_num,
                    "line_content": line.strip(),
                    "match": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                })
        
        return matches
        
    except re.error as e:
        return [{
            "error": "RegexError",
            "message": str(e),
        }]
    except Exception as e:
        return [{
            "error": "Error",
            "message": str(e),
        }]


# =============================================================================
# Security Pattern Detection
# =============================================================================

# Common security vulnerability patterns
SECURITY_PATTERNS = {
    "sql_injection": r"(execute|cursor\.execute|raw|RawSQL)\s*\([^)]*[\"'].*%s|{.*}|\+.*\+",
    "hardcoded_secret": r"(API_KEY|SECRET|PASSWORD|TOKEN|PRIVATE_KEY)\s*=\s*[\"'][^\"']+[\"']",
    "eval_usage": r"\beval\s*\(",
    "exec_usage": r"\bexec\s*\(",
    "pickle_loads": r"pickle\.(loads|load)\s*\(",
    "shell_injection": r"(os\.system|subprocess\.call|subprocess\.run|subprocess\.Popen)\s*\([^)]*[\"'].*\+|\{|\$",
    "unsafe_yaml": r"yaml\.(load|unsafe_load)\s*\(",
    "hardcoded_ip": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    "debug_true": r"DEBUG\s*=\s*True",
    "insecure_hash": r"(md5|sha1)\s*\(",
}

# Common performance issue patterns
PERFORMANCE_PATTERNS = {
    "n_plus_one": r"for\s+\w+\s+in\s+\w+:\s*\n\s+.*\.(query|execute|get|filter)\s*\(",
    "select_all": r"SELECT\s+\*\s+FROM",
    "no_limit_query": r"\.(all|filter)\s*\(\s*\)(?!\s*\[\s*:\s*\d+\s*\])",
    "string_concat_loop": r"for\s+.*:\s*\n\s+\w+\s*\+=\s*[\"']",
    "global_variable": r"^global\s+\w+",
    "nested_loops": r"for\s+\w+\s+in\s+\w+:\s*\n\s+for\s+\w+\s+in\s+\w+:",
    "repeated_computation": r"(\w+\([^)]*\))\s*[+\-*/]\s*\1",
}

# Common architecture issue patterns
ARCHITECTURE_PATTERNS = {
    "god_class": r"class\s+\w+[^:]*:\s*\n(?:[^\n]*\n){100,}",
    "long_function": r"def\s+\w+[^:]*:\s*\n(?:[^\n]*\n){50,}",
    "too_many_params": r"def\s+\w+\s*\([^)]{100,}\)",
    "magic_number": r"(?<![\"'\w])\b(?!0\b|1\b)\d{2,}\b(?![\"'\w])",
    "todo_fixme": r"#\s*(TODO|FIXME|XXX|HACK|BUG)",
    "bare_except": r"except\s*:",
    "pass_in_except": r"except[^:]*:\s*\n\s+pass",
    "unused_import": r"^import\s+\w+\s*$|^from\s+\w+\s+import\s+\w+\s*$",
    "wildcard_import": r"from\s+\w+\s+import\s+\*",
}


@tool
def find_security_issues(code: str) -> List[Dict[str, Any]]:
    """
    Find common security vulnerability patterns in code.
    
    Args:
        code: Source code as string
        
    Returns:
        List of potential security issues with pattern name, line number, and matched code
    """
    return _find_issues_by_patterns(code, SECURITY_PATTERNS, "security")


@tool
def find_performance_issues(code: str) -> List[Dict[str, Any]]:
    """
    Find common performance issue patterns in code.
    
    Args:
        code: Source code as string
        
    Returns:
        List of potential performance issues with pattern name, line number, and matched code
    """
    return _find_issues_by_patterns(code, PERFORMANCE_PATTERNS, "performance")


@tool
def find_architecture_issues(code: str) -> List[Dict[str, Any]]:
    """
    Find common architecture/code quality issue patterns in code.
    
    Args:
        code: Source code as string
        
    Returns:
        List of potential architecture issues with pattern name, line number, and matched code
    """
    return _find_issues_by_patterns(code, ARCHITECTURE_PATTERNS, "architecture")


def _find_issues_by_patterns(
    code: str,
    patterns: Dict[str, str],
    category: str
) -> List[Dict[str, Any]]:
    """Find issues matching a set of patterns."""
    issues = []
    
    for pattern_name, pattern in patterns.items():
        try:
            matches = _find_pattern_impl(code, pattern)
            for match in matches:
                if "error" not in match:
                    issues.append({
                        "category": category,
                        "pattern": pattern_name,
                        "line_number": match["line_number"],
                        "line_content": match["line_content"],
                        "match": match["match"],
                    })
        except Exception:
            continue
    
    return issues


# =============================================================================
# Code Metrics
# =============================================================================

@tool
def get_code_metrics(code: str) -> Dict[str, Any]:
    """
    Calculate basic code metrics for Python code.
    
    Args:
        code: Python source code as string
        
    Returns:
        Dictionary containing:
        - lines_total: Total number of lines
        - lines_code: Lines of actual code
        - lines_blank: Blank lines
        - lines_comment: Comment lines
        - functions_count: Number of functions
        - classes_count: Number of classes
        - imports_count: Number of imports
        - complexity_estimate: Rough complexity estimate
    """
    return _get_code_metrics_impl(code)


def _get_code_metrics_impl(code: str) -> Dict[str, Any]:
    """Implementation of get_code_metrics (non-tool version for internal use)."""
    lines = code.split('\n')
    lines_total = len(lines)
    lines_blank = sum(1 for line in lines if not line.strip())
    lines_comment = sum(1 for line in lines if line.strip().startswith('#'))
    lines_code = lines_total - lines_blank - lines_comment
    
    # Get AST-based metrics
    functions = _extract_functions_impl(code)
    classes = _extract_classes_impl(code)
    imports = _extract_imports_impl(code)
    
    # Count only valid results (no errors)
    functions_count = len([f for f in functions if "error" not in f])
    classes_count = len([c for c in classes if "error" not in c])
    imports_count = len([i for i in imports if "error" not in i])
    
    # Rough complexity estimate based on various factors
    complexity = (
        functions_count * 2 +
        classes_count * 3 +
        lines_code // 50 +
        len(_find_pattern_impl(code, r'\bif\b')) +
        len(_find_pattern_impl(code, r'\bfor\b')) +
        len(_find_pattern_impl(code, r'\bwhile\b')) +
        len(_find_pattern_impl(code, r'\btry\b'))
    )
    
    return {
        "lines_total": lines_total,
        "lines_code": lines_code,
        "lines_blank": lines_blank,
        "lines_comment": lines_comment,
        "functions_count": functions_count,
        "classes_count": classes_count,
        "imports_count": imports_count,
        "complexity_estimate": complexity,
    }


# =============================================================================
# Utility Functions (not tools, for direct Python use)
# =============================================================================

def analyze_file(filepath: str) -> Dict[str, Any]:
    """
    Perform comprehensive analysis on a single Python file.
    
    Args:
        filepath: Path to the Python file
        
    Returns:
        Dictionary containing all analysis results
    """
    content = _read_file_impl(filepath)
    
    if content.startswith("[ERROR]"):
        return {"error": content, "filepath": filepath}
    
    return {
        "filepath": filepath,
        "metrics": _get_code_metrics_impl(content),
        "functions": _extract_functions_impl(content),
        "classes": _extract_classes_impl(content),
        "imports": _extract_imports_impl(content),
        "security_issues": _find_issues_by_patterns(content, SECURITY_PATTERNS, "security"),
        "performance_issues": _find_issues_by_patterns(content, PERFORMANCE_PATTERNS, "performance"),
        "architecture_issues": _find_issues_by_patterns(content, ARCHITECTURE_PATTERNS, "architecture"),
    }


def analyze_directory(
    directory: str,
    ignore_patterns: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Analyze all Python files in a directory.
    
    Args:
        directory: Path to the directory
        ignore_patterns: Patterns to ignore
        
    Returns:
        List of analysis results for each file
    """
    files = _list_python_files_impl(directory, ignore_patterns)
    
    if files and files[0].startswith("[ERROR]"):
        return [{"error": files[0]}]
    
    results = []
    for filepath in files:
        results.append(analyze_file(filepath))
    
    return results

