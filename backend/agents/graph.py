"""
LangGraph Multi-Agent Orchestration for Code Analysis.

This module defines the workflow graph that coordinates:
- Manager agent: orchestrates file processing and delegates to specialists
- Security agent: analyzes code for security vulnerabilities
- Performance agent: analyzes code for performance issues
- Architecture agent: analyzes code for design/architecture issues
- Results compiler: aggregates findings into a summary report

The graph uses LangGraph's StateGraph to manage state transitions
and conditional routing between agents.
"""

import operator
from typing import TypedDict, List, Annotated, Literal, Dict, Any

from langgraph.graph import StateGraph, END

from agents.manager import manager_node
from agents.specialists import security_node, performance_node, architecture_node
from agents.compiler import compiler_node


# =============================================================================
# State Definition
# =============================================================================

class AnalysisState(TypedDict, total=False):
    """
    Shared state for the multi-agent code analysis workflow.
    
    This state is passed between agents and accumulates findings
    throughout the analysis process.
    """
    # Core analysis tracking
    target_path: str
    files_to_analyze: List[str]
    current_file: str
    current_file_content: str
    processed_files: List[str]
    
    # Analysis tracking per file
    current_file_analyzed_by: List[str]  # Which agents have analyzed current file
    
    # Issue accumulation - uses operator.add to merge lists from different agents
    issues: Annotated[List[dict], operator.add]
    
    # Agent communication
    messages: Annotated[List[dict], operator.add]
    
    # Status tracking
    scan_status: Literal["pending", "scanning", "compiling", "done", "error"]
    
    # Results
    summary: str
    error: str
    
    # Configuration
    config: dict


# =============================================================================
# Routing Functions
# =============================================================================

def route_after_manager(state: AnalysisState) -> str:
    """
    Route after manager node decides what to do next.
    
    Routes to:
    - "security": If there's a file to analyze and security hasn't analyzed it
    - "compile": If all files have been processed
    - END: If there's an error
    """
    if state.get("error"):
        return END
    
    if state.get("scan_status") == "compiling":
        return "compile"
    
    # Check if we have a current file to analyze
    if state.get("current_file") and state.get("current_file_content"):
        analyzed_by = state.get("current_file_analyzed_by", [])
        
        # Route to first agent that hasn't analyzed this file
        if "security" not in analyzed_by:
            return "security"
        elif "performance" not in analyzed_by:
            return "performance"
        elif "architecture" not in analyzed_by:
            return "architecture"
        else:
            # All agents have analyzed, go back to manager for next file
            return "manager"
    
    # No current file, check if there are more files
    if state.get("files_to_analyze"):
        return "manager"
    
    return "compile"


def route_after_security(state: AnalysisState) -> str:
    """Route after security agent completes analysis."""
    if state.get("error"):
        return END
    return "performance"


def route_after_performance(state: AnalysisState) -> str:
    """Route after performance agent completes analysis."""
    if state.get("error"):
        return END
    return "architecture"


def route_after_architecture(state: AnalysisState) -> str:
    """Route after architecture agent completes analysis."""
    if state.get("error"):
        return END
    # Go back to manager to check for more files
    return "manager"


def route_after_compiler(state: AnalysisState) -> str:
    """Route after compiler completes - always ends."""
    return END


# =============================================================================
# Graph Construction
# =============================================================================

