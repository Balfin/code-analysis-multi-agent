"""
Results Compiler for the Code Analysis Multi-Agent System.

The Results Compiler is responsible for:
- Aggregating all issues from specialist agents
- Generating a summary report
- Calculating code health scores
- Grouping issues by priority and type

This is a stub implementation that will be enhanced in Phase 6.
"""

from datetime import datetime
from typing import Dict, Any, List
from collections import defaultdict


def compiler_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Results compiler node for the analysis graph.
    
    Aggregates all issues and generates a summary report including:
    - Total issue counts by type and severity
    - Code health score
    - Top critical issues
    - Recommendations
    
    Args:
        state: Current analysis state with accumulated issues
        
    Returns:
        Updated state with summary and final status
    """
    issues = state.get("issues", [])
    processed_files = state.get("processed_files", [])
    target_path = state.get("target_path", "")
    
    messages = []
    
    # Calculate statistics
    stats = _calculate_statistics(issues)
    
    # Generate summary
    summary = _generate_summary(
        target_path=target_path,
        processed_files=processed_files,
        issues=issues,
        stats=stats
    )
    
    messages.append({
        "role": "compiler",
        "content": f"Analysis complete. Generated summary with {stats['total']} issues.",
        "timestamp": datetime.now().isoformat(),
        "metadata": {
            "action": "compile",
            "total_issues": stats["total"],
            "files_analyzed": len(processed_files)
        }
    })
    
    return {
        "scan_status": "done",
        "summary": summary,
        "messages": messages,
    }


def _calculate_statistics(issues: List[dict]) -> Dict[str, Any]:
    """Calculate issue statistics."""
    stats = {
        "total": len(issues),
        "by_type": defaultdict(int),
        "by_risk": defaultdict(int),
        "by_file": defaultdict(int),
    }
    
    for issue in issues:
        issue_type = issue.get("type", "unknown")
        risk_level = issue.get("risk_level", "unknown")
        location = issue.get("location", "unknown")
        file_path = location.split(":")[0] if ":" in location else location
        
        stats["by_type"][issue_type] += 1
        stats["by_risk"][risk_level] += 1
        stats["by_file"][file_path] += 1
    
    return stats


def _generate_summary(
    target_path: str,
    processed_files: List[str],
    issues: List[dict],
    stats: Dict[str, Any]
) -> str:
    """Generate a markdown summary report."""
    
    # Calculate health score (0-100)
    health_score = _calculate_health_score(issues, len(processed_files))
    health_grade = _get_health_grade(health_score)
    
    # Group issues by severity
    critical_issues = [i for i in issues if i.get("risk_level") == "critical"]
    high_issues = [i for i in issues if i.get("risk_level") == "high"]
    medium_issues = [i for i in issues if i.get("risk_level") == "medium"]
    low_issues = [i for i in issues if i.get("risk_level") == "low"]
    
    summary = f"""# Code Analysis Report

## Executive Summary

**Target:** `{target_path}`  
**Files Analyzed:** {len(processed_files)}  
**Total Issues Found:** {stats['total']}  
**Health Score:** {health_score}/100 ({health_grade})

## Issue Breakdown

### By Severity

| Severity | Count | Percentage |
|----------|-------|------------|
| 🔴 Critical | {len(critical_issues)} | {_percentage(len(critical_issues), stats['total'])}% |
| 🟠 High | {len(high_issues)} | {_percentage(len(high_issues), stats['total'])}% |
| 🟡 Medium | {len(medium_issues)} | {_percentage(len(medium_issues), stats['total'])}% |
| 🟢 Low | {len(low_issues)} | {_percentage(len(low_issues), stats['total'])}% |

### By Category

| Category | Count | Percentage |
|----------|-------|------------|
| 🔒 Security | {stats['by_type'].get('security', 0)} | {_percentage(stats['by_type'].get('security', 0), stats['total'])}% |
| ⚡ Performance | {stats['by_type'].get('performance', 0)} | {_percentage(stats['by_type'].get('performance', 0), stats['total'])}% |
| 🏗️ Architecture | {stats['by_type'].get('architecture', 0)} | {_percentage(stats['by_type'].get('architecture', 0), stats['total'])}% |

