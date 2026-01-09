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
import json
import os
import subprocess
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from models.issue import Issue, IssueStore, IssueType, RiskLevel
from agents.graph import run_analysis
from config import get_settings, setup_langsmith


# =============================================================================
# Configuration
# =============================================================================

# Issues directory is at the project root, not in backend/
# When running from backend/, we need to go up one level
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_BACKEND_DIR)
ISSUES_DIR = os.getenv("ISSUES_DIR", os.path.join(_PROJECT_ROOT, "issues"))
REPORTS_DIR = os.getenv("REPORTS_DIR", os.path.join(_PROJECT_ROOT, "reports"))

# Thread pool for running sync analysis in background
executor = ThreadPoolExecutor(max_workers=2)

# In-memory storage for analysis tasks (would use Redis/DB in production)
analysis_tasks: dict[str, dict[str, Any]] = {}

# Chat session storage (in-memory with JSON persistence)
chat_sessions: dict[str, dict[str, Any]] = {}
SESSION_TIMEOUT = 1800  # 30 minutes in seconds
CHAT_LOGS_DIR = os.path.join(_PROJECT_ROOT, "chat_logs")
MAX_HISTORY_MESSAGES = 20  # Keep last 20 messages


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
    model: Optional[str] = Field(
        default=None,
        description="Ollama model to use for analysis (uses default if not specified)"
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
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for conversation continuity. Auto-generated if not provided."
    )
    context: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional context (e.g., current issue being viewed)"
    )
    model: Optional[str] = Field(
        default=None,
        description="Ollama model to use for chat (uses default if not specified). Deprecated: use 'models' instead."
    )
    models: Optional[list[str]] = Field(
        default=None,
        description="List of Ollama models to use for chat. If not specified, uses 'model' or default."
    )


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    session_id: str = Field(..., description="Session ID for this conversation")
    # For backward compatibility with single model
    response: Optional[str] = None
    issues_referenced: Optional[list[str]] = None
    suggestions: Optional[list[str]] = None
    # For multiple models
    responses: Optional[dict[str, dict[str, Any]]] = None


class ReportRequest(BaseModel):
    """Request model for report generation."""
    prompt: str = Field(..., description="Prompt for generating the report")
    model: Optional[str] = Field(
        default=None,
        description="Ollama model to use for report generation (uses default if not specified)"
    )


class ReportFile(BaseModel):
    """Model for a generated report file."""
    url: str = Field(..., description="URL to download the file")
    filename: str = Field(..., description="Name of the file")
    format: str = Field(..., description="File format (pdf, doc, md)")
    size: Optional[int] = Field(default=None, description="File size in bytes")


class ReportResponse(BaseModel):
    """Response model for report generation."""
    files: list[ReportFile] = Field(..., description="List of generated report files")


class ImproveIssueRequest(BaseModel):
    """Request model for improving an issue."""
    model: str = Field(..., description="Model name to use for improvement")


class UpdateIssueRequest(BaseModel):
    """Request model for updating an issue."""
    title: Optional[str] = Field(None, description="Updated title")
    description: Optional[str] = Field(None, description="Updated description")
    solution: Optional[str] = Field(None, description="Updated solution")
    code_snippet: Optional[str] = Field(None, description="Updated code snippet")
    risk_level: Optional[str] = Field(None, description="Updated risk level")
    type: Optional[str] = Field(None, description="Updated issue type")
    author: Optional[str] = Field(None, description="Updated author")


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

# Note: Static files for reports will be mounted after routes are defined
# to avoid conflicts with /reports/generate endpoint


# =============================================================================
# Helper Functions
# =============================================================================

def save_session_to_json(session_id: str) -> None:
    """Save chat session to JSON file for manual review."""
    if session_id not in chat_sessions:
        return
    
    session = chat_sessions[session_id]
    os.makedirs(CHAT_LOGS_DIR, exist_ok=True)
    
    file_path = os.path.join(CHAT_LOGS_DIR, f"session_{session_id}.json")
    
    # Build JSON structure
    session_data = {
        "session_id": session_id,
        "created_at": session.get("created_at", ""),
        "last_access": session.get("last_access", ""),
        "messages": session.get("messages", []),
        "metadata": {
            "total_messages": len(session.get("messages", [])),
            "models_used": list(set(session.get("models_used", []))),
            "issues_discussed": list(set(session.get("issues_discussed", [])))
        }
    }
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(session_data, f, indent=2, ensure_ascii=False)


