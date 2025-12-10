"""
Specialist Agents for the Code Analysis Multi-Agent System.

This module contains three specialist agents with LLM integration:
- Security Agent: Analyzes code for security vulnerabilities
- Performance Agent: Analyzes code for performance issues
- Architecture Agent: Analyzes code for design/architecture problems

Each agent:
1. Uses LLM for intelligent analysis when available
2. Falls back to pattern-based detection if LLM fails
3. Combines both approaches for comprehensive coverage
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

from tools.code_tools import (
    _extract_functions_impl,
    _extract_classes_impl,
    _extract_imports_impl,
    _find_issues_by_patterns,
    _get_code_metrics_impl,
    SECURITY_PATTERNS,
    PERFORMANCE_PATTERNS,
    ARCHITECTURE_PATTERNS,
)
from prompts.templates import (
    get_security_prompt,
    get_performance_prompt,
    get_architecture_prompt,
    parse_llm_issues,
)

logger = logging.getLogger(__name__)


# =============================================================================
# LLM Integration Helpers
# =============================================================================

def _get_llm_safe():
    """Safely get LLM instance, returning None if unavailable."""
    try:
        from config import get_settings, get_llm
        settings = get_settings()
        
        if not settings.use_llm_analysis:
            return None
        
        return get_llm()
    except Exception as e:
        logger.warning(f"Failed to initialize LLM: {e}")
        return None


def _invoke_llm_safe(llm, prompt, **kwargs) -> Optional[str]:
    """Safely invoke LLM, returning None on failure."""
    try:
        messages = prompt.format_messages(**kwargs)
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        logger.warning(f"LLM invocation failed: {e}")
        return None


def _format_functions_for_prompt(functions: List[dict]) -> str:
    """Format functions list for prompt context."""
    if not functions or (len(functions) == 1 and "error" in functions[0]):
        return "None found"
    
    formatted = []
    for func in functions[:10]:  # Limit to 10
        if "error" not in func:
            args = ", ".join(func.get("args", [])[:5])
            formatted.append(f"- {func['name']}({args}) at line {func.get('line_start', '?')}")
    
    if len(functions) > 10:
        formatted.append(f"... and {len(functions) - 10} more")
    
    return "\n".join(formatted) if formatted else "None found"


def _format_classes_for_prompt(classes: List[dict]) -> str:
    """Format classes list for prompt context."""
    if not classes or (len(classes) == 1 and "error" in classes[0]):
        return "None found"
    
    formatted = []
    for cls in classes[:10]:  # Limit to 10
        if "error" not in cls:
            methods = ", ".join(cls.get("methods", [])[:5])
            formatted.append(f"- {cls['name']} (methods: {methods}) at line {cls.get('line_start', '?')}")
    
    if len(classes) > 10:
        formatted.append(f"... and {len(classes) - 10} more")
    
    return "\n".join(formatted) if formatted else "None found"


def _format_imports_for_prompt(imports: List[dict]) -> str:
    """Format imports list for prompt context."""
    if not imports or (len(imports) == 1 and "error" in imports[0]):
        return "None found"
    
    formatted = []
    for imp in imports[:15]:  # Limit to 15
        if "error" not in imp:
            if imp.get("type") == "from":
                names = ", ".join(imp.get("names", [])[:3])
                formatted.append(f"from {imp['module']} import {names}")
            else:
                formatted.append(f"import {imp['module']}")
    
    if len(imports) > 15:
        formatted.append(f"... and {len(imports) - 15} more")
    
    return "\n".join(formatted) if formatted else "None found"


def _truncate_code(code: str, max_lines: int = 200) -> str:
    """Truncate code to fit within context limits."""
    lines = code.split('\n')
    if len(lines) <= max_lines:
        return code
    
    # Take first and last portions
    half = max_lines // 2
    truncated = lines[:half] + [f"\n# ... ({len(lines) - max_lines} lines truncated) ...\n"] + lines[-half:]
    return '\n'.join(truncated)


# =============================================================================
# Security Agent
# =============================================================================

def security_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Security agent node with LLM integration.
    
    Analyzes the current file for security vulnerabilities using:
    1. LLM-based analysis (when available)
    2. Pattern-based detection (always)
    3. Deduplication of findings
    
    Args:
        state: Current analysis state
        
    Returns:
        Updated state with security issues and messages
    """
    current_file = state.get("current_file", "")
    content = state.get("current_file_content", "")
    analyzed_by = list(state.get("current_file_analyzed_by", []))
    
    messages = []
    issues = []
    llm_used = False
    
    if not content or not current_file:
        return {
            "current_file_analyzed_by": analyzed_by + ["security"],
            "messages": [{
                "role": "security",
                "content": "No file content to analyze",
                "timestamp": datetime.now().isoformat(),
                "metadata": {"action": "skip"}
            }]
        }
    
    # Extract code structure for context
    functions = _extract_functions_impl(content)
    classes = _extract_classes_impl(content)
    imports = _extract_imports_impl(content)
    
    # Try LLM-based analysis first
    llm = _get_llm_safe()
    if llm:
        try:
            prompt = get_security_prompt()
            response = _invoke_llm_safe(
                llm,
                prompt,
                file_path=current_file,
                code=_truncate_code(content),
                functions=_format_functions_for_prompt(functions),
                classes=_format_classes_for_prompt(classes),
                imports=_format_imports_for_prompt(imports),
            )
            
            if response:
                llm_issues = parse_llm_issues(response, current_file, "security")
                issues.extend(llm_issues)
                llm_used = True
                logger.info(f"LLM found {len(llm_issues)} security issues in {current_file}")
        except Exception as e:
            logger.warning(f"LLM security analysis failed: {e}")
    
    # Always run pattern-based detection for coverage
    pattern_findings = _find_issues_by_patterns(content, SECURITY_PATTERNS, "security")
    
    for finding in pattern_findings:
        # Check if this issue is already found by LLM (by line number and similar title)
        is_duplicate = any(
            abs(int(issue.get("location", ":0").split(":")[-1]) - finding["line_number"]) <= 2
            for issue in issues
        )
        
        if not is_duplicate:
            risk_level = _determine_security_risk(finding["pattern"])
            issue = {
                "location": f"{current_file}:{finding['line_number']}",
                "type": "security",
                "risk_level": risk_level,
                "title": _get_security_title(finding["pattern"]),
                "description": _get_security_description(finding["pattern"], finding["match"]),
                "code_snippet": finding["line_content"],
                "solution": _get_security_solution(finding["pattern"]),
                "author": "SecurityAgent (Pattern)",
            }
            issues.append(issue)
    
    messages.append({
        "role": "security",
        "content": f"Found {len(issues)} security issues in {current_file}" + 
                   (f" (LLM: {sum(1 for i in issues if 'LLM' in i.get('author', ''))})" if llm_used else " (pattern-only)"),
        "timestamp": datetime.now().isoformat(),
        "metadata": {
            "action": "analyze",
            "file": current_file,
            "issues_found": len(issues),
            "llm_used": llm_used
        }
    })
    
    return {
        "current_file_analyzed_by": analyzed_by + ["security"],
        "issues": issues,
        "messages": messages,
    }


