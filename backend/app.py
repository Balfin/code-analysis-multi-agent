"""
AI-Powered Code Analysis Multi-Agent System - FastAPI Backend

This is the main FastAPI application that exposes REST endpoints
for code analysis, issue management, and chat functionality.

Endpoints:
- GET /health - Health check
- POST /analyze - Start code analysis on a codebase
- GET /analyze/{task_id}/status - Get analysis status (for async)
- GET /issues - Get all issues with filtering
- GET /issues/{issue_id} - Get specific issue details
- POST /chat - Chat about code issues using LLM
"""

import asyncio
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from models.issue import IssueStore, IssueType, RiskLevel
from agents.graph import run_analysis


# =============================================================================
# Configuration
# =============================================================================

ISSUES_DIR = os.getenv("ISSUES_DIR", "./issues")

# Thread pool for running sync analysis in background
executor = ThreadPoolExecutor(max_workers=2)

# In-memory storage for analysis tasks (would use Redis/DB in production)
analysis_tasks: dict[str, dict[str, Any]] = {}


# =============================================================================
# Pydantic Models
# =============================================================================

class AnalysisRequest(BaseModel):
    """Request model for starting a code analysis."""
    path: str = Field(..., description="Path to the codebase to analyze")
    file_types: list[str] = Field(
        default=["*.py"],
        description="File patterns to analyze"
    )
    async_mode: bool = Field(
        default=False,
        description="If true, returns immediately with task ID for polling"
    )


class AnalysisResponse(BaseModel):
    """Response model for analysis results."""
    status: str
    task_id: Optional[str] = None
    issues_found: Optional[int] = None
    files_analyzed: Optional[int] = None
    health_score: Optional[int] = None
    summary: Optional[str] = None
    message: Optional[str] = None


class AnalysisStatus(BaseModel):
    """Response model for analysis task status."""
    task_id: str
    status: str  # pending, running, completed, error
    progress: Optional[float] = None
    issues_found: Optional[int] = None
    files_analyzed: Optional[int] = None
    health_score: Optional[int] = None
    summary: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class IssueListResponse(BaseModel):
    """Response model for issues list."""
    issues: list[dict[str, Any]]
    total: int
    filtered_total: int
    page: int
    page_size: int