def cleanup_old_sessions() -> int:
    """Remove sessions older than SESSION_TIMEOUT. Returns count of removed sessions."""
    now = datetime.now()
    to_remove = []
    
    for session_id, session in chat_sessions.items():
        last_access = session.get("last_access")
        if isinstance(last_access, str):
            last_access = datetime.fromisoformat(last_access)
        
        if (now - last_access).total_seconds() > SESSION_TIMEOUT:
            to_remove.append(session_id)
    
    for session_id in to_remove:
        del chat_sessions[session_id]
    
    return len(to_remove)


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
        
        # Save analysis metadata for RAG
        try:
            from models.rag_store import RAGStore
            from config import get_settings
            
            settings = get_settings()
            rag_store = RAGStore(directory=settings.rag_data_dir)
            rag_store.save_analysis_metadata(
                analyzed_path=path,
                files=processed,
                target_path=result.get("target_path", path)
            )
        except Exception as rag_error:
            # Don't fail the analysis if RAG storage fails
            print(f"Warning: Failed to save RAG metadata: {rag_error}")
        
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
            "models": "GET /models",
            "prompts": "GET /prompts",
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


@app.get("/models", tags=["Info"])
async def list_models():
    """
    List available Ollama models.
    
    Returns a list of model names that can be used for analysis.
    """
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return {"models": [], "error": "Failed to get models from Ollama"}
        
        # Parse the output: first line is header, rest are models
        lines = result.stdout.strip().split('\n')
        models = []
        
        for line in lines[1:]:  # Skip header line
            if line.strip():
                # Model name is the first column (before whitespace)
                model_name = line.split()[0]
                models.append(model_name)
        
        return {"models": models}
        
    except subprocess.TimeoutExpired:
        return {"models": [], "error": "Timeout getting models from Ollama"}
    except FileNotFoundError:
        return {"models": [], "error": "Ollama is not installed or not in PATH"}
    except Exception as e:
        return {"models": [], "error": str(e)}


@app.get("/prompts", tags=["Info"])
async def get_prompts():
    """
    Get the prompts configuration used for analysis.
    
    Returns roles and their associated system and human prompts.
    """
    try:
        from prompts.templates import get_all_roles
        
        roles = get_all_roles()
        
        # Format roles for response
        formatted_roles = []
        for role in roles:
            formatted_roles.append({
                "name": role.get("name", ""),
                "type": role.get("type", ""),
                "description": role.get("description", ""),
                "system_prompt": role.get("system_prompt", ""),
                "human_prompt_template": role.get("human_prompt_template", ""),
            })
        
        return {"roles": formatted_roles}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load prompts configuration: {str(e)}"
        )


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
    
    config = {
        "issues_dir": ISSUES_DIR,
        "model": request.model,  # Pass selected model to analysis
    }
    
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
        
        # Save analysis metadata for RAG
        try:
            from models.rag_store import RAGStore
            from config import get_settings
            
            settings = get_settings()
            rag_store = RAGStore(directory=settings.rag_data_dir)
            rag_store.save_analysis_metadata(
                analyzed_path=request.path,
                files=processed,
                target_path=result.get("target_path", request.path)
            )
        except Exception as rag_error:
            # Don't fail the analysis if RAG storage fails
            print(f"Warning: Failed to save RAG metadata: {rag_error}")
        
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


@app.delete("/issues", tags=["Issues"])
async def clear_all_issues():
    """
    Delete all issues and clear the issues folder.
    
    This removes all issue markdown files and clears the index.
    Use with caution as this action cannot be undone.
    """
    store = get_issue_store()
    count = store.clear()
    
    return {
        "status": "cleared",
        "deleted_count": count,
        "message": f"Successfully deleted {count} issues"
    }


