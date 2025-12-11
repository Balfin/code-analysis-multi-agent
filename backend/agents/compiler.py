"""
Results Compiler for the Code Analysis Multi-Agent System.

The Results Compiler is responsible for:
- Aggregating all issues from specialist agents
- Generating an executive summary (optionally with LLM)
- Calculating code health scores
- Grouping issues by priority and type
- Persisting issues to the filesystem
- Creating actionable recommendations

This is the enhanced implementation with LLM support and persistence.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import defaultdict
import logging

from models.issue import Issue, IssueStore, IssueType, RiskLevel

logger = logging.getLogger(__name__)


def compiler_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Results compiler node for the analysis graph.
    
    Aggregates all issues and generates a comprehensive report including:
    - Executive summary
    - Code health score
    - Issues grouped by severity and type
    - Top critical issues with details
    - Actionable recommendations
    - Persistence to filesystem
    
    Args:
        state: Current analysis state with accumulated issues
        
    Returns:
        Updated state with summary and final status
    """
    issues = state.get("issues", [])
    processed_files = state.get("processed_files", [])
    target_path = state.get("target_path", "")
    config = state.get("config", {})
    
    messages = []
    
    logger.info(f"Compiler processing {len(issues)} issues from {len(processed_files)} files")
    
    # Persist issues to filesystem
    saved_count = _persist_issues(issues, config)
    
    messages.append({
        "role": "compiler",
        "content": f"💾 Saved {saved_count} issues to filesystem",
        "timestamp": datetime.now().isoformat(),
        "metadata": {"action": "persist", "saved_count": saved_count}
    })
    
    # Calculate statistics
    stats = _calculate_statistics(issues, processed_files)
    
    # Generate summary (try LLM first, fallback to template)
    summary = _generate_summary_with_llm(
        target_path=target_path,
        processed_files=processed_files,
        issues=issues,
        stats=stats,
        config=config
    )
    
    messages.append({
        "role": "compiler",
        "content": f"📊 Analysis complete! Found {stats['total']} issues across {len(processed_files)} files. Health score: {stats['health_score']}/100",
        "timestamp": datetime.now().isoformat(),
        "metadata": {
            "action": "complete",
            "total_issues": stats["total"],
            "files_analyzed": len(processed_files),
            "health_score": stats["health_score"],
            "by_type": dict(stats["by_type"]),
            "by_risk": dict(stats["by_risk"])
        }
    })
    
    logger.info(f"Compiler completed: {stats['total']} issues, health score {stats['health_score']}/100")
    
    return {
        "scan_status": "done",
        "summary": summary,
        "messages": messages,
    }


def _persist_issues(issues: List[dict], config: Dict[str, Any]) -> int:
    """
    Persist all issues to the filesystem using IssueStore.
    
    Args:
        issues: List of issue dictionaries
        config: Configuration with issues_dir
        
    Returns:
        Number of issues successfully saved
    """
    issues_dir = config.get("issues_dir", "./issues")
    
    try:
        store = IssueStore(issues_dir)
        saved_count = 0
        
        for issue_data in issues:
            try:
                # Convert to Issue model
                issue = Issue(
                    location=issue_data.get("location", "unknown:0"),
                    type=IssueType(issue_data.get("type", "architecture")),
                    risk_level=RiskLevel(issue_data.get("risk_level", "low")),
                    title=issue_data.get("title", "Unnamed Issue"),
                    description=issue_data.get("description", "No description"),
                    code_snippet=issue_data.get("code_snippet", ""),
                    solution=issue_data.get("solution", "Review and fix"),
                    author=issue_data.get("author"),
                    related_issues=issue_data.get("related_issues"),
                )
                
                store.save(issue)
                saved_count += 1
                
            except Exception as e:
                logger.warning(f"Failed to save issue: {e}")
                continue
        
        logger.info(f"Persisted {saved_count} issues to {issues_dir}")
        return saved_count
        
    except Exception as e:
        logger.error(f"Failed to initialize IssueStore: {e}")
        return 0