class IssueDetailResponse(BaseModel):
    """Response model for issue details."""
    id: str
    location: str
    type: str
    risk_level: str
    title: str
    description: str
    code_snippet: Optional[str] = None
    solution: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[str] = None
    markdown_content: str


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., description="User's question or message")
    context: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional context (e.g., current issue being viewed)"
    )


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str
    issues_referenced: Optional[list[str]] = None
    suggestions: Optional[list[str]] = None


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Code Analysis Multi-Agent System",
    description="""
AI-powered code analysis using multiple specialized agents.

## Features
- **Security Analysis**: Detect SQL injection, hardcoded secrets, unsafe patterns
- **Performance Analysis**: Find N+1 queries, inefficient algorithms
- **Architecture Analysis**: Identify code smells, complexity issues

## Agents
- Manager Agent: Orchestrates the workflow
- Security Expert: Identifies security vulnerabilities
- Performance Specialist: Finds performance bottlenecks
- Architecture Analyst: Reviews code structure and patterns
- Results Compiler: Aggregates findings into reports
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Helper Functions
# =============================================================================

def get_issue_store() -> IssueStore:
    """Get or create the issue store."""
    return IssueStore(ISSUES_DIR)


def run_analysis_sync(task_id: str, path: str, config: dict) -> None:
    """Run analysis synchronously (for background task)."""
    try:
        analysis_tasks[task_id]["status"] = "running"
        analysis_tasks[task_id]["started_at"] = datetime.now().isoformat()
        
        result = run_analysis(
            target_path=path,
            config=config
        )
        
        # Extract stats from summary or calculate
        issues = result.get("issues", [])
        processed = result.get("processed_files", [])
        
        # Calculate health score from issues
        critical = len([i for i in issues if i.get("risk_level") == "critical"])
        high = len([i for i in issues if i.get("risk_level") == "high"])
        medium = len([i for i in issues if i.get("risk_level") == "medium"])
        low = len([i for i in issues if i.get("risk_level") == "low"])
        
        score = 100
        score -= min(critical * 15, 60)
        score -= min(high * 8, 40)
        score -= min(medium * 3, 30)
        score -= min(low * 1, 10)
        health_score = max(0, min(100, score))
        
        analysis_tasks[task_id].update({
            "status": "completed",
            "issues_found": len(issues),
            "files_analyzed": len(processed),
            "health_score": health_score,
            "summary": result.get("summary", ""),
            "completed_at": datetime.now().isoformat(),
        })
        
    except Exception as e:
        analysis_tasks[task_id].update({
            "status": "error",
            "error": str(e),
            "completed_at": datetime.now().isoformat(),
        })


# =============================================================================
# Endpoints
# =============================================================================

@app.get("/", tags=["Info"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Code Analysis Multi-Agent System",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "health": "GET /health",
            "analyze": "POST /analyze",
            "analyze_status": "GET /analyze/{task_id}/status",
            "issues": "GET /issues",
            "issue_detail": "GET /issues/{issue_id}",
            "chat": "POST /chat",
        },
    }


@app.get("/health", tags=["Info"])
async def health_check():
    """Health check endpoint."""
    store = get_issue_store()
    return {
        "status": "healthy",
        "version": "1.0.0",
        "issues_count": store.count(),
        "timestamp": datetime.now().isoformat(),
    }


# -----------------------------------------------------------------------------
# Analysis Endpoints
# -----------------------------------------------------------------------------

@app.post("/analyze", response_model=AnalysisResponse, tags=["Analysis"])
async def analyze_codebase(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Start code analysis on a codebase.
    
    - **path**: Path to the codebase to analyze (relative or absolute)
    - **file_types**: File patterns to analyze (default: ["*.py"])
    - **async_mode**: If true, returns task ID for polling status
    
    In async mode, use GET /analyze/{task_id}/status to poll for results.
    """
    # Validate path exists
    if not os.path.exists(request.path):
        raise HTTPException(
            status_code=400,
            detail=f"Path does not exist: {request.path}"
        )
    
    config = {"issues_dir": ISSUES_DIR}
    
    if request.async_mode:
        # Async mode: start background task
        task_id = str(uuid.uuid4())[:8]
        analysis_tasks[task_id] = {
            "status": "pending",
            "path": request.path,
            "created_at": datetime.now().isoformat(),
        }
        
        # Run in thread pool
        loop = asyncio.get_event_loop()
        loop.run_in_executor(
            executor,
            run_analysis_sync,
            task_id,
            request.path,
            config
        )
        
        return AnalysisResponse(
            status="accepted",
            task_id=task_id,
            message=f"Analysis started. Poll GET /analyze/{task_id}/status for results."
        )
    
    # Sync mode: run and wait
    try:
        result = run_analysis(
            target_path=request.path,
            config=config
        )
        
        issues = result.get("issues", [])
        processed = result.get("processed_files", [])
        
        # Calculate health score
        critical = len([i for i in issues if i.get("risk_level") == "critical"])
        high = len([i for i in issues if i.get("risk_level") == "high"])
        medium = len([i for i in issues if i.get("risk_level") == "medium"])
        low = len([i for i in issues if i.get("risk_level") == "low"])
        
        score = 100
        score -= min(critical * 15, 60)
        score -= min(high * 8, 40)
        score -= min(medium * 3, 30)
        score -= min(low * 1, 10)
        health_score = max(0, min(100, score))
        
        return AnalysisResponse(
            status="completed",
            issues_found=len(issues),
            files_analyzed=len(processed),
            health_score=health_score,
            summary=result.get("summary", "")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@app.get("/analyze/{task_id}/status", response_model=AnalysisStatus, tags=["Analysis"])
async def get_analysis_status(task_id: str):
    """
    Get status of an async analysis task.
    
    Returns task progress and results when completed.
    """
    if task_id not in analysis_tasks:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis task not found: {task_id}"
        )
    
    task = analysis_tasks[task_id]
    return AnalysisStatus(
        task_id=task_id,
        status=task.get("status", "unknown"),
        progress=task.get("progress"),
        issues_found=task.get("issues_found"),
        files_analyzed=task.get("files_analyzed"),
        health_score=task.get("health_score"),
        summary=task.get("summary"),
        error=task.get("error"),
        started_at=task.get("started_at"),
        completed_at=task.get("completed_at"),
    )


# -----------------------------------------------------------------------------
# Issues Endpoints
# -----------------------------------------------------------------------------