@app.post("/issues/{issue_id}/improve", response_model=IssueDetailResponse, tags=["Issues"])
async def improve_issue(issue_id: str, request: ImproveIssueRequest):
    """
    Improve an issue using a custom LLM model.
    
    Uses the specified model to enhance the issue's title, description, and solution
    while maintaining the same location, type, risk level, and code snippet.
    """
    store = get_issue_store()
    issue_dict = store.get_by_id(issue_id)
    
    if not issue_dict:
        raise HTTPException(
            status_code=404,
            detail=f"Issue not found: {issue_id}"
        )
    
    try:
        from langchain_core.prompts import ChatPromptTemplate
        from config import get_llm, get_settings
        import json
        import re
        
        settings = get_settings()
        
        if not settings.use_llm_analysis:
            raise HTTPException(
                status_code=400,
                detail="LLM analysis is not enabled. Set USE_LLM_ANALYSIS=true to use this feature."
            )
        
        llm = get_llm(model_override=request.model)
        
        # Build prompt for improving the issue
        system_prompt = """You are an expert code reviewer helping to improve issue descriptions.
Your task is to enhance the clarity, detail, and actionability of code issue reports while maintaining technical accuracy.

IMPORTANT: You must return a valid JSON object with exactly these fields:
- title: Improved title (keep it concise, max 100 characters)
- description: Enhanced description with more detail and context
- solution: Improved solution with specific, actionable steps

Do NOT change the location, type, risk_level, or code_snippet. Only improve title, description, and solution.
Return ONLY valid JSON, no markdown code blocks, no additional text."""
        
        human_prompt = """Improve the following code issue report:

Original Issue:
- Title: {title}
- Type: {type}
- Risk Level: {risk_level}
- Location: {location}
- Description: {description}
- Code Snippet: {code_snippet}
- Solution: {solution}

Provide an improved version with:
1. A clearer, more descriptive title
2. A more detailed description that explains the issue better
3. A more actionable solution with specific steps

Return your response as a JSON object with fields: title, description, solution"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt)
        ])
        
        messages = prompt.format_messages(
            title=issue_dict.get("title", ""),
            type=issue_dict.get("type", ""),
            risk_level=issue_dict.get("risk_level", ""),
            location=issue_dict.get("location", ""),
            description=issue_dict.get("description", ""),
            code_snippet=issue_dict.get("code_snippet", ""),
            solution=issue_dict.get("solution", "")
        )
        
        response = llm.invoke(messages)
        response_text = response.content.strip()
        
        # Try to extract JSON from response (handle various formats)
        improved_data = {}
        
        # First, try to find JSON in markdown code blocks
        json_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_block_match:
            response_text = json_block_match.group(1)
        
        # Try to find JSON object boundaries
        json_start = response_text.find('{')
        json_end = response_text.rfind('}')
        if json_start >= 0 and json_end > json_start:
            json_text = response_text[json_start:json_end + 1]
            
            # Try parsing the JSON
            try:
                improved_data = json.loads(json_text)
            except json.JSONDecodeError:
                # Fallback: try to extract fields manually with better regex
                # Handle multiline strings and escaped quotes
                title_match = re.search(r'"title"\s*:\s*"((?:[^"\\]|\\.)*)"', json_text, re.DOTALL)
                desc_match = re.search(r'"description"\s*:\s*"((?:[^"\\]|\\.)*)"', json_text, re.DOTALL)
                sol_match = re.search(r'"solution"\s*:\s*"((?:[^"\\]|\\.)*)"', json_text, re.DOTALL)
                
                if title_match:
                    improved_data["title"] = title_match.group(1).replace('\\"', '"').replace('\\n', '\n')
                if desc_match:
                    improved_data["description"] = desc_match.group(1).replace('\\"', '"').replace('\\n', '\n')
                if sol_match:
                    improved_data["solution"] = sol_match.group(1).replace('\\"', '"').replace('\\n', '\n')
        
        # Validate that we got at least some data
        if not improved_data or not any(key in improved_data for key in ["title", "description", "solution"]):
            raise HTTPException(
                status_code=500,
                detail="Failed to parse improved issue data from LLM response. The model may not have returned valid JSON."
            )
        
        # Create improved issue (keep same location, type, risk_level, code_snippet for same ID)
        improved_title = improved_data.get("title", issue_dict.get("title", ""))
        improved_description = improved_data.get("description", issue_dict.get("description", ""))
        improved_solution = improved_data.get("solution", issue_dict.get("solution", ""))
        
        # Create Issue object with improved fields
        improved_issue = Issue(
            location=issue_dict.get("location", ""),
            type=IssueType(issue_dict.get("type", "architecture")),
            risk_level=RiskLevel(issue_dict.get("risk_level", "low")),
            title=improved_title,
            description=improved_description,
            code_snippet=issue_dict.get("code_snippet", ""),
            solution=improved_solution,
            author=issue_dict.get("author"),
            related_issues=issue_dict.get("related_issues"),
        )
        
        # Get markdown for the improved issue
        markdown = improved_issue.to_markdown()
        
        return IssueDetailResponse(
            id=improved_issue.id,
            location=improved_issue.location,
            type=improved_issue.type.value,
            risk_level=improved_issue.risk_level.value,
            title=improved_issue.title,
            description=improved_issue.description,
            code_snippet=improved_issue.code_snippet,
            solution=improved_issue.solution,
            author=improved_issue.author,
            created_at=issue_dict.get("created_at"),  # Keep original created_at
            markdown_content=markdown,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to improve issue: {str(e)}"
        )


@app.put("/issues/{issue_id}", response_model=IssueDetailResponse, tags=["Issues"])
async def update_issue(issue_id: str, request: UpdateIssueRequest):
    """
    Update/overwrite an issue with new data.
    
    This endpoint allows updating issue fields. The issue will be overwritten
    in storage if it exists. Note that changing location, title, or code_snippet
    will result in a new issue ID.
    """
    store = get_issue_store()
    existing_issue = store.get_by_id(issue_id)
    
    if not existing_issue:
        raise HTTPException(
            status_code=404,
            detail=f"Issue not found: {issue_id}"
        )
    
    # Build updated issue data (use request values if provided, otherwise keep existing)
    updated_data = {
        "location": existing_issue.get("location", ""),
        "type": request.type if request.type else existing_issue.get("type", "architecture"),
        "risk_level": request.risk_level if request.risk_level else existing_issue.get("risk_level", "low"),
        "title": request.title if request.title else existing_issue.get("title", ""),
        "description": request.description if request.description else existing_issue.get("description", ""),
        "code_snippet": request.code_snippet if request.code_snippet else existing_issue.get("code_snippet", ""),
        "solution": request.solution if request.solution else existing_issue.get("solution", ""),
        "author": request.author if request.author else existing_issue.get("author"),
        "related_issues": existing_issue.get("related_issues"),
    }
    
    # Create Issue object
    updated_issue = Issue(
        location=updated_data["location"],
        type=IssueType(updated_data["type"]),
        risk_level=RiskLevel(updated_data["risk_level"]),
        title=updated_data["title"],
        description=updated_data["description"],
        code_snippet=updated_data["code_snippet"],
        solution=updated_data["solution"],
        author=updated_data["author"],
        related_issues=updated_data["related_issues"],
    )
    
    # Save the updated issue (this will overwrite if same ID, or create new if ID changed)
    store.save(updated_issue)
    
    # Get markdown
    markdown = store.get_markdown(updated_issue.id) or updated_issue.to_markdown()
    
    return IssueDetailResponse(
        id=updated_issue.id,
        location=updated_issue.location,
        type=updated_issue.type.value,
        risk_level=updated_issue.risk_level.value,
        title=updated_issue.title,
        description=updated_issue.description,
        code_snippet=updated_issue.code_snippet,
        solution=updated_issue.solution,
        author=updated_issue.author,
        created_at=existing_issue.get("created_at"),  # Keep original created_at
        markdown_content=markdown,
    )


# -----------------------------------------------------------------------------
# Chat Endpoint
# -----------------------------------------------------------------------------

async def _process_single_model_chat(
    message: str,
    context_str: str,
    model_name: Optional[str],
    all_issues: list,
    store: IssueStore,
    session_id: str,
    history_messages: list[tuple[str, str]]
) -> dict[str, Any]:
    """Process chat request for a single model and return response dict."""
    try:
        from langchain_core.prompts import ChatPromptTemplate
        from config import get_llm, get_settings
        
        settings = get_settings()
        
        if settings.use_llm_analysis:
            llm = get_llm(model_override=model_name)
            
            # Enhanced system prompt with RAG context and conversation support
            system_prompt = """You are a helpful code analysis assistant in an ongoing conversation.
