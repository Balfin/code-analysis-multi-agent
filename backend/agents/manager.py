"""
Manager Agent for the Code Analysis Multi-Agent System.

The Manager agent is responsible for:
- Initializing the analysis workflow
- Selecting files for analysis
- Delegating to specialist agents
- Tracking progress across files
- Deciding when to compile results
- Providing progress updates

This is the enhanced implementation with full orchestration logic.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

from tools.code_tools import _read_file_impl, _list_python_files_impl, _get_code_metrics_impl

logger = logging.getLogger(__name__)


def manager_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Manager agent node for the analysis graph.
    
    Responsibilities:
    1. On first call: Initialize file list if empty, discover files
    2. Pick next file to analyze
    3. Load file content and prepare context
    4. Track which files have been processed
    5. Decide when to move to compilation
    6. Provide progress updates
    
    Args:
        state: Current analysis state
        
    Returns:
        Updated state with next file to analyze or compilation flag
    """
    messages = []
    
    # Get current state values
    target_path = state.get("target_path", ".")
    files_to_analyze = list(state.get("files_to_analyze", []))
    current_file = state.get("current_file", "")
    processed_files = list(state.get("processed_files", []))
    current_file_analyzed_by = list(state.get("current_file_analyzed_by", []))
    scan_status = state.get("scan_status", "pending")
    config = state.get("config", {})
    
    # First invocation - initialize
    if scan_status == "pending":
        init_result = _initialize_analysis(target_path, files_to_analyze, config)
        
        if init_result.get("error"):
            return {
                "scan_status": "error",
                "error": init_result["error"],
                "messages": init_result["messages"]
            }
        
        files_to_analyze = init_result["files"]
        messages.extend(init_result["messages"])
        scan_status = "scanning"
        
        logger.info(f"Manager initialized analysis of {target_path} with {len(files_to_analyze)} files")
    
    # Check if current file analysis is complete (all 3 agents have processed it)
    if current_file and len(current_file_analyzed_by) >= 3:
        # Mark current file as processed
        if current_file not in processed_files:
            processed_files.append(current_file)
            
            # Calculate progress
            total_files = len(processed_files) + len(files_to_analyze)
            progress = (len(processed_files) / total_files * 100) if total_files > 0 else 100
            
            messages.append({
                "role": "manager",
                "content": f"✓ Completed analysis of {_get_filename(current_file)} ({progress:.0f}% complete)",
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "action": "file_complete",
                    "file": current_file,
                    "progress": progress,
                    "processed_count": len(processed_files)
                }
            })
        
        # Reset for next file
        current_file = ""
        current_file_analyzed_by = []
    
    # Check if all files have been processed
    remaining_files = [f for f in files_to_analyze if f not in processed_files]
    
    if not remaining_files and not current_file:
        # All done - move to compilation
        messages.append({
            "role": "manager",
            "content": f"📊 All {len(processed_files)} files analyzed. Compiling results...",
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "action": "complete",
                "total_files": len(processed_files),
                "files": processed_files
            }
        })
        
        logger.info(f"Manager completed analysis of {len(processed_files)} files, moving to compilation")
        
        return {
            "files_to_analyze": [],
            "current_file": "",
            "current_file_content": "",
            "processed_files": processed_files,
            "current_file_analyzed_by": [],
            "scan_status": "compiling",
            "messages": messages,
        }
    
    # Pick next file if we don't have one
    if not current_file and remaining_files:
        next_file = remaining_files[0]
        remaining_files = remaining_files[1:]
        
        # Read file content
        content = _read_file_impl(next_file)
        
        if content.startswith("[ERROR]"):
            # Skip this file
            messages.append({
                "role": "manager",
                "content": f"⚠️ Skipping {_get_filename(next_file)}: {content}",
                "timestamp": datetime.now().isoformat(),
                "metadata": {"action": "skip", "file": next_file, "reason": content}
            })
            
            processed_files.append(next_file)
            
            logger.warning(f"Manager skipping file {next_file}: {content}")
            
            return {
                "files_to_analyze": remaining_files,
                "current_file": "",
                "current_file_content": "",
                "processed_files": processed_files,
                "current_file_analyzed_by": [],
                "scan_status": "scanning",
                "messages": messages,
            }
        
        # Get file metrics for context
        metrics = _get_code_metrics_impl(content)
        
        # Calculate progress
        total_files = len(processed_files) + len(remaining_files) + 1
        progress = (len(processed_files) / total_files * 100) if total_files > 0 else 0
        
        messages.append({
            "role": "manager",
            "content": f"🔍 Analyzing {_get_filename(next_file)} ({metrics.get('lines_code', 0)} lines, {metrics.get('functions_count', 0)} functions)",
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "action": "analyze",
                "file": next_file,
                "size": len(content),
                "metrics": metrics,
                "progress": progress,
                "remaining": len(remaining_files)
            }
        })
        
        logger.info(f"Manager starting analysis of {next_file}")
        
        return {
            "files_to_analyze": remaining_files,
            "current_file": next_file,
            "current_file_content": content,
            "processed_files": processed_files,
            "current_file_analyzed_by": [],
            "scan_status": "scanning",
            "messages": messages,
        }
    
    # Return current state if nothing to change
    return {
        "files_to_analyze": remaining_files if remaining_files else files_to_analyze,
        "current_file": current_file,
        "processed_files": processed_files,
        "current_file_analyzed_by": current_file_analyzed_by,
        "scan_status": scan_status,
        "messages": messages if messages else [],
    }


def _initialize_analysis(
    target_path: str,
    files_to_analyze: List[str],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Initialize the analysis by discovering files and validating the target.
    
    Args:
        target_path: Path to analyze
        files_to_analyze: Pre-specified files (if any)
        config: Analysis configuration
        
    Returns:
        Dictionary with files, messages, and potential error
    """
    messages = []
    
    messages.append({
        "role": "manager",
        "content": f"🚀 Starting code analysis of `{target_path}`",
        "timestamp": datetime.now().isoformat(),
        "metadata": {"action": "init", "target": target_path}
    })
    
    # Auto-discover files if list is empty
    if not files_to_analyze:
        ignore_patterns = config.get("ignore_patterns", None)
        discovered_files = _list_python_files_impl(target_path, ignore_patterns)
        
        # Filter out errors
        files_to_analyze = [f for f in discovered_files if not f.startswith("[ERROR]")]
        
        if not files_to_analyze:
            error_msg = f"No Python files found in {target_path}"
            if discovered_files and discovered_files[0].startswith("[ERROR]"):
                error_msg = discovered_files[0]
            
            return {
                "files": [],
                "messages": [{
                    "role": "manager",
                    "content": f"❌ Error: {error_msg}",
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {"action": "error", "reason": error_msg}
                }],
                "error": error_msg
            }
        
        messages.append({
            "role": "manager",
            "content": f"📁 Discovered {len(files_to_analyze)} Python files to analyze",
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "action": "discover",
                "file_count": len(files_to_analyze),
                "files": files_to_analyze[:10]  # First 10 for context
            }
        })
    else:
        messages.append({
            "role": "manager",
            "content": f"📁 Analyzing {len(files_to_analyze)} specified files",
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "action": "specified",
                "file_count": len(files_to_analyze)
            }
        })
    
    return {
        "files": files_to_analyze,
        "messages": messages,
        "error": None
    }


def _get_filename(filepath: str) -> str:
    """Extract filename from path."""
    return filepath.split("/")[-1] if "/" in filepath else filepath
