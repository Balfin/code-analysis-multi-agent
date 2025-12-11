"""
Code Retriever for RAG (Retrieval-Augmented Generation).

This module provides code context retrieval based on user queries,
enabling the LLM to have knowledge about the analyzed codebase.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter


class CodeRetriever:
    """
    Retrieves relevant code context based on user queries.
    
    Uses simple keyword-based matching to find relevant code snippets
    from issues and optionally from actual files.
    """
    
    # Common stopwords to filter out
    STOPWORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were', 'be',
        'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'should', 'could', 'may', 'might', 'can', 'this', 'that', 'these',
        'those', 'what', 'which', 'who', 'where', 'when', 'why', 'how',
        'about', 'tell', 'me', 'show', 'explain', 'describe', 'give'
    }
    
    def __init__(self, issue_store, rag_store):
        """
        Initialize the CodeRetriever.
        
        Args:
            issue_store: IssueStore instance to access issues
            rag_store: RAGStore instance to access analyzed folder metadata
        """
        self.issue_store = issue_store
        self.rag_store = rag_store
    
    def retrieve_relevant_context(
        self,
        query: str,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant code context based on user query.
        
        Args:
            query: User's question or message
            max_results: Maximum number of code snippets to return
            
        Returns:
            List of dictionaries with code context, each containing:
            - code_snippet: The code snippet
            - location: File path and line number
            - title: Issue title (if from issue)
            - description: Issue description (if from issue)
            - score: Relevance score
        """
        # Extract keywords from query
        keywords = self._extract_keywords(query)
        
        if not keywords:
            return []
        
        # Get all issues
        try:
            all_issues = self.issue_store.get_all()
        except Exception:
            # If issue store fails, return empty results
            return []
        
        if not all_issues:
            return []
        
        # Score and rank issues
        scored_items = []
        for issue in all_issues:
            try:
                score = self._score_issue(issue, keywords)
                if score > 0:
                    # Ensure code_snippet is not None
                    code_snippet = issue.get("code_snippet") or ""
                    if code_snippet:  # Only include if there's actual code
                        scored_items.append({
                            "code_snippet": code_snippet,
                            "location": issue.get("location", ""),
                            "title": issue.get("title", ""),
                            "description": issue.get("description", ""),
                            "solution": issue.get("solution", ""),
                            "type": issue.get("type", ""),
                            "risk_level": issue.get("risk_level", ""),
                            "score": score
                        })
            except Exception:
                # Skip issues that cause errors
                continue
        
        # Sort by score (descending) and take top N
        scored_items.sort(key=lambda x: x["score"], reverse=True)
        results = scored_items[:max_results]
        
        # Truncate code snippets if too long
        for result in results:
            code = result["code_snippet"]
            if len(code) > 500:
                result["code_snippet"] = code[:497] + "..."
        
        return results
    
    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract relevant keywords from user query.
        
        Args:
            query: User's query string
            
        Returns:
            List of lowercase keywords (excluding stopwords)
        """
        # Convert to lowercase and split
        words = re.findall(r'\b\w+\b', query.lower())
        
        # Filter out stopwords and short words
        keywords = [
            w for w in words
            if w not in self.STOPWORDS and len(w) > 2
        ]
        
        return keywords
    
    def _score_issue(self, issue: Dict[str, Any], keywords: List[str]) -> float:
        """
        Score an issue based on keyword matches.
        
        Args:
            issue: Issue dictionary
            keywords: List of keywords to match
            
        Returns:
            Relevance score (higher = more relevant)
        """
        if not keywords:
            return 0.0
        
        # Combine all searchable text
        code_snippet = issue.get("code_snippet", "").lower()
        description = issue.get("description", "").lower()
        title = issue.get("title", "").lower()
        location = issue.get("location", "").lower()
        solution = issue.get("solution", "").lower()
        
        # Count keyword matches with weights
        code_matches = sum(1 for kw in keywords if kw in code_snippet)
        desc_matches = sum(1 for kw in keywords if kw in description)
        title_matches = sum(1 for kw in keywords if kw in title)
        location_matches = sum(1 for kw in keywords if kw in location)
        solution_matches = sum(1 for kw in keywords if kw in solution)
        
        # Weighted scoring (code snippets are most important)
        score = (
            code_matches * 3.0 +      # High weight for code
            title_matches * 2.0 +      # Medium-high for title
            desc_matches * 1.5 +       # Medium for description
            solution_matches * 1.0 +   # Lower for solution
            location_matches * 0.5      # Low for file path
        )
        
        # Normalize by number of keywords
        if keywords:
            score = score / len(keywords)
        
        return score
    
    def get_analyzed_folder_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the analyzed folder.
        
        Returns:
            Dictionary with folder info or None if not available
        """
        metadata = self.rag_store.get_metadata()
        if not metadata:
            return None
        
        analyzed_path = metadata.get("analyzed_path") or metadata.get("target_path")
        files = metadata.get("files", [])
        
        return {
            "path": analyzed_path,
            "total_files": len(files),
            "files": files[:10],  # First 10 files as sample
            "analyzed_at": metadata.get("analyzed_at")
        }