def _calculate_statistics(issues: List[dict], processed_files: List[str]) -> Dict[str, Any]:
    """Calculate comprehensive issue statistics."""
    stats = {
        "total": len(issues),
        "by_type": defaultdict(int),
        "by_risk": defaultdict(int),
        "by_file": defaultdict(int),
        "by_author": defaultdict(int),
    }
    
    for issue in issues:
        issue_type = issue.get("type", "unknown")
        risk_level = issue.get("risk_level", "unknown")
        location = issue.get("location", "unknown")
        author = issue.get("author", "unknown")
        file_path = location.split(":")[0] if ":" in location else location
        
        stats["by_type"][issue_type] += 1
        stats["by_risk"][risk_level] += 1
        stats["by_file"][file_path] += 1
        stats["by_author"][author] += 1
    
    # Calculate health score
    stats["health_score"] = _calculate_health_score(issues, len(processed_files))
    stats["health_grade"] = _get_health_grade(stats["health_score"])
    
    return stats


def _generate_summary_with_llm(
    target_path: str,
    processed_files: List[str],
    issues: List[dict],
    stats: Dict[str, Any],
    config: Dict[str, Any]
) -> str:
    """
    Generate summary, optionally using LLM for executive summary.
    
    Args:
        target_path: Path that was analyzed
        processed_files: List of analyzed files
        issues: All detected issues
        stats: Calculated statistics
        config: Configuration
        
    Returns:
        Complete markdown summary report
    """
    # Try to generate executive summary with LLM
    executive_summary = _generate_llm_executive_summary(issues, stats, config)
    
    # Generate the full report
    return _generate_full_report(
        target_path=target_path,
        processed_files=processed_files,
        issues=issues,
        stats=stats,
        executive_summary=executive_summary
    )


def _generate_llm_executive_summary(
    issues: List[dict],
    stats: Dict[str, Any],
    config: Dict[str, Any]
) -> Optional[str]:
    """
    Generate an executive summary using LLM.
    
    Args:
        issues: All detected issues
        stats: Statistics
        config: Configuration
        
    Returns:
        Executive summary text or None if LLM unavailable
    """
    try:
        from config import get_settings, get_llm
        from langchain_core.prompts import ChatPromptTemplate
        
        settings = get_settings()
        if not settings.use_llm_analysis:
            return None
        
        # Get model override from config if specified
        model_override = config.get("model") if config else None
        llm = get_llm(model_override=model_override)
        
        # Prepare issue summary for context
        critical_issues = [i for i in issues if i.get("risk_level") == "critical"][:5]
        high_issues = [i for i in issues if i.get("risk_level") == "high"][:5]
        
        issue_context = ""
        if critical_issues:
            issue_context += "CRITICAL ISSUES:\n"
            for i in critical_issues:
                issue_context += f"- {i.get('title')} at {i.get('location')}\n"
        if high_issues:
            issue_context += "\nHIGH PRIORITY ISSUES:\n"
            for i in high_issues:
                issue_context += f"- {i.get('title')} at {i.get('location')}\n"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a senior software architect writing an executive summary for a code analysis report.
Write a concise 2-3 paragraph executive summary that:
1. Summarizes the overall code quality and main concerns
2. Highlights the most critical findings
3. Provides a brief recommendation for next steps

Be direct, professional, and actionable. Do not use markdown formatting in your response."""),
            ("human", """Code Analysis Results:
- Total Issues: {total}
- Health Score: {health_score}/100 ({health_grade})
- Security Issues: {security}
- Performance Issues: {performance}
- Architecture Issues: {architecture}
- Critical: {critical}, High: {high}, Medium: {medium}, Low: {low}

{issue_context}

Write an executive summary:""")
        ])
        
        messages = prompt.format_messages(
            total=stats["total"],
            health_score=stats["health_score"],
            health_grade=stats["health_grade"],
            security=stats["by_type"].get("security", 0),
            performance=stats["by_type"].get("performance", 0),
            architecture=stats["by_type"].get("architecture", 0),
            critical=stats["by_risk"].get("critical", 0),
            high=stats["by_risk"].get("high", 0),
            medium=stats["by_risk"].get("medium", 0),
            low=stats["by_risk"].get("low", 0),
            issue_context=issue_context or "No critical or high priority issues found."
        )
        
        response = llm.invoke(messages)
        return response.content
        
    except Exception as e:
        logger.warning(f"Failed to generate LLM executive summary: {e}")
        return None


def _generate_full_report(
    target_path: str,
    processed_files: List[str],
    issues: List[dict],
    stats: Dict[str, Any],
    executive_summary: Optional[str] = None
) -> str:
    """Generate the complete markdown report."""
    
    # Group issues by severity
    critical_issues = [i for i in issues if i.get("risk_level") == "critical"]
    high_issues = [i for i in issues if i.get("risk_level") == "high"]
    medium_issues = [i for i in issues if i.get("risk_level") == "medium"]
    low_issues = [i for i in issues if i.get("risk_level") == "low"]
    
    # Start building report
    report = f"""# 📊 Code Analysis Report

