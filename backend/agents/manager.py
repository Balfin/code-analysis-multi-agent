"""
Manager Agent for the Code Analysis Multi-Agent System.

The Manager agent is responsible for:
- Initializing the analysis workflow
- Selecting files for analysis
- Delegating to specialist agents
- Tracking progress across files
- Deciding when to compile results

This is a stub implementation that will be enhanced in Phase 5/6.
"""

from datetime import datetime
from typing import Dict, Any

from tools.code_tools import _read_file_impl, _list_python_files_impl


def manager_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Manager agent node for the analysis graph.
    
    Responsibilities:
    1. On first call: Initialize file list if empty
    2. Pick next file to analyze
    3. Load file content
    4. Track which files have been processed
    5. Decide when to move to compilation
    
    Args:
        state: Current analysis state
        
    Returns:
        Updated state with next file to analyze or compilation flag
    """
    messages = []
    
    # Get current state values
    target_path = state.get("target_path", ".")
    files_to_analyze = state.get("files_to_analyze", [])
    current_file = state.get("current_file", "")
    processed_files = list(state.get("processed_files", []))
    current_file_analyzed_by = state.get("current_file_analyzed_by", [])
    scan_status = state.get("scan_status", "pending")
    
    # First invocation - initialize
    if scan_status == "pending":
        messages.append({
            "role": "manager",
            "content": f"Starting analysis of {target_path}",
            "timestamp": datetime.now().isoformat(),
            "metadata": {"action": "init"}
        })
        
        # Auto-discover files if list is empty
        if not files_to_analyze:
            discovered_files = _list_python_files_impl(target_path)
            # Filter out errors
            files_to_analyze = [f for f in discovered_files if not f.startswith("[ERROR]")]
            
            if not files_to_analyze:
                return {
                    "scan_status": "error",
                    "error": f"No Python files found in {target_path}",
                    "messages": [{
                        "role": "manager",
                        "content": f"Error: No Python files found in {target_path}",
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {"action": "error"}
                    }]
                }
            
            messages.append({
                "role": "manager",
                "content": f"Discovered {len(files_to_analyze)} Python files",
                "timestamp": datetime.now().isoformat(),
                "metadata": {"action": "discover", "file_count": len(files_to_analyze)}
            })
        
        scan_status = "scanning"
    
    # Check if current file analysis is complete (all agents have processed it)
    if current_file and len(current_file_analyzed_by) >= 3:
        # Mark current file as processed
        if current_file not in processed_files:
            processed_files.append(current_file)
        
        messages.append({
            "role": "manager",
            "content": f"Completed analysis of {current_file}",
            "timestamp": datetime.now().isoformat(),
            "metadata": {"action": "file_complete", "file": current_file}
        })
        
        # Reset for next file
        current_file = ""
        current_file_analyzed_by = []
    
    # Remove processed files from the list
    remaining_files = [f for f in files_to_analyze if f not in processed_files]
    
    # Check if all files have been processed
    if not remaining_files and not current_file:
        messages.append({
            "role": "manager",
            "content": f"All {len(processed_files)} files analyzed. Moving to compilation.",
            "timestamp": datetime.now().isoformat(),
            "metadata": {"action": "complete", "total_files": len(processed_files)}
        })
        
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
        current_file = remaining_files[0]
        remaining_files = remaining_files[1:]
        
        # Read file content
        content = _read_file_impl(current_file)
        
        if content.startswith("[ERROR]"):
            messages.append({
                "role": "manager",
                "content": f"Skipping {current_file}: {content}",
                "timestamp": datetime.now().isoformat(),
                "metadata": {"action": "skip", "file": current_file, "reason": content}
            })
            
            # Mark as processed (skipped) and continue
            processed_files.append(current_file)
            
            return {
                "files_to_analyze": remaining_files,
                "current_file": "",
                "current_file_content": "",
                "processed_files": processed_files,
                "current_file_analyzed_by": [],
                "scan_status": "scanning",
                "messages": messages,
            }
        
        messages.append({
            "role": "manager",
            "content": f"Analyzing file: {current_file} ({len(content)} chars)",
            "timestamp": datetime.now().isoformat(),
            "metadata": {"action": "analyze", "file": current_file, "size": len(content)}
        })
        
        return {
            "files_to_analyze": remaining_files,
            "current_file": current_file,
            "current_file_content": content,
            "processed_files": processed_files,
            "current_file_analyzed_by": [],
            "scan_status": "scanning",
            "messages": messages,
        }
    
    # Return current state if nothing to change
    return {
        "files_to_analyze": remaining_files,
        "current_file": current_file,
        "processed_files": processed_files,
        "current_file_analyzed_by": current_file_analyzed_by,
        "scan_status": scan_status,
        "messages": messages if messages else [],
    }

