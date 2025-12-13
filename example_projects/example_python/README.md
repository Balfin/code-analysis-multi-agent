# Example Python Project - Bad Code Examples

This directory contains Python files with intentionally **bad code** for testing code analysis tools. 

⚠️ **DO NOT USE THIS CODE IN PRODUCTION** ⚠️

## Files and Their Issues

### `security_issues.py`
Contains security vulnerabilities:
- Hardcoded credentials and API keys
- SQL injection vulnerabilities
- Command injection vulnerabilities
- Insecure deserialization (pickle)
- Weak cryptographic practices (MD5)
- Path traversal vulnerabilities
- Insecure random number generation
- Plain text password storage

### `code_quality.py`
Contains code quality problems:
- Poor naming conventions
- Unused imports and variables
- High cyclomatic complexity
- Deeply nested code
- Code duplication
- Missing type hints
- Global mutable state
- Functions with too many parameters
- Dead/unreachable code

### `performance_issues.py`
Contains performance anti-patterns:
- O(n²) algorithms where O(n) is possible
- String concatenation in loops
- Using list for membership testing instead of set
- Repeated computation in loops
- N+1 query patterns
- Missing memoization for recursive functions
- Sequential operations that could be parallel
- Inefficient sorting algorithms

### `error_handling.py`
Contains error handling anti-patterns:
- Bare except clauses
- Catching overly broad exceptions
- Silent failure (swallowing exceptions)
- Using exceptions for flow control
- Missing exception chaining
- Cleanup code that might not run
- Return in finally blocks

### `style_issues.py`
Contains style and formatting issues:
- Inconsistent naming conventions
- Lines exceeding length limits
- Inconsistent spacing and indentation
- Multiple statements per line
- Commented-out code
- Magic numbers
- Misleading comments
- Inconsistent quote usage
- Missing docstrings

### `main.py`
Entry point combining multiple issue types:
- Mutable default arguments
- Class-level mutable state
- Print statements instead of logging
- Hardcoded configuration
- Direct use of user input
- Long if-elif chains
- Code duplication
- Complex destructors

## Usage

This project is designed to be scanned by code analysis tools to demonstrate their detection capabilities. Each file is self-contained with examples of specific issue categories.

```bash
# Example: Run a linter
pylint example_python/

# Example: Run a security scanner
bandit -r example_python/

# Example: Run type checker
mypy example_python/
```

## Issue Count Summary

| Category | Approximate Issue Count |
|----------|------------------------|
| Security | 20+ |
| Code Quality | 30+ |
| Performance | 15+ |
| Error Handling | 15+ |
| Style | 25+ |
| **Total** | **100+** |

