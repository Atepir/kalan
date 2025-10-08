"""
LLM tool definitions for function calling.

This module defines tools that LLMs can use to interact with the system,
following the function calling / tool use pattern.
"""

from __future__ import annotations

from typing import Any


class LLMTools:
    """Tool definitions for LLM function calling."""

    @staticmethod
    def get_all_tools() -> list[dict[str, Any]]:
        """Get all available tool definitions."""
        return [
            LLMTools.search_papers(),
            LLMTools.read_paper(),
            LLMTools.query_knowledge(),
            LLMTools.run_experiment(),
            LLMTools.ask_mentor(),
            LLMTools.update_knowledge(),
            LLMTools.search_related_concepts(),
        ]

    @staticmethod
    def search_papers() -> dict[str, Any]:
        """Tool for searching research papers."""
        return {
            "name": "search_papers",
            "description": "Search for research papers using keywords or topics. Returns relevant papers from arXiv and other sources.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (keywords or natural language)",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of papers to return",
                        "default": 10,
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["relevance", "date", "citations"],
                        "description": "How to sort results",
                        "default": "relevance",
                    },
                },
                "required": ["query"],
            },
        }

    @staticmethod
    def read_paper() -> dict[str, Any]:
        """Tool for reading a specific paper."""
        return {
            "name": "read_paper",
            "description": "Read and analyze a specific research paper. Returns detailed content including abstract, methodology, results, and conclusions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "paper_id": {
                        "type": "string",
                        "description": "Paper identifier (arXiv ID, DOI, or internal ID)",
                    },
                    "sections": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific sections to read (e.g., ['abstract', 'methodology'])",
                    },
                },
                "required": ["paper_id"],
            },
        }

    @staticmethod
    def query_knowledge() -> dict[str, Any]:
        """Tool for querying the knowledge base."""
        return {
            "name": "query_knowledge",
            "description": "Query the knowledge base for information about concepts, topics, or relationships. Returns relevant knowledge entries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What to search for in the knowledge base",
                    },
                    "knowledge_type": {
                        "type": "string",
                        "enum": ["concepts", "methods", "facts", "relationships"],
                        "description": "Type of knowledge to search for",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        }

    @staticmethod
    def run_experiment() -> dict[str, Any]:
        """Tool for running experiments."""
        return {
            "name": "run_experiment",
            "description": "Execute code to run an experiment or analysis. Code runs in a sandboxed environment with access to common scientific libraries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute",
                    },
                    "description": {
                        "type": "string",
                        "description": "What this experiment is testing",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Maximum execution time in seconds",
                        "default": 300,
                    },
                },
                "required": ["code", "description"],
            },
        }

    @staticmethod
    def ask_mentor() -> dict[str, Any]:
        """Tool for asking a mentor for help."""
        return {
            "name": "ask_mentor",
            "description": "Ask your mentor for help understanding a concept or solving a problem. Mentors can provide explanations, examples, and guidance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The topic or concept you need help with",
                    },
                    "question": {
                        "type": "string",
                        "description": "Your specific question",
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context (what you've tried, what you understand so far)",
                    },
                },
                "required": ["topic", "question"],
            },
        }

    @staticmethod
    def update_knowledge() -> dict[str, Any]:
        """Tool for updating personal knowledge graph."""
        return {
            "name": "update_knowledge",
            "description": "Add or update knowledge in your personal knowledge graph. Use this when you learn something new.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Topic or concept name",
                    },
                    "depth_change": {
                        "type": "number",
                        "description": "How much to increase depth understanding (-1 to 1)",
                    },
                    "confidence_change": {
                        "type": "number",
                        "description": "How much to increase confidence (-1 to 1)",
                    },
                    "source": {
                        "type": "string",
                        "description": "Where this knowledge came from (paper ID, mentor, experiment)",
                    },
                    "notes": {
                        "type": "string",
                        "description": "Any notes or key insights",
                    },
                },
                "required": ["topic", "depth_change", "confidence_change", "source"],
            },
        }

    @staticmethod
    def search_related_concepts() -> dict[str, Any]:
        """Tool for finding related concepts."""
        return {
            "name": "search_related_concepts",
            "description": "Find concepts related to a given topic in the knowledge graph. Useful for exploring prerequisites or applications.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Topic to find related concepts for",
                    },
                    "relationship_type": {
                        "type": "string",
                        "enum": ["prerequisite", "related", "application", "subtopic"],
                        "description": "Type of relationship to search for",
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "How many relationship hops to traverse",
                        "default": 2,
                    },
                },
                "required": ["topic"],
            },
        }

    @staticmethod
    def get_learning_tools() -> list[dict[str, Any]]:
        """Get tools specifically for learning activities."""
        return [
            LLMTools.search_papers(),
            LLMTools.read_paper(),
            LLMTools.query_knowledge(),
            LLMTools.ask_mentor(),
            LLMTools.update_knowledge(),
            LLMTools.search_related_concepts(),
        ]

    @staticmethod
    def get_research_tools() -> list[dict[str, Any]]:
        """Get tools specifically for research activities."""
        return [
            LLMTools.search_papers(),
            LLMTools.read_paper(),
            LLMTools.query_knowledge(),
            LLMTools.run_experiment(),
            LLMTools.search_related_concepts(),
        ]

    @staticmethod
    def get_teaching_tools() -> list[dict[str, Any]]:
        """Get tools specifically for teaching activities."""
        return [
            LLMTools.query_knowledge(),
            LLMTools.search_related_concepts(),
            LLMTools.search_papers(),
        ]