def _determine_security_risk(pattern: str) -> str:
    """Determine risk level based on security pattern."""
    critical_patterns = ["sql_injection", "eval_usage", "exec_usage", "pickle_loads", "shell_injection"]
    high_patterns = ["hardcoded_secret", "unsafe_yaml"]
    medium_patterns = ["debug_true", "insecure_hash"]
    
    if pattern in critical_patterns:
        return "critical"
    elif pattern in high_patterns:
        return "high"
    elif pattern in medium_patterns:
        return "medium"
    return "low"


def _get_security_title(pattern: str) -> str:
    """Get human-readable title for security pattern."""
    titles = {
        "sql_injection": "Potential SQL Injection",
        "hardcoded_secret": "Hardcoded Secret/Credential",
        "eval_usage": "Unsafe eval() Usage",
        "exec_usage": "Unsafe exec() Usage",
        "pickle_loads": "Unsafe Pickle Deserialization",
        "shell_injection": "Potential Shell Injection",
        "unsafe_yaml": "Unsafe YAML Loading",
        "hardcoded_ip": "Hardcoded IP Address",
        "debug_true": "Debug Mode Enabled",
        "insecure_hash": "Insecure Hash Algorithm",
    }
    return titles.get(pattern, f"Security Issue: {pattern}")


