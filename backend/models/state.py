"""
Analysis State for the Code Analysis Multi-Agent System.

This module defines the AnalysisState TypedDict that represents
the shared state passed between agents in the LangGraph workflow.
"""

import operator
from typing import TypedDict, List, Annotated, Literal


class AnalysisState(TypedDict, total=False):
    """
    Shared state for the multi-agent code analysis workflow.
    
    This state is passed between agents and accumulates findings
    throughout the analysis process.
    
    Attributes:
        target_path: Path to the codebase being analyzed
        files_to_analyze: List of file paths to analyze
        current_file: Currently processing file path
        processed_files: List of already processed file paths
        issues: Accumulated list of detected issues (uses operator.add for merging)
        messages: Conversation history for agent communication
        scan_status: Current status of the analysis
        summary: Final summary report (populated by results compiler)
        error: Error message if analysis failed
        config: Analysis configuration options
    """
    
    # Core analysis tracking
    target_path: str
    files_to_analyze: List[str]
    current_file: str
    processed_files: List[str]
    
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


class FileAnalysisResult(TypedDict):
    """Result from analyzing a single file."""
    file_path: str
    issues: List[dict]
    status: Literal["success", "error", "skipped"]
    error_message: str


class AgentMessage(TypedDict):
    """Message structure for agent communication."""
    role: Literal["manager", "security", "performance", "architecture", "compiler", "system"]
    content: str
    timestamp: str
    metadata: dict


# Default initial state factory
def create_initial_state(
    target_path: str,
    files_to_analyze: List[str] = None,
    config: dict = None
) -> AnalysisState:
    """
    Create an initial AnalysisState for starting a new analysis.
    
    Args:
        target_path: Path to the codebase to analyze
        files_to_analyze: Optional list of specific files (defaults to empty)
        config: Optional configuration dictionary
        
    Returns:
        Initialized AnalysisState
    """
    return AnalysisState(
        target_path=target_path,
        files_to_analyze=files_to_analyze or [],
        current_file="",
        processed_files=[],
        issues=[],
        messages=[],
        scan_status="pending",
        summary="",
        error="",
        config=config or {},
    )

