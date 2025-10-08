"""LLM integration package."""

from src.llm.client import OllamaClient, get_ollama_client, ClaudeClient, get_claude_client
from src.llm.prompts import PromptTemplates
from src.llm.tools import LLMTools

__all__ = [
    "OllamaClient",
    "get_ollama_client",
    "ClaudeClient",  # Alias for backward compatibility
    "get_claude_client",  # Alias for backward compatibility
    "PromptTemplates",
    "LLMTools",
]