You help developers understand and fix code issues found during automated analysis.

IMPORTANT: This is a multi-turn conversation. When users ask follow-up questions like 
"how do I fix this?", "tell me more", or "what about that issue?", refer back to the 
issue or topic you just discussed in previous messages. Maintain context across the conversation.

You have access to the following context about the codebase:
{context}

Be helpful, concise, and provide actionable advice. When referencing code, use the specific
file locations and code snippets provided. If asked about specific issues, reference them
by title and location. If asked for recommendations, prioritize critical and high-risk
issues first. Use the retrieved code context to provide detailed, accurate answers about
the codebase."""
            
            # Build messages with history
            messages = [
                ("system", system_prompt.format(context=context_str)),
                *history_messages,  # Include conversation history
                ("human", message)
            ]
            
            response = llm.invoke(messages)
            
            # Find referenced issues
            issues_referenced = []
            for issue in all_issues[:20]:  # Check first 20 issues
                issue_title = issue.get('title', '').lower() if isinstance(issue, dict) else issue.title.lower()
                if issue_title and issue_title in response.content.lower():
                    issue_id = issue.get('id') if isinstance(issue, dict) else issue.id
                    issues_referenced.append(issue_id)
            
            return {
                "response": response.content,
                "issues_referenced": issues_referenced if issues_referenced else None,
                "suggestions": None
            }
    
    except Exception as e:
        # Fall back to simple response
        print(f"Warning: LLM chat failed for model {model_name}: {e}")
        pass
    
    # Simple fallback response without LLM
    summary = store.summary()
    fallback_response = _generate_fallback_response(
        message=message,
        summary=summary,
        all_issues=all_issues
    )
    
    return {
        "response": fallback_response,
        "issues_referenced": None,
        "suggestions": ["Enable LLM for more detailed responses"]
    }


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_about_issues(request: ChatRequest):
    """
    Chat about code issues using the LLM.
    
    Send a question about the codebase or issues and get an AI-powered response.
    Context can include the current issue being viewed for more relevant answers.
    Uses RAG to retrieve relevant code context from the analyzed folder.
    
    Supports multiple models for comparison. Provide 'models' list to get responses from multiple models.
    """
    store = get_issue_store()
    
    # Get relevant context
    all_issues = store.get_all()
    summary = store.summary()
    
    # Initialize RAG components
    from models.rag_store import RAGStore
    from rag.retriever import CodeRetriever
    from config import get_settings
    
    settings = get_settings()
    rag_store = RAGStore(directory=settings.rag_data_dir)
    retriever = CodeRetriever(issue_store=store, rag_store=rag_store)
    
    # Build context string (shared across all models)
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
    
    # Add analyzed folder information if available
    folder_info = retriever.get_analyzed_folder_info()
    if folder_info:
        context_str += f"""
