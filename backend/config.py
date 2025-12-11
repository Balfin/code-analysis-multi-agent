"""
Configuration for the Code Analysis Multi-Agent System.

This module handles:
- Environment variable loading
- LLM provider configuration (Ollama/OpenAI)
- LangSmith tracing setup
- Application settings
"""

import os
from pathlib import Path
from typing import Optional, Literal
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # ==========================================================================
    # LLM Configuration
    # ==========================================================================
    
    # LLM Provider: "ollama" or "openai"
    llm_provider: Literal["ollama", "openai"] = Field(
        default="ollama",
        description="LLM provider to use"
    )
    
    # OpenAI settings
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key"
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model to use"
    )
    
    # Ollama settings
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama server URL"
    )
    ollama_model: str = Field(
        default="llama3.2",
        description="Ollama model to use"
    )
    
    # LLM parameters
    llm_temperature: float = Field(
        default=0.1,
        description="LLM temperature (lower = more deterministic)"
    )
    llm_max_tokens: int = Field(
        default=2000,
        description="Maximum tokens in LLM response"
    )
    llm_timeout: int = Field(
        default=120,
        description="LLM request timeout in seconds"
    )
    
    # ==========================================================================
    # LangSmith Configuration
    # ==========================================================================
    
    langchain_tracing_v2: bool = Field(
        default=False,
        description="Enable LangSmith tracing"
    )
    langchain_api_key: Optional[str] = Field(
        default=None,
        description="LangSmith API key"
    )
    langchain_project: str = Field(
        default="code-analyzer-capstone",
        description="LangSmith project name"
    )
    
    # ==========================================================================
    # Application Settings
    # ==========================================================================
    
    # Backend server
    backend_host: str = Field(default="0.0.0.0")
    backend_port: int = Field(default=8000)
    
    # Frontend URL (for CORS)
    frontend_url: str = Field(default="http://localhost:5173")
    
    # Issue storage
    issues_dir: str = Field(default="./issues")
    
    # RAG storage
    rag_data_dir: str = Field(
        default="./rag_data",
        description="Directory for storing RAG metadata"
    )
    
    # Analysis settings
    max_file_size: int = Field(
        default=1048576,  # 1MB
        description="Maximum file size to analyze in bytes"
    )
    ignore_patterns: str = Field(
        default="__pycache__,*.pyc,.git,node_modules,venv,.venv,dist,build",
        description="Comma-separated patterns to ignore"
    )
    
    # Feature flags
    use_llm_analysis: bool = Field(
        default=True,
        description="Use LLM for analysis (False = pattern-only)"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def setup_langsmith():
    """Configure LangSmith tracing if enabled."""
    settings = get_settings()
    
    if settings.langchain_tracing_v2 and settings.langchain_api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
        os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
        print(f"LangSmith tracing enabled for project: {settings.langchain_project}")
    else:
        os.environ["LANGCHAIN_TRACING_V2"] = "false"


def get_llm(model_override: Optional[str] = None):
    """
    Get the configured LLM instance.
    
    Args:
        model_override: Optional model name to use instead of the default.
                       Only applies to Ollama provider.
    
    Returns:
        LangChain LLM instance (ChatOllama or ChatOpenAI)
    """
    settings = get_settings()
    
    if settings.llm_provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured. Set OPENAI_API_KEY environment variable.")
        
        from langchain_openai import ChatOpenAI
        
        return ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            timeout=settings.llm_timeout,
            api_key=settings.openai_api_key,
        )
    
    else:  # ollama
        from langchain_ollama import ChatOllama
        
        # Use override model if provided, otherwise use default
        model_name = model_override if model_override else settings.ollama_model
        
        return ChatOllama(
            model=model_name,
            base_url=settings.ollama_base_url,
            temperature=settings.llm_temperature,
            num_predict=settings.llm_max_tokens,
        )


def get_llm_info() -> dict:
    """Get information about the configured LLM."""
    settings = get_settings()
    
    return {
        "provider": settings.llm_provider,
        "model": settings.openai_model if settings.llm_provider == "openai" else settings.ollama_model,
        "temperature": settings.llm_temperature,
        "max_tokens": settings.llm_max_tokens,
    }


# Initialize LangSmith on module load
setup_langsmith()

