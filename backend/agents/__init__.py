# Agents module
"""
Contains the multi-agent system components:
- Manager agent: orchestrates the analysis workflow
- Specialist agents: Security, Performance, Architecture experts
- Results compiler: aggregates findings into reports
- Graph: LangGraph workflow definition
"""

from agents.graph import (
    AnalysisState,
    create_analysis_graph,
    create_initial_state,
    run_analysis,
    get_graph_mermaid,
)
from agents.manager import manager_node
from agents.specialists import security_node, performance_node, architecture_node
from agents.compiler import compiler_node

__all__ = [
    # State
    "AnalysisState",
    # Graph
    "create_analysis_graph",
    "create_initial_state",
    "run_analysis",
    "get_graph_mermaid",
    # Agent nodes
    "manager_node",
    "security_node",
    "performance_node",
    "architecture_node",
    "compiler_node",
]