Analyzed Folder:
- Path: {folder_info.get('path', 'Unknown')}
- Total Files: {folder_info.get('total_files', 0)}
- Analyzed At: {folder_info.get('analyzed_at', 'Unknown')}
"""
    
    # Retrieve relevant code context using RAG
    retrieved_context = []
    try:
        retrieved_context = retriever.retrieve_relevant_context(
            query=request.message,
            max_results=5
        )
    except Exception as rag_error:
        # Don't fail if RAG retrieval fails
        print(f"Warning: RAG retrieval failed: {rag_error}")
    
    # Filter out any invalid contexts (missing code snippets)
    retrieved_context = [
        ctx for ctx in retrieved_context
        if ctx.get("code_snippet") and len(ctx.get("code_snippet", "").strip()) > 0
    ]
    
    # Add retrieved code snippets to context
    if retrieved_context:
        context_str += "\n\nRelevant Code Context from Analyzed Folder:\n"
        for idx, ctx in enumerate(retrieved_context, 1):
            code_snippet = ctx.get('code_snippet', '').strip()
            description = (ctx.get('description', '') or '')[:200]
            location = ctx.get('location', 'Unknown')
            title = ctx.get('title', 'N/A')
            issue_type = ctx.get('type', 'unknown')
            risk_level = ctx.get('risk_level', 'unknown')
            
            if code_snippet:  # Only add if we have actual code
                context_str += f"""
{idx}. Location: {location}
   Issue: {title} ({issue_type} - {risk_level})
   Code Snippet:
```python
{code_snippet}
```
"""
                if description:
                    context_str += f"   Description: {description}\n"
    
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
    
    # Session management: get or create session
    session_id = request.session_id or str(uuid.uuid4())[:12]
    now = datetime.now()
    
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            "messages": [],
            "created_at": now.isoformat(),
            "last_access": now.isoformat(),
            "models_used": [],
            "issues_discussed": []
        }
    
    session = chat_sessions[session_id]
    session["last_access"] = now.isoformat()
    
    # Cleanup old sessions periodically
    cleanup_old_sessions()
    
    # Determine which models to use
    models_to_use = []
    if request.models:
        models_to_use = request.models
    elif request.model:
        models_to_use = [request.model]
    else:
        models_to_use = [None]  # Use default model
    
    # Process all models with their separate conversation histories
    tasks = []
    for model_name in models_to_use:
        model_key = model_name if model_name else "default"
        
        # Get conversation history for this specific model (last MAX_HISTORY_MESSAGES)
        model_messages = [
            (msg["role"], msg["content"])
            for msg in session["messages"]
            if msg.get("model") == model_key
        ][-MAX_HISTORY_MESSAGES:]
        
        tasks.append(_process_single_model_chat(
            message=request.message,
            context_str=context_str,
            model_name=model_name,
            all_issues=all_issues,
            store=store,
            session_id=session_id,
            history_messages=model_messages
        ))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Save messages to session and collect issues discussed
    for model_name, result in zip(models_to_use, results):
        model_key = model_name if model_name else "default"
        
        # Track model usage
        if model_key not in session.get("models_used", []):
            session.setdefault("models_used", []).append(model_key)
        
        # Add user message (only once per model)
        session["messages"].append({
            "role": "human",
            "content": request.message,
            "timestamp": now.isoformat(),
            "model": model_key
        })
        
        # Add assistant response if successful
        if not isinstance(result, Exception):
            session["messages"].append({
                "role": "assistant",
                "content": result.get("response", ""),
                "timestamp": datetime.now().isoformat(),
                "model": model_key,
                "issues_referenced": result.get("issues_referenced", [])
            })
            
            # Track issues discussed
            if result.get("issues_referenced"):
                for issue_id in result["issues_referenced"]:
                    if issue_id not in session.get("issues_discussed", []):
                        session.setdefault("issues_discussed", []).append(issue_id)
    
    # Save session to JSON file
    save_session_to_json(session_id)
    
    # Build response
    if len(models_to_use) == 1:
        # Single model: return backward-compatible format
        result = results[0]
        if isinstance(result, Exception):
            # Error occurred, return fallback
            fallback_response = _generate_fallback_response(
                message=request.message,
                summary=summary,
                all_issues=all_issues
            )
            return ChatResponse(
                session_id=session_id,
                response=fallback_response,
                issues_referenced=None,
                suggestions=["Enable LLM for more detailed responses"]
            )
        
        return ChatResponse(
            session_id=session_id,
            response=result["response"],
            issues_referenced=result["issues_referenced"],
            suggestions=result["suggestions"]
        )
    else:
        # Multiple models: return responses dict
        responses_dict = {}
        for idx, (model_name, result) in enumerate(zip(models_to_use, results)):
            model_key = model_name if model_name else "default"
            
            if isinstance(result, Exception):
                # Error occurred for this model
                fallback_response = _generate_fallback_response(
                    message=request.message,
                    summary=summary,
                    all_issues=all_issues
                )
                responses_dict[model_key] = {
                    "response": f"Error: {str(result)}",
                    "issues_referenced": None,
                    "suggestions": ["Enable LLM for more detailed responses"]
                }
            else:
                responses_dict[model_key] = result
        
        return ChatResponse(session_id=session_id, responses=responses_dict)


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


# -----------------------------------------------------------------------------
# Chat Session Management Endpoints
# -----------------------------------------------------------------------------

@app.get("/chat/sessions", tags=["Chat"])
async def list_chat_sessions():
    """
    List all saved chat sessions.
    
    Returns a list of session summaries including session ID, timestamps,
    message count, and models used.
    """
    if not os.path.exists(CHAT_LOGS_DIR):
        return {"sessions": []}
    
    sessions = []
    for filename in os.listdir(CHAT_LOGS_DIR):
        if filename.startswith("session_") and filename.endswith(".json"):
            file_path = os.path.join(CHAT_LOGS_DIR, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    sessions.append({
                        "session_id": data.get("session_id"),
                        "created_at": data.get("created_at"),
                        "last_access": data.get("last_access"),
                        "message_count": data.get("metadata", {}).get("total_messages", 0),
                        "models_used": data.get("metadata", {}).get("models_used", [])
                    })
            except Exception as e:
                print(f"Error reading session file {filename}: {e}")
    
    # Sort by last_access descending
    sessions.sort(key=lambda x: x.get("last_access", ""), reverse=True)
    return {"sessions": sessions}


@app.get("/chat/sessions/{session_id}", tags=["Chat"])
async def get_chat_session(session_id: str):
    """
    Get full chat session log.
    
    Returns the complete conversation history for a specific session,
    including all messages, timestamps, and metadata.
    """
    file_path = os.path.join(CHAT_LOGS_DIR, f"session_{session_id}.json")
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail=f"Session not found: {session_id}"
        )
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read session: {str(e)}"
        )


@app.delete("/chat/sessions/{session_id}", tags=["Chat"])
async def delete_chat_session(session_id: str):
    """
    Delete a chat session.
    
    Removes the session from both memory and the JSON file storage.
    """
    file_path = os.path.join(CHAT_LOGS_DIR, f"session_{session_id}.json")
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail=f"Session not found: {session_id}"
        )
    
    try:
        os.remove(file_path)
        if session_id in chat_sessions:
            del chat_sessions[session_id]
        return {"status": "deleted", "session_id": session_id}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete session: {str(e)}"
        )


# -----------------------------------------------------------------------------
# Report Generation Endpoint
# -----------------------------------------------------------------------------

@app.post("/reports/generate", response_model=ReportResponse, tags=["Reports"])
async def generate_report(request: ReportRequest):
    """
    Generate a report from code analysis issues.
    
    The report can be generated in PDF, DOC, or MD formats based on keywords
    in the prompt (e.g., "generate pdf report" or "in pdf format").
    
    - **prompt**: Prompt describing what kind of report to generate
    - **model**: Optional model name to use for generation
    """
    from reports.generator import (
        detect_formats,
        generate_report_summary,
        generate_markdown,
        save_markdown,
        generate_pdf,
        generate_doc,
    )
    from models.rag_store import RAGStore
    from rag.retriever import CodeRetriever
    from config import get_settings
    
    store = get_issue_store()
    all_issues = store.get_all()
    summary_stats = store.summary()
    
    # Build context similar to chat endpoint
    context_str = f"""
