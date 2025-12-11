"""
RAG Store for the Code Analysis Multi-Agent System.

This module manages storage of analyzed folder metadata for RAG (Retrieval-Augmented Generation).
It stores information about the last analyzed folder to enable context-aware chat responses.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


class RAGStore:
    """
    Manages storage of analyzed folder metadata for RAG context.
    
    Stores metadata about the last analyzed folder including:
    - Analyzed folder path
    - List of analyzed files
    - Analysis timestamp
    - File structure summary
    """
    
    def __init__(self, directory: str = "./rag_data"):
        """
        Initialize the RAGStore.
        
        Args:
            directory: Path to the base directory for storing RAG metadata
        """
        self.directory = Path(directory)
        self._ensure_directory()
        self._metadata_file = self.directory / "analysis_metadata.json"
    
    def _ensure_directory(self) -> None:
        """Create the base RAG directory if it doesn't exist."""
        self.directory.mkdir(parents=True, exist_ok=True)
    
    def save_analysis_metadata(
        self,
        analyzed_path: str,
        files: List[str],
        target_path: Optional[str] = None
    ) -> None:
        """
        Save metadata about an analyzed folder.
        
        Args:
            analyzed_path: Path to the analyzed folder
            files: List of file paths that were analyzed
            target_path: Original target path (may differ from analyzed_path)
        """
        metadata = {
            "analyzed_path": analyzed_path,
            "target_path": target_path or analyzed_path,
            "analyzed_at": datetime.now().isoformat(),
            "files": files,
            "total_files": len(files)
        }
        
        with open(self._metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def get_last_analyzed_path(self) -> Optional[str]:
        """
        Get the path of the last analyzed folder.
        
        Returns:
            Path string if metadata exists, None otherwise
        """
        metadata = self._load_metadata()
        if metadata:
            return metadata.get("analyzed_path") or metadata.get("target_path")
        return None
    
    def get_analyzed_files(self) -> List[str]:
        """
        Get the list of files from the last analysis.
        
        Returns:
            List of file paths, empty list if no metadata exists
        """
        metadata = self._load_metadata()
        if metadata:
            return metadata.get("files", [])
        return []
    
    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """
        Get the complete metadata dictionary.
        
        Returns:
            Metadata dictionary if exists, None otherwise
        """
        return self._load_metadata()
    
    def _load_metadata(self) -> Optional[Dict[str, Any]]:
        """Load metadata from file."""
        if not self._metadata_file.exists():
            return None
        
        try:
            with open(self._metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    
    def clear(self) -> None:
        """Clear all stored metadata."""
        if self._metadata_file.exists():
            self._metadata_file.unlink()