def _get_security_description(pattern: str, match: str) -> str:
    """Get description for security pattern."""
    descriptions = {
        "sql_injection": f"Detected potential SQL injection vulnerability. User input may be directly concatenated into SQL query: `{match[:50]}...`",
        "hardcoded_secret": f"Found hardcoded secret or credential in source code: `{match[:30]}...`. This exposes sensitive information.",
        "eval_usage": "Using eval() with external input can execute arbitrary code and is a critical security risk.",
        "exec_usage": "Using exec() with external input can execute arbitrary code and is a critical security risk.",
        "pickle_loads": "pickle.loads() can execute arbitrary code during deserialization. Never unpickle data from untrusted sources.",
        "shell_injection": f"Shell command appears to include external input: `{match[:50]}...`. This could allow command injection.",
        "unsafe_yaml": "yaml.load() without Loader parameter can execute arbitrary code. Use yaml.safe_load() instead.",
        "hardcoded_ip": f"Hardcoded IP address found: `{match}`. Consider using configuration or environment variables.",
        "debug_true": "Debug mode is enabled in code. Ensure this is disabled in production.",
        "insecure_hash": "MD5 or SHA1 are cryptographically weak. Use SHA-256 or stronger for security purposes.",
    }
    return descriptions.get(pattern, f"Security concern detected: {pattern}")


def _get_security_solution(pattern: str) -> str:
    """Get solution recommendation for security pattern."""
    solutions = {
        "sql_injection": "Use parameterized queries or an ORM with proper escaping. Never concatenate user input into SQL.",
        "hardcoded_secret": "Move secrets to environment variables or a secure secrets manager. Never commit secrets to source control.",
        "eval_usage": "Avoid eval(). If dynamic execution is needed, use ast.literal_eval() for safe evaluation of literals.",
        "exec_usage": "Avoid exec(). Consider safer alternatives like importlib for dynamic imports.",
        "pickle_loads": "Use JSON or other safe serialization formats. If pickle is required, only unpickle trusted data.",
        "shell_injection": "Use subprocess with shell=False and pass arguments as a list. Validate and sanitize all inputs.",
        "unsafe_yaml": "Replace yaml.load() with yaml.safe_load() or specify Loader=yaml.SafeLoader.",
        "hardcoded_ip": "Use environment variables or configuration files for IP addresses to support different environments.",
        "debug_true": "Use environment variables to control debug mode. Set DEBUG=False for production.",
        "insecure_hash": "Use hashlib.sha256() or hashlib.sha3_256() for security-sensitive hashing.",
    }
    return solutions.get(pattern, "Review and fix the security concern following security best practices.")


# =============================================================================
# Performance Agent
# =============================================================================