"""
    
    # Add critical issues section if any
    if critical_issues:
        summary += """## 🚨 Critical Issues (Immediate Action Required)

"""
        for i, issue in enumerate(critical_issues[:5], 1):
            summary += f"""### {i}. {issue.get('title', 'Unknown Issue')}

- **Location:** `{issue.get('location', 'Unknown')}`
- **Description:** {issue.get('description', 'No description')[:200]}...
- **Solution:** {issue.get('solution', 'No solution provided')[:200]}...

"""
    
    # Add high priority issues section if any
    if high_issues:
        summary += """## ⚠️ High Priority Issues

"""
        for i, issue in enumerate(high_issues[:5], 1):
            summary += f"- **{issue.get('title', 'Unknown')}** at `{issue.get('location', 'Unknown')}`\n"
        
        if len(high_issues) > 5:
            summary += f"\n*...and {len(high_issues) - 5} more high priority issues*\n"
        
        summary += "\n"
    
    # Add recommendations
    summary += _generate_recommendations(stats, health_score)
    
    # Add files analyzed
    summary += """## Files Analyzed

"""
    for file_path in processed_files[:20]:
        issue_count = stats["by_file"].get(file_path, 0)
        summary += f"- `{file_path}` ({issue_count} issues)\n"
    
    if len(processed_files) > 20:
        summary += f"\n*...and {len(processed_files) - 20} more files*\n"
    
    summary += f"""
---

*Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    return summary


def _calculate_health_score(issues: List[dict], file_count: int) -> int:
    """
    Calculate a health score from 0-100.
    
    Scoring:
    - Start with 100
    - Critical issues: -20 each
    - High issues: -10 each
    - Medium issues: -5 each
    - Low issues: -1 each
    - Normalize by file count
    """
    if file_count == 0:
        return 100
    
    score = 100
    
    for issue in issues:
        risk = issue.get("risk_level", "low")
        if risk == "critical":
            score -= 20
        elif risk == "high":
            score -= 10
        elif risk == "medium":
            score -= 5
        else:
            score -= 1
    
    # Normalize slightly by file count (more files = more lenient)
    normalization = min(file_count * 2, 20)
    score += normalization
    
    return max(0, min(100, score))


def _get_health_grade(score: int) -> str:
    """Convert health score to letter grade."""
    if score >= 90:
        return "A - Excellent"
    elif score >= 80:
        return "B - Good"
    elif score >= 70:
        return "C - Acceptable"
    elif score >= 60:
        return "D - Needs Improvement"
    else:
        return "F - Critical"


def _percentage(count: int, total: int) -> str:
    """Calculate percentage safely."""
    if total == 0:
        return "0"
    return f"{(count / total * 100):.1f}"


def _generate_recommendations(stats: Dict[str, Any], health_score: int) -> str:
    """Generate recommendations based on analysis results."""
    recommendations = """## Recommendations

"""
    
    rec_list = []
    
    # Security recommendations
    security_count = stats["by_type"].get("security", 0)
    if security_count > 0:
        rec_list.append(f"🔒 **Address {security_count} security issues** - Prioritize critical vulnerabilities like SQL injection and hardcoded secrets.")
    
    # Performance recommendations
    perf_count = stats["by_type"].get("performance", 0)
    if perf_count > 0:
        rec_list.append(f"⚡ **Review {perf_count} performance issues** - Focus on N+1 queries and inefficient algorithms.")
    
    # Architecture recommendations
    arch_count = stats["by_type"].get("architecture", 0)
    if arch_count > 0:
        rec_list.append(f"🏗️ **Refactor {arch_count} architecture issues** - Improve code organization and error handling.")
    
    # Health-based recommendations
    if health_score < 60:
        rec_list.append("⚠️ **Code health is critical** - Consider a dedicated sprint for technical debt reduction.")
    elif health_score < 80:
        rec_list.append("📋 **Schedule regular code reviews** - Incorporate issue fixes into sprint planning.")
    else:
        rec_list.append("✅ **Maintain code quality** - Continue following best practices and regular reviews.")
    
    for i, rec in enumerate(rec_list, 1):
        recommendations += f"{i}. {rec}\n"
    
    recommendations += "\n"
    
    return recommendations