Code Analysis Summary:
- Total Issues: {summary_stats.get('total', 0)}
- Security Issues: {summary_stats.get('by_type', {}).get('security', 0)}
- Performance Issues: {summary_stats.get('by_type', {}).get('performance', 0)}
- Architecture Issues: {summary_stats.get('by_type', {}).get('architecture', 0)}
- Critical: {summary_stats.get('by_risk_level', {}).get('critical', 0)}
- High: {summary_stats.get('by_risk_level', {}).get('high', 0)}
- Medium: {summary_stats.get('by_risk_level', {}).get('medium', 0)}
- Low: {summary_stats.get('by_risk_level', {}).get('low', 0)}
"""
    
    # Add analyzed folder information if available
    try:
        settings = get_settings()
        rag_store = RAGStore(directory=settings.rag_data_dir)
        retriever = CodeRetriever(issue_store=store, rag_store=rag_store)
        folder_info = retriever.get_analyzed_folder_info()
        if folder_info:
            context_str += f"""
Analyzed Folder:
- Path: {folder_info.get('path', 'Unknown')}
- Total Files: {folder_info.get('total_files', 0)}
- Analyzed At: {folder_info.get('analyzed_at', 'Unknown')}
"""
    except Exception:
        pass  # Don't fail if RAG is not available
    
    # Add sample of critical issues
    critical_issues = [i for i in all_issues if i.get("risk_level") == "critical"][:10]
    if critical_issues:
        context_str += "\nCritical Issues:\n"
        for issue in critical_issues:
            context_str += f"- {issue.get('title')} at {issue.get('location')}\n"
    
    # Generate summary using LLM
    try:
        summary = generate_report_summary(
            prompt=request.prompt,
            context=context_str,
            model=request.model
        )
        if not summary or not summary.strip():
            raise HTTPException(
                status_code=500,
                detail="LLM returned an empty summary"
            )
        print(f"Generated summary length: {len(summary)} characters")
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate report summary: {str(e)}"
        )
    
    # Detect formats from prompt
    formats = detect_formats(request.prompt)
    print(f"Detected formats from prompt: {formats}")
    print(f"Prompt snippet: {request.prompt[:200]}...")
    
    # If no formats detected, default to markdown
    if not formats:
        formats = ['md']
        print("No formats detected, defaulting to markdown")
    
    # Generate markdown content
    try:
        markdown_content = generate_markdown(summary, all_issues, summary_stats)
        if not markdown_content or not markdown_content.strip():
            raise HTTPException(
                status_code=500,
                detail="Generated markdown content is empty"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate markdown content: {str(e)}"
        )
    
    # Generate files for each detected format
    generated_files = []
    errors = []
    timestamp = datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
    
    # Ensure reports directory exists
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    for fmt in formats:
        print(f"Attempting to generate {fmt} format...")
        try:
            if fmt == 'md':
                filename = f"report-{timestamp}.md"
                file_path = Path(REPORTS_DIR) / filename
                print(f"  Saving markdown to {file_path}")
                save_markdown(markdown_content, file_path)
                file_size = file_path.stat().st_size
                print(f"  Successfully generated {fmt} file: {filename} ({file_size} bytes)")
                
            elif fmt == 'pdf':
                filename = f"report-{timestamp}.pdf"
                file_path = Path(REPORTS_DIR) / filename
                print(f"  Generating PDF to {file_path}")
                generate_pdf(markdown_content, file_path)
                file_size = file_path.stat().st_size
                print(f"  Successfully generated {fmt} file: {filename} ({file_size} bytes)")
                
            elif fmt == 'doc':
                filename = f"report-{timestamp}.docx"
                file_path = Path(REPORTS_DIR) / filename
                print(f"  Generating DOCX to {file_path}")
                generate_doc(markdown_content, file_path)
                file_size = file_path.stat().st_size
                print(f"  Successfully generated {fmt} file: {filename} ({file_size} bytes)")
                
            else:
                errors.append(f"Unknown format: {fmt}")
                print(f"  Skipping unknown format: {fmt}")
                continue  # Skip unknown formats
            
            # Create relative URL for download
            url = f"/reports/files/{filename}"
            
            generated_files.append(ReportFile(
                url=url,
                filename=filename,
                format=fmt,
                size=file_size
            ))
            
        except ImportError as e:
            error_msg = f"Missing dependency for {fmt} format: {str(e)}"
            print(f"ERROR: {error_msg}")
            errors.append(error_msg)
            # Continue to try other formats
            continue
        except Exception as e:
            error_msg = f"Failed to generate {fmt} format: {str(e)}"
            print(f"ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
            errors.append(error_msg)
            # Continue to try other formats even if one fails
            continue
    
    if not generated_files:
        error_detail = "Failed to generate any report files."
        if errors:
            error_detail += f" Errors: {'; '.join(errors)}"
        else:
            error_detail += " No formats were detected or generated."
        raise HTTPException(
            status_code=500,
            detail=error_detail
        )
    
    return ReportResponse(files=generated_files)


# Mount static files for reports (after route definition to avoid conflicts)
# This allows downloading generated report files
try:
    os.makedirs(REPORTS_DIR, exist_ok=True)
    app.mount("/reports/files", StaticFiles(directory=REPORTS_DIR), name="reports-files")
except Exception as e:
    print(f"Warning: Could not mount reports static files: {e}")


# =============================================================================
# Startup/Shutdown Events
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup."""
    # Ensure issues directory exists
    os.makedirs(ISSUES_DIR, exist_ok=True)
    # Ensure reports directory exists
    os.makedirs(REPORTS_DIR, exist_ok=True)
    # Ensure chat logs directory exists
    os.makedirs(CHAT_LOGS_DIR, exist_ok=True)
    
    # Log LangSmith status
    settings = get_settings()
    if settings.langchain_tracing_v2 and settings.langchain_api_key:
        print(f"📊 LangSmith tracing enabled: {settings.langchain_project}")
    else:
        print("⚠️  LangSmith tracing disabled (set LANGCHAIN_TRACING_V2=true and LANGCHAIN_API_KEY)")
    
    print(f"🚀 Code Analysis API started")
    print(f"📁 Issues directory: {ISSUES_DIR}")
    print(f"📁 Reports directory: {REPORTS_DIR}")
    print(f"📁 Chat logs directory: {CHAT_LOGS_DIR}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    executor.shutdown(wait=False)
    print("👋 Code Analysis API shutting down")