def performance_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Performance agent node with LLM integration.
    
    Analyzes the current file for performance issues using:
    1. LLM-based analysis (when available)
    2. Pattern-based detection (always)
    3. Code metrics analysis
    
    Args:
        state: Current analysis state
        
    Returns:
        Updated state with performance issues and messages
    """
    current_file = state.get("current_file", "")
    content = state.get("current_file_content", "")
    analyzed_by = list(state.get("current_file_analyzed_by", []))
    
    messages = []
    issues = []
    llm_used = False
    
    if not content or not current_file:
        return {
            "current_file_analyzed_by": analyzed_by + ["performance"],
            "messages": [{
                "role": "performance",
                "content": "No file content to analyze",
                "timestamp": datetime.now().isoformat(),
                "metadata": {"action": "skip"}
            }]
        }
    
    # Extract code metrics
    metrics = _get_code_metrics_impl(content)
    functions = _extract_functions_impl(content)
    classes = _extract_classes_impl(content)
    
    # Try LLM-based analysis first
    llm = _get_llm_safe()
    if llm:
        try:
            prompt = get_performance_prompt()
            response = _invoke_llm_safe(
                llm,
                prompt,
                file_path=current_file,
                code=_truncate_code(content),
                lines_code=metrics.get("lines_code", 0),
                functions_count=metrics.get("functions_count", 0),
                classes_count=metrics.get("classes_count", 0),
                complexity=metrics.get("complexity_estimate", 0),
            )
            
            if response:
                llm_issues = parse_llm_issues(response, current_file, "performance")
                issues.extend(llm_issues)
                llm_used = True
                logger.info(f"LLM found {len(llm_issues)} performance issues in {current_file}")
        except Exception as e:
            logger.warning(f"LLM performance analysis failed: {e}")
    
    # Run pattern-based detection
    pattern_findings = _find_issues_by_patterns(content, PERFORMANCE_PATTERNS, "performance")
    
    for finding in pattern_findings:
        is_duplicate = any(
            abs(int(issue.get("location", ":0").split(":")[-1]) - finding["line_number"]) <= 2
            for issue in issues
        )
        
        if not is_duplicate:
            risk_level = _determine_performance_risk(finding["pattern"])
            issue = {
                "location": f"{current_file}:{finding['line_number']}",
                "type": "performance",
                "risk_level": risk_level,
                "title": _get_performance_title(finding["pattern"]),
                "description": _get_performance_description(finding["pattern"], finding["match"]),
                "code_snippet": finding["line_content"],
                "solution": _get_performance_solution(finding["pattern"]),
                "author": "PerformanceAgent (Pattern)",
            }
            issues.append(issue)
    
    # Add complexity warning if code is very complex
    if metrics.get("complexity_estimate", 0) > 50 and not any("complexity" in i.get("title", "").lower() for i in issues):
        issues.append({
            "location": f"{current_file}:1",
            "type": "performance",
            "risk_level": "medium",
            "title": "High Code Complexity",
            "description": f"File has high complexity score ({metrics['complexity_estimate']}). Consider refactoring for better performance and maintainability.",
            "code_snippet": f"# Metrics: {metrics['functions_count']} functions, {metrics['classes_count']} classes",
            "solution": "Break down complex functions into smaller units. Consider extracting classes or modules.",
            "author": "PerformanceAgent (Metrics)",
        })
    
    messages.append({
        "role": "performance",
        "content": f"Found {len(issues)} performance issues in {current_file}" +
                   (f" (LLM: {sum(1 for i in issues if 'LLM' in i.get('author', ''))})" if llm_used else " (pattern-only)"),
        "timestamp": datetime.now().isoformat(),
        "metadata": {
            "action": "analyze",
            "file": current_file,
            "issues_found": len(issues),
            "complexity": metrics.get("complexity_estimate", 0),
            "llm_used": llm_used
        }
    })
    
    return {
        "current_file_analyzed_by": analyzed_by + ["performance"],
        "issues": issues,
        "messages": messages,
    }


def _determine_performance_risk(pattern: str) -> str:
    """Determine risk level based on performance pattern."""
    high_patterns = ["n_plus_one", "nested_loops"]
    medium_patterns = ["select_all", "no_limit_query", "string_concat_loop"]
    
    if pattern in high_patterns:
        return "high"
    elif pattern in medium_patterns:
        return "medium"
    return "low"


def _get_performance_title(pattern: str) -> str:
    """Get human-readable title for performance pattern."""
    titles = {
        "n_plus_one": "N+1 Query Pattern",
        "select_all": "SELECT * Query",
        "no_limit_query": "Query Without Limit",
        "string_concat_loop": "String Concatenation in Loop",
        "global_variable": "Global Variable Usage",
        "nested_loops": "Nested Loop (O(n²) complexity)",
        "repeated_computation": "Repeated Computation",
    }
    return titles.get(pattern, f"Performance Issue: {pattern}")


def _get_performance_description(pattern: str, match: str) -> str:
    """Get description for performance pattern."""
    descriptions = {
        "n_plus_one": f"Detected N+1 query pattern where database queries are made inside a loop: `{match[:50]}...`",
        "select_all": "Using SELECT * retrieves all columns, which can be inefficient. Select only needed columns.",
        "no_limit_query": "Query retrieves all records without limit, which can cause memory issues with large datasets.",
        "string_concat_loop": "String concatenation in a loop creates many intermediate strings. Use join() or list comprehension.",
        "global_variable": "Global variables can cause performance issues in multi-threaded environments and make code harder to optimize.",
        "nested_loops": f"Nested loops detected: `{match[:40]}...`. This has O(n²) complexity and can be slow for large inputs.",
        "repeated_computation": f"Same computation appears to be repeated: `{match[:40]}...`. Consider caching the result.",
    }
    return descriptions.get(pattern, f"Performance concern detected: {pattern}")


def _get_performance_solution(pattern: str) -> str:
    """Get solution recommendation for performance pattern."""
    solutions = {
        "n_plus_one": "Use eager loading (prefetch_related, select_related) or batch queries to reduce database round trips.",
        "select_all": "Specify only the columns you need: SELECT col1, col2 FROM table instead of SELECT *.",
        "no_limit_query": "Add LIMIT clause or use pagination (.all()[:100] or .paginate()) to avoid loading entire tables.",
        "string_concat_loop": "Use ''.join(list_of_strings) or build a list and join at the end.",
        "global_variable": "Pass values as function parameters or use dependency injection. Consider using a class to encapsulate state.",
        "nested_loops": "Consider using sets for O(1) lookups, dictionary-based approaches, or algorithmic optimizations.",
        "repeated_computation": "Cache the result in a variable or use functools.lru_cache for function memoization.",
    }
    return solutions.get(pattern, "Review and optimize for better performance.")


# =============================================================================
# Architecture Agent
# =============================================================================

def architecture_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Architecture agent node with LLM integration.
    
    Analyzes the current file for architecture/design issues using:
    1. LLM-based analysis (when available)
    2. Pattern-based detection (always)
    3. Structural analysis (function/class size)
    
    Args:
        state: Current analysis state
        
    Returns:
        Updated state with architecture issues and messages
    """
    current_file = state.get("current_file", "")
    content = state.get("current_file_content", "")
    analyzed_by = list(state.get("current_file_analyzed_by", []))
    
    messages = []
    issues = []
    llm_used = False
    
    if not content or not current_file:
        return {
            "current_file_analyzed_by": analyzed_by + ["architecture"],
            "messages": [{
                "role": "architecture",
                "content": "No file content to analyze",
                "timestamp": datetime.now().isoformat(),
                "metadata": {"action": "skip"}
            }]
        }
    
    # Extract structure
    functions = _extract_functions_impl(content)
    classes = _extract_classes_impl(content)
    metrics = _get_code_metrics_impl(content)
    
    # Try LLM-based analysis first
    llm = _get_llm_safe()
    if llm:
        try:
            prompt = get_architecture_prompt()
            response = _invoke_llm_safe(
                llm,
                prompt,
                file_path=current_file,
                code=_truncate_code(content),
                functions=_format_functions_for_prompt(functions),
                classes=_format_classes_for_prompt(classes),
                lines_total=metrics.get("lines_total", 0),
                lines_code=metrics.get("lines_code", 0),
            )
            
            if response:
                llm_issues = parse_llm_issues(response, current_file, "architecture")
                issues.extend(llm_issues)
                llm_used = True
                logger.info(f"LLM found {len(llm_issues)} architecture issues in {current_file}")
        except Exception as e:
            logger.warning(f"LLM architecture analysis failed: {e}")
    
    # Run pattern-based detection
    pattern_findings = _find_issues_by_patterns(content, ARCHITECTURE_PATTERNS, "architecture")
    
    for finding in pattern_findings:
        is_duplicate = any(
            abs(int(issue.get("location", ":0").split(":")[-1]) - finding["line_number"]) <= 2
            for issue in issues
        )
        
        if not is_duplicate:
            risk_level = _determine_architecture_risk(finding["pattern"])
            issue = {
                "location": f"{current_file}:{finding['line_number']}",
                "type": "architecture",
                "risk_level": risk_level,
                "title": _get_architecture_title(finding["pattern"]),
                "description": _get_architecture_description(finding["pattern"], finding["match"]),
                "code_snippet": finding["line_content"],
                "solution": _get_architecture_solution(finding["pattern"]),
                "author": "ArchitectureAgent (Pattern)",
            }
            issues.append(issue)
    
    # Check for long functions (if not already found by LLM)
    for func in functions:
        if "error" not in func:
            lines = func.get("line_end", 0) - func.get("line_start", 0)
            if lines > 50:
                # Check if LLM already found this
                func_line = func.get("line_start", 0)
                is_duplicate = any(
                    abs(int(issue.get("location", ":0").split(":")[-1]) - func_line) <= 5
                    and "long" in issue.get("title", "").lower()
                    for issue in issues
                )
                
                if not is_duplicate:
                    issues.append({
                        "location": f"{current_file}:{func['line_start']}",
                        "type": "architecture",
                        "risk_level": "medium",
                        "title": "Long Function",
                        "description": f"Function `{func['name']}` is {lines} lines long. Long functions are harder to understand and test.",
                        "code_snippet": f"def {func['name']}({', '.join(func.get('args', [])[:3])}...):",
                        "solution": "Break down into smaller, focused functions with single responsibilities.",
                        "author": "ArchitectureAgent (Metrics)",
                    })
    
    # Check for large classes (if not already found by LLM)
    for cls in classes:
        if "error" not in cls:
            method_count = len(cls.get("methods", []))
            if method_count > 10:
                cls_line = cls.get("line_start", 0)
                is_duplicate = any(
                    abs(int(issue.get("location", ":0").split(":")[-1]) - cls_line) <= 5
                    and ("god" in issue.get("title", "").lower() or "large" in issue.get("title", "").lower())
                    for issue in issues
                )
                
                if not is_duplicate:
                    issues.append({
                        "location": f"{current_file}:{cls['line_start']}",
                        "type": "architecture",
                        "risk_level": "medium",
                        "title": "Large Class (God Object)",
                        "description": f"Class `{cls['name']}` has {method_count} methods. Large classes often violate Single Responsibility Principle.",
                        "code_snippet": f"class {cls['name']}: # {method_count} methods",
                        "solution": "Consider splitting into smaller, focused classes. Extract related methods into separate classes.",
                        "author": "ArchitectureAgent (Metrics)",
                    })
    
    messages.append({
        "role": "architecture",
        "content": f"Found {len(issues)} architecture issues in {current_file}" +
                   (f" (LLM: {sum(1 for i in issues if 'LLM' in i.get('author', ''))})" if llm_used else " (pattern-only)"),
        "timestamp": datetime.now().isoformat(),
        "metadata": {
            "action": "analyze",
            "file": current_file,
            "issues_found": len(issues),
            "functions": len([f for f in functions if "error" not in f]),
            "classes": len([c for c in classes if "error" not in c]),
            "llm_used": llm_used
        }
    })
    
    return {
        "current_file_analyzed_by": analyzed_by + ["architecture"],
        "issues": issues,
        "messages": messages,
    }


