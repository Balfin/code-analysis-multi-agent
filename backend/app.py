"""
AI-Powered Code Analysis Multi-Agent System - FastAPI Backend

This is the main FastAPI application that exposes REST endpoints
for code analysis, issue management, and chat functionality.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI application
app = FastAPI(
    title="Code Analysis Multi-Agent System",
    description="AI-powered code analysis using multiple specialized agents",
    version="0.1.0",
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


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Code Analysis Multi-Agent System",
        "version": "0.1.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "analyze": "/analyze (POST) - Coming in Phase 7",
            "issues": "/issues (GET) - Coming in Phase 7",
            "chat": "/chat (POST) - Coming in Phase 7",
        },
    }


# Placeholder endpoints - will be fully implemented in Phase 7
@app.post("/analyze")
async def analyze_codebase(request: dict):
    """Start code analysis on a codebase. (Placeholder)"""
    return {
        "status": "placeholder",
        "message": "Analysis endpoint will be implemented in Phase 7",
        "path": request.get("path", "not provided"),
    }


@app.get("/issues")
async def get_issues():
    """Get all issues. (Placeholder)"""
    return {
        "issues": [],
        "total": 0,
        "message": "Issues endpoint will be implemented in Phase 7",
    }


@app.get("/issues/{issue_id}")
async def get_issue(issue_id: str):
    """Get a specific issue by ID. (Placeholder)"""
    return {
        "id": issue_id,
        "message": "Issue detail endpoint will be implemented in Phase 7",
    }


@app.post("/chat")
async def chat(request: dict):
    """Chat about code issues. (Placeholder)"""
    return {
        "response": "Chat endpoint will be implemented in Phase 7",
        "message": request.get("message", ""),
    }