**Target:** `{target_path}`  
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Files Analyzed:** {len(processed_files)}  
**Total Issues:** {stats['total']}  
**Health Score:** {stats['health_score']}/100 ({stats['health_grade']})

---

## Executive Summary

"""
    
    # Add executive summary (LLM or generated)
    if executive_summary:
        report += executive_summary + "\n\n"
    else:
        report += _generate_default_executive_summary(stats) + "\n\n"
    
    # Issue breakdown
    report += """---

## Issue Breakdown

### By Severity

| Severity | Count | Percentage |
|----------|-------|------------|
"""
    report += f"| 🔴 Critical | {len(critical_issues)} | {_percentage(len(critical_issues), stats['total'])}% |\n"
    report += f"| 🟠 High | {len(high_issues)} | {_percentage(len(high_issues), stats['total'])}% |\n"
    report += f"| 🟡 Medium | {len(medium_issues)} | {_percentage(len(medium_issues), stats['total'])}% |\n"
    report += f"| 🟢 Low | {len(low_issues)} | {_percentage(len(low_issues), stats['total'])}% |\n"
    
    report += """
### By Category

| Category | Count | Percentage |
|----------|-------|------------|
"""
    report += f"| 🔒 Security | {stats['by_type'].get('security', 0)} | {_percentage(stats['by_type'].get('security', 0), stats['total'])}% |\n"
    report += f"| ⚡ Performance | {stats['by_type'].get('performance', 0)} | {_percentage(stats['by_type'].get('performance', 0), stats['total'])}% |\n"
    report += f"| 🏗️ Architecture | {stats['by_type'].get('architecture', 0)} | {_percentage(stats['by_type'].get('architecture', 0), stats['total'])}% |\n"
    
    # Critical issues section
    if critical_issues:
        report += """
---

## 🚨 Critical Issues (Immediate Action Required)

"""
        for i, issue in enumerate(critical_issues[:10], 1):
            report += _format_issue_detail(i, issue)
        
        if len(critical_issues) > 10:
            report += f"\n*...and {len(critical_issues) - 10} more critical issues*\n"
    
    # High priority issues
    if high_issues:
        report += """
---

## ⚠️ High Priority Issues

"""
        for i, issue in enumerate(high_issues[:10], 1):
            report += f"**{i}. {issue.get('title', 'Unknown')}**\n"
            report += f"   - Location: `{issue.get('location', 'Unknown')}`\n"
            report += f"   - {issue.get('description', 'No description')[:150]}...\n\n"
        
        if len(high_issues) > 10:
            report += f"*...and {len(high_issues) - 10} more high priority issues*\n"
    
    # Recommendations
    report += "\n---\n\n"
    report += _generate_recommendations(stats)
    
    # Files analyzed
    report += """
---

## Files Analyzed

"""
    # Sort files by issue count (highest first)
    files_with_issues = sorted(
        [(f, stats["by_file"].get(f, 0)) for f in processed_files],
        key=lambda x: x[1],
        reverse=True
    )
    
    for filepath, issue_count in files_with_issues[:20]:
        filename = filepath.split("/")[-1] if "/" in filepath else filepath
        status = "🔴" if issue_count > 5 else "🟡" if issue_count > 0 else "✅"
        report += f"- {status} `{filename}` ({issue_count} issues)\n"
    
    if len(processed_files) > 20:
        report += f"\n*...and {len(processed_files) - 20} more files*\n"
    
    # Footer
    report += f"""
---