def create_analysis_graph() -> StateGraph:
    """
    Create and compile the multi-agent analysis graph.
    
    The graph follows this workflow:
    1. Manager initializes and picks first file
    2. Security agent analyzes the file
    3. Performance agent analyzes the file
    4. Architecture agent analyzes the file
    5. Manager picks next file (repeat 2-4) or moves to compilation
    6. Compiler aggregates all issues into summary
    
    Returns:
        Compiled StateGraph ready for invocation
    """
    # Create the graph with our state type
    workflow = StateGraph(AnalysisState)
    
    # Add nodes
    workflow.add_node("manager", manager_node)
    workflow.add_node("security", security_node)
    workflow.add_node("performance", performance_node)
    workflow.add_node("architecture", architecture_node)
    workflow.add_node("compile", compiler_node)
    
    # Set entry point
    workflow.set_entry_point("manager")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "manager",
        route_after_manager,
        {
            "security": "security",
            "performance": "performance",
            "architecture": "architecture",
            "compile": "compile",
            "manager": "manager",
            END: END,
        }
    )
    
    workflow.add_conditional_edges(
        "security",
        route_after_security,
        {
            "performance": "performance",
            END: END,
        }
    )
    
    workflow.add_conditional_edges(
        "performance",
        route_after_performance,
        {
            "architecture": "architecture",
            END: END,
        }
    )
    
    workflow.add_conditional_edges(
        "architecture",
        route_after_architecture,
        {
            "manager": "manager",
            END: END,
        }
    )
    
    workflow.add_conditional_edges(
        "compile",
        route_after_compiler,
        {
            END: END,
        }
    )
    
    # Compile the graph
    return workflow.compile()


# =============================================================================
# Helper Functions
# =============================================================================

def create_initial_state(
    target_path: str,
    files_to_analyze: List[str] = None,
    config: Dict[str, Any] = None
) -> AnalysisState:
    """
    Create an initial AnalysisState for starting a new analysis.
    
    Args:
        target_path: Path to the codebase to analyze
        files_to_analyze: List of file paths to analyze
        config: Optional configuration dictionary
        
    Returns:
        Initialized AnalysisState
    """
    return {
        "target_path": target_path,
        "files_to_analyze": files_to_analyze or [],
        "current_file": "",
        "current_file_content": "",
        "processed_files": [],
        "current_file_analyzed_by": [],
        "issues": [],
        "messages": [],
        "scan_status": "pending",
        "summary": "",
        "error": "",
        "config": config or {},
    }


def run_analysis(
    target_path: str,
    files: List[str] = None,
    config: Dict[str, Any] = None
) -> AnalysisState:
    """
    Convenience function to run a complete analysis.
    
    Args:
        target_path: Path to the codebase
        files: List of files to analyze (auto-discovers if None)
        config: Optional configuration
        
    Returns:
        Final state with all issues and summary
    """
    from tools.code_tools import _list_python_files_impl
    
    # Auto-discover files if not provided
    if files is None:
        files = _list_python_files_impl(target_path)
        # Filter out any error messages
        files = [f for f in files if not f.startswith("[ERROR]")]
    
    # Create graph and initial state
    graph = create_analysis_graph()
    initial_state = create_initial_state(target_path, files, config)
    
    # Calculate recursion limit based on file count
    # Each file needs ~5 iterations (manager + 3 specialists + manager again)
    # Plus some buffer for initialization and compilation
    recursion_limit = max(50, len(files) * 6 + 10)
    
    # Run the analysis with appropriate recursion limit
    result = graph.invoke(
        initial_state,
        config={"recursion_limit": recursion_limit}
    )
    
    return result


# =============================================================================
# Graph Visualization (Mermaid)
# =============================================================================

def get_graph_mermaid() -> str:
    """
    Generate a Mermaid diagram of the analysis graph.
    
    Returns:
        Mermaid diagram string
    """
    return """
```mermaid
graph TD
    START((Start)) --> Manager
    
    Manager -->|has file| Security
    Manager -->|all done| Compile
    Manager -->|error| END((End))
    
    Security --> Performance
    Performance --> Architecture
    Architecture -->|more files| Manager
    Architecture -->|no more files| Manager
    
    Manager -->|compiling| Compile
    Compile --> END
    
    subgraph "Specialist Analysis"
        Security[🔒 Security Agent]
        Performance[⚡ Performance Agent]
        Architecture[🏗️ Architecture Agent]
    end
    
    subgraph "Orchestration"
        Manager[📋 Manager Agent]
        Compile[📊 Results Compiler]
    end
```
"""