def _determine_architecture_risk(pattern: str) -> str:
    """Determine risk level based on architecture pattern."""
    high_patterns = ["god_class", "wildcard_import"]
    medium_patterns = ["long_function", "too_many_params", "bare_except", "pass_in_except"]
    
    if pattern in high_patterns:
        return "high"
    elif pattern in medium_patterns:
        return "medium"
    return "low"


def _get_architecture_title(pattern: str) -> str:
    """Get human-readable title for architecture pattern."""
    titles = {
        "god_class": "God Class (Too Large)",
        "long_function": "Long Function",
        "too_many_params": "Too Many Parameters",
        "magic_number": "Magic Number",
        "todo_fixme": "TODO/FIXME Comment",
        "bare_except": "Bare Except Clause",
        "pass_in_except": "Empty Exception Handler",
        "unused_import": "Potentially Unused Import",
        "wildcard_import": "Wildcard Import",
    }
    return titles.get(pattern, f"Architecture Issue: {pattern}")


def _get_architecture_description(pattern: str, match: str) -> str:
    """Get description for architecture pattern."""
    descriptions = {
        "god_class": "Class is very large and likely handles too many responsibilities.",
        "long_function": "Function is very long and may be doing too much.",
        "too_many_params": f"Function has many parameters: `{match[:40]}...`. This makes it hard to use and test.",
        "magic_number": f"Magic number detected: `{match}`. Unnamed numbers make code harder to understand.",
        "todo_fixme": f"Found incomplete work marker: `{match}`. This should be addressed or tracked.",
        "bare_except": "Bare except catches all exceptions including KeyboardInterrupt and SystemExit.",
        "pass_in_except": "Empty exception handler silently ignores errors, making debugging difficult.",
        "unused_import": f"Import may be unused: `{match[:40]}...`. Unused imports add clutter.",
        "wildcard_import": f"Wildcard import: `{match}`. This pollutes the namespace and makes code harder to understand.",
    }
    return descriptions.get(pattern, f"Architecture concern detected: {pattern}")


def _get_architecture_solution(pattern: str) -> str:
    """Get solution recommendation for architecture pattern."""
    solutions = {
        "god_class": "Apply Single Responsibility Principle. Split into smaller classes with focused responsibilities.",
        "long_function": "Extract smaller functions. Each function should do one thing well.",
        "too_many_params": "Consider using a configuration object, dataclass, or builder pattern to reduce parameters.",
        "magic_number": "Define named constants with meaningful names: MAX_RETRIES = 3 instead of just 3.",
        "todo_fixme": "Create a proper issue/ticket to track this work. Include context for future developers.",
        "bare_except": "Catch specific exceptions: except ValueError, TypeError: or use except Exception: at minimum.",
        "pass_in_except": "Log the exception or re-raise it. At minimum: except Exception as e: logger.error(e)",
        "unused_import": "Remove unused imports to keep code clean. Use tools like autoflake or ruff.",
        "wildcard_import": "Import specific names: from module import func1, func2 instead of from module import *",
    }
    return solutions.get(pattern, "Review and refactor following clean code principles.")