*Report generated by Code Analysis Multi-Agent System*  
*{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    return report


def _format_issue_detail(index: int, issue: dict) -> str:
    """Format a single issue with full details."""
    return f"""### {index}. {issue.get('title', 'Unknown Issue')}

| Property | Value |
|----------|-------|
| **Type** | {issue.get('type', 'unknown').capitalize()} |
| **Risk** | {issue.get('risk_level', 'unknown').capitalize()} |
| **Location** | `{issue.get('location', 'Unknown')}` |

**Description:** {issue.get('description', 'No description')}

**Code:**
```python
{issue.get('code_snippet', 'No code snippet')[:200]}
```

**Solution:** {issue.get('solution', 'No solution provided')}

"""


def _generate_default_executive_summary(stats: Dict[str, Any]) -> str:
    """Generate a default executive summary without LLM."""
    health_score = stats["health_score"]
    total = stats["total"]
    critical = stats["by_risk"].get("critical", 0)
    high = stats["by_risk"].get("high", 0)
    security = stats["by_type"].get("security", 0)
    
    if health_score >= 90:
        quality = "excellent"
        recommendation = "Continue maintaining current code quality standards."
    elif health_score >= 80:
        quality = "good"
        recommendation = "Address the identified issues during regular maintenance cycles."
    elif health_score >= 70:
        quality = "acceptable"
        recommendation = "Prioritize fixing high and critical issues in the next sprint."
    elif health_score >= 60:
        quality = "concerning"
        recommendation = "Dedicate focused effort to address critical security and architecture issues."
    else:
        quality = "poor"
        recommendation = "Immediate attention required. Consider a dedicated technical debt reduction sprint."
    
    summary = f"The codebase demonstrates {quality} code quality with a health score of {health_score}/100. "
    
    if critical > 0:
        summary += f"There are {critical} critical issues requiring immediate attention. "
    
    if security > 0:
        summary += f"Security analysis identified {security} potential vulnerabilities that should be prioritized. "
    
    if high > 0:
        summary += f"Additionally, {high} high-priority issues were found. "
    
    summary += f"\n\n**Recommendation:** {recommendation}"
    
    return summary


def _calculate_health_score(issues: List[dict], file_count: int) -> int:
    """
    Calculate a health score from 0-100.
    
    Scoring:
    - Start with 100
    - Critical issues: -15 each (max -60)
    - High issues: -8 each (max -40)
    - Medium issues: -3 each (max -30)
    - Low issues: -1 each (max -10)
    - Bonus for clean files
    """
    if file_count == 0:
        return 100
    
    score = 100
    
    critical_penalty = 0
    high_penalty = 0
    medium_penalty = 0
    low_penalty = 0
    
    for issue in issues:
        risk = issue.get("risk_level", "low")
        if risk == "critical":
            critical_penalty += 15
        elif risk == "high":
            high_penalty += 8
        elif risk == "medium":
            medium_penalty += 3
        else:
            low_penalty += 1
    
    # Apply capped penalties
    score -= min(critical_penalty, 60)
    score -= min(high_penalty, 40)
    score -= min(medium_penalty, 30)
    score -= min(low_penalty, 10)
    
    # Small bonus for having some clean files
    issues_per_file = len(issues) / file_count if file_count > 0 else 0
    if issues_per_file < 5:
        score += 5
    
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


def _generate_recommendations(stats: Dict[str, Any]) -> str:
    """Generate recommendations based on analysis results."""
    recommendations = "## 💡 Recommendations\n\n"
    
    rec_list = []
    priority = 1
    
    # Critical issues first
    critical = stats["by_risk"].get("critical", 0)
    if critical > 0:
        rec_list.append(f"**{priority}. Address {critical} critical issues immediately** - These pose significant risk and should be fixed before any deployment.")
        priority += 1
    
    # Security recommendations
    security_count = stats["by_type"].get("security", 0)
    if security_count > 0:
        rec_list.append(f"**{priority}. Review {security_count} security issues** - Prioritize SQL injection, hardcoded secrets, and authentication flaws.")
        priority += 1
    
    # Performance recommendations
    perf_count = stats["by_type"].get("performance", 0)
    if perf_count > 0:
        rec_list.append(f"**{priority}. Optimize {perf_count} performance issues** - Focus on N+1 queries and inefficient algorithms that impact user experience.")
        priority += 1
    
    # Architecture recommendations
    arch_count = stats["by_type"].get("architecture", 0)
    if arch_count > 0:
        rec_list.append(f"**{priority}. Refactor {arch_count} architecture issues** - Improve code organization, reduce complexity, and enhance maintainability.")
        priority += 1
    
    # Health-based recommendations
    health_score = stats["health_score"]
    if health_score < 60:
        rec_list.append(f"**{priority}. Schedule technical debt sprint** - With a health score of {health_score}/100, dedicated time for code quality improvement is essential.")
    elif health_score < 80:
        rec_list.append(f"**{priority}. Incorporate fixes into sprint planning** - Allocate 10-20% of sprint capacity to address identified issues.")
    else:
        rec_list.append(f"**{priority}. Maintain code quality** - Continue code reviews and consider adding automated quality gates to CI/CD.")
    
    for rec in rec_list:
        recommendations += f"{rec}\n\n"
    
    return recommendations