@app.get("/issues", response_model=IssueListResponse, tags=["Issues"])
async def get_issues(
    type: Optional[str] = Query(
        None,
        description="Filter by issue type (security, performance, architecture)"
    ),
    risk_level: Optional[str] = Query(
        None,
        description="Filter by risk level (critical, high, medium, low)"
    ),
    search: Optional[str] = Query(
        None,
        description="Search in title and description"
    ),
    file: Optional[str] = Query(
        None,
        description="Filter by file path (partial match)"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """
    Get all issues with optional filtering and pagination.
    
    - **type**: Filter by security, performance, or architecture
    - **risk_level**: Filter by critical, high, medium, or low
    - **search**: Search in issue title and description
    - **file**: Filter by file path
    - **page**: Page number (1-indexed)
    - **page_size**: Number of items per page (max 100)
    """
    store = get_issue_store()
    all_issues = store.get_all()  # Returns list of dicts
    
    # Normalize dict values (handles both dicts and Issue objects)
    issues_data = []
    for issue in all_issues:
        # get_all() returns dicts, so access as dict
        issue_dict = {
            "id": issue.get("id"),
            "location": issue.get("location"),
            "type": issue.get("type"),
            "risk_level": issue.get("risk_level"),
            "title": issue.get("title"),
            "description": issue.get("description"),
            "code_snippet": issue.get("code_snippet"),
            "solution": issue.get("solution"),
            "author": issue.get("author"),
            "created_at": issue.get("created_at"),
        }
        issues_data.append(issue_dict)
    
    total = len(issues_data)
    filtered = issues_data
    
    # Apply filters
    if type:
        filtered = [i for i in filtered if i.get("type") == type]
    
    if risk_level:
        filtered = [i for i in filtered if i.get("risk_level") == risk_level]
    
    if search:
        search_lower = search.lower()
        filtered = [
            i for i in filtered
            if search_lower in i.get("title", "").lower()
            or search_lower in i.get("description", "").lower()
        ]
    
    if file:
        file_lower = file.lower()
        filtered = [
            i for i in filtered
            if file_lower in i.get("location", "").lower()
        ]
    
    filtered_total = len(filtered)
    
    # Paginate
    start = (page - 1) * page_size
    end = start + page_size
    paginated = filtered[start:end]
    
    return IssueListResponse(
        issues=paginated,
        total=total,
        filtered_total=filtered_total,
        page=page,
        page_size=page_size,
    )


@app.get("/issues/summary", tags=["Issues"])
async def get_issues_summary():
    """
    Get summary statistics for all issues.
    """
    store = get_issue_store()
    summary = store.summary()
    
    return {
        "total": summary.get("total", 0),
        "by_type": summary.get("by_type", {}),
        "by_risk_level": summary.get("by_risk_level", {}),
    }


@app.get("/issues/{issue_id}", response_model=IssueDetailResponse, tags=["Issues"])
async def get_issue_detail(issue_id: str):
    """
    Get detailed information about a specific issue.
    
    Returns full issue data including markdown content.
    """
    store = get_issue_store()
    issue = store.get_by_id(issue_id)
    
    if not issue:
        raise HTTPException(
            status_code=404,
            detail=f"Issue not found: {issue_id}"
        )
    
    # get_by_id returns dict
    markdown = store.get_markdown(issue_id) or ""
    
    return IssueDetailResponse(
        id=issue.get("id"),
        location=issue.get("location"),
        type=issue.get("type"),
        risk_level=issue.get("risk_level"),
        title=issue.get("title"),
        description=issue.get("description"),
        code_snippet=issue.get("code_snippet"),
        solution=issue.get("solution"),
        author=issue.get("author"),
        created_at=issue.get("created_at"),
        markdown_content=markdown,
    )


@app.delete("/issues/{issue_id}", tags=["Issues"])
async def delete_issue(issue_id: str):
    """
    Delete a specific issue.
    """
    store = get_issue_store()
    issue = store.get_by_id(issue_id)
    
    if not issue:
        raise HTTPException(
            status_code=404,
            detail=f"Issue not found: {issue_id}"
        )
    
    success = store.delete(issue_id)
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete issue: {issue_id}"
        )
    
    return {"status": "deleted", "id": issue_id}


# -----------------------------------------------------------------------------
# Chat Endpoint
# -----------------------------------------------------------------------------

@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_about_issues(request: ChatRequest):
    """
    Chat about code issues using the LLM.
    
    Send a question about the codebase or issues and get an AI-powered response.
    Context can include the current issue being viewed for more relevant answers.
    """
    store = get_issue_store()
    
    # Get relevant context
    all_issues = store.get_all()
    summary = store.summary()
    
    # Build context string
    context_str = f"""
Code Analysis Summary:
- Total Issues: {summary.get('total', 0)}
- Security Issues: {summary.get('by_type', {}).get('security', 0)}
- Performance Issues: {summary.get('by_type', {}).get('performance', 0)}
- Architecture Issues: {summary.get('by_type', {}).get('architecture', 0)}
- Critical: {summary.get('by_risk_level', {}).get('critical', 0)}
- High: {summary.get('by_risk_level', {}).get('high', 0)}
- Medium: {summary.get('by_risk_level', {}).get('medium', 0)}
- Low: {summary.get('by_risk_level', {}).get('low', 0)}
"""
    
    # Add specific issue context if provided
    if request.context and request.context.get("issue_id"):
        issue = store.get_by_id(request.context["issue_id"])
        if issue:
            context_str += f"""
Current Issue Context:
- Title: {issue.get('title')}
- Type: {issue.get('type')}
- Risk: {issue.get('risk_level')}
- Location: {issue.get('location')}
- Description: {issue.get('description')}
- Solution: {issue.get('solution')}
"""
    
    # Add sample of critical issues (all_issues is list of dicts)
    critical_issues = [i for i in all_issues if i.get("risk_level") == "critical"][:5]
    if critical_issues:
        context_str += "\nCritical Issues:\n"
        for issue in critical_issues:
            context_str += f"- {issue.get('title')} at {issue.get('location')}\n"
    
    # Try to use LLM for response
    try:
        from config import get_settings, get_llm
        from langchain_core.prompts import ChatPromptTemplate
        
        settings = get_settings()
        
        if settings.use_llm_analysis:
            llm = get_llm()
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a helpful code analysis assistant. You help developers understand
and fix code issues found during automated analysis.

You have access to the following context about the codebase:
{context}

Be helpful, concise, and provide actionable advice. If asked about specific issues,
reference them by title and location. If asked for recommendations, prioritize
critical and high-risk issues first."""),
                ("human", "{message}")
            ])
            
            messages = prompt.format_messages(
                context=context_str,
                message=request.message
            )
            
            response = llm.invoke(messages)
            
            # Find referenced issues
            issues_referenced = []
            for issue in all_issues[:20]:  # Check first 20 issues
                if issue.title.lower() in response.content.lower():
                    issues_referenced.append(issue.id)
            
            return ChatResponse(
                response=response.content,
                issues_referenced=issues_referenced if issues_referenced else None,
                suggestions=None
            )
    
    except Exception as e:
        # Fall back to simple response
        pass
    
    # Simple fallback response without LLM
    fallback_response = _generate_fallback_response(
        message=request.message,
        summary=summary,
        all_issues=all_issues
    )
    
    return ChatResponse(
        response=fallback_response,
        issues_referenced=None,
        suggestions=["Enable LLM for more detailed responses"]
    )


def _generate_fallback_response(
    message: str,
    summary: dict,
    all_issues: list
) -> str:
    """Generate a simple response without LLM."""
    message_lower = message.lower()
    
    # Common question patterns
    if "critical" in message_lower or "most important" in message_lower:
        critical = [i for i in all_issues if i.get("risk_level") == "critical"]
        if critical:
            response = f"There are {len(critical)} critical issues that need immediate attention:\n\n"
            for idx, issue in enumerate(critical[:5], 1):
                response += f"{idx}. **{issue.get('title')}** at `{issue.get('location')}`\n"
            return response
        return "No critical issues found in the codebase."
    
    if "security" in message_lower:
        security = [i for i in all_issues if i.get("type") == "security"]
        if security:
            return f"Found {len(security)} security issues. The most critical ones should be addressed first to prevent vulnerabilities."
        return "No security issues found."
    
    if "performance" in message_lower:
        perf = [i for i in all_issues if i.get("type") == "performance"]
        if perf:
            return f"Found {len(perf)} performance issues. Review these to improve application speed and efficiency."
        return "No performance issues found."
    
    if "summary" in message_lower or "overview" in message_lower:
        total = summary.get("total", 0)
        by_type = summary.get("by_type", {})
        by_risk = summary.get("by_risk_level", {})
        
        return f"""Code Analysis Summary:
        
Total Issues: {total}
- Security: {by_type.get('security', 0)}
- Performance: {by_type.get('performance', 0)}
- Architecture: {by_type.get('architecture', 0)}

By Priority:
- Critical: {by_risk.get('critical', 0)}
- High: {by_risk.get('high', 0)}
- Medium: {by_risk.get('medium', 0)}
- Low: {by_risk.get('low', 0)}"""
    
    # Default response
    return f"""I found {summary.get('total', 0)} issues in your codebase.

Ask me about:
- "What are the critical issues?"
- "Tell me about security issues"
- "What performance problems were found?"
- "Give me an overview"

For more detailed responses, enable LLM integration."""


# =============================================================================
# Startup/Shutdown Events
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup."""
    # Ensure issues directory exists
    os.makedirs(ISSUES_DIR, exist_ok=True)
    print(f"🚀 Code Analysis API started")
    print(f"📁 Issues directory: {ISSUES_DIR}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    executor.shutdown(wait=False)
    print("👋 Code Analysis API shutting down")
