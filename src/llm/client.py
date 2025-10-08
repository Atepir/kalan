"""
Ollama API client wrapper with retry logic and error handling.

Provides a consistent interface for interacting with local Ollama models.
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.utils.config import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class OllamaClient:
    """
    Async client for Ollama API with built-in retry logic and rate limiting.

    Features:
    - Automatic retry on transient failures
    - Request/response logging
    - Token usage tracking
    - Local model execution
    """

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize Ollama client.

        Args:
            base_url: Ollama API base URL (defaults to settings)
            model: Ollama model to use (defaults to settings)
        """
        settings = get_settings()
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.ollama_model
        self.max_tokens = settings.ollama_max_tokens

        self.client = httpx.AsyncClient(timeout=300.0)  # 5 minute timeout
        self.total_tokens_used = 0
        self.request_count = 0

        logger.info("ollama_client_initialized", model=self.model, base_url=self.base_url)

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(5),
    )
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        stop_sequences: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Generate a completion from Ollama.

        Args:
            prompt: User prompt/query
            system: System prompt to set context
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            stop_sequences: Sequences that stop generation
            metadata: Additional metadata for logging

        Returns:
            Dictionary with:
                - content: Generated text
                - usage: Token usage information (estimated)
                - model: Model used
                - stop_reason: Why generation stopped
        """
        try:
            self.request_count += 1
            request_id = f"req_{self.request_count}"

            logger.info(
                "ollama_request",
                request_id=request_id,
                prompt_length=len(prompt),
                system_length=len(system) if system else 0,
                **(metadata or {}),
            )

            # Build the full prompt with system message
            full_prompt = prompt
            if system:
                full_prompt = f"{system}\n\n{prompt}"

            # Prepare request payload for Ollama
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens or self.max_tokens,
                }
            }

            if stop_sequences:
                payload["options"]["stop"] = stop_sequences

            # Make API call to Ollama
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            result = response.json()

            # Extract response
            content = result.get("response", "")

            # Estimate token usage (Ollama provides eval_count and prompt_eval_count)
            input_tokens = result.get("prompt_eval_count", len(full_prompt.split()) * 1.3)
            output_tokens = result.get("eval_count", len(content.split()) * 1.3)
            total_tokens = int(input_tokens + output_tokens)
            self.total_tokens_used += total_tokens

            # Determine stop reason
            stop_reason = "stop" if result.get("done", False) else "length"

            logger.info(
                "ollama_response",
                request_id=request_id,
                input_tokens=int(input_tokens),
                output_tokens=int(output_tokens),
                total_tokens=total_tokens,
                stop_reason=stop_reason,
                content_length=len(content),
                done=result.get("done", False),
            )

            return {
                "content": content,
                "usage": {
                    "input_tokens": int(input_tokens),
                    "output_tokens": int(output_tokens),
                    "total_tokens": total_tokens,
                },
                "model": self.model,
                "stop_reason": stop_reason,
                "request_id": request_id,
            }

        except httpx.TimeoutException as e:
            logger.warning("ollama_timeout", error=str(e), request_id=request_id)
            raise
        except httpx.HTTPStatusError as e:
            logger.error("ollama_http_error", error=str(e), request_id=request_id, status_code=e.response.status_code)
            raise
        except Exception as e:
            logger.exception("ollama_unexpected_error", error=str(e), request_id=request_id)
            raise

    async def generate_with_tools(
        self,
        prompt: str,
        tools: list[dict[str, Any]],
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Generate with tool use capability using function calling.

        Note: Ollama's function calling support varies by model.
        This works best with models that support it (e.g., llama3.1, mistral).

        Args:
            prompt: User prompt
            tools: List of tool definitions
            system: System prompt
            max_tokens: Max tokens to generate

        Returns:
            Response dictionary including any tool calls
        """
        try:
            # Build the full prompt with system message and tools
            full_prompt = prompt
            if system:
                full_prompt = f"{system}\n\n{prompt}"

            # Add tool descriptions to prompt for models without native tool support
            tools_description = "\n\nAvailable tools:\n"
            for tool in tools:
                tools_description += f"- {tool['name']}: {tool.get('description', '')}\n"

            full_prompt += tools_description

            # Use chat API for better tool support
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system or "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": max_tokens or self.max_tokens,
                },
                "tools": tools,  # Some Ollama models support this
            }

            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            result = response.json()

            # Extract content and tool calls
            message = result.get("message", {})
            text_content = message.get("content", "")
            tool_calls = message.get("tool_calls", [])

            # Estimate token usage
            input_tokens = result.get("prompt_eval_count", 0)
            output_tokens = result.get("eval_count", 0)

            return {
                "content": text_content,
                "tool_calls": tool_calls,
                "usage": {
                    "input_tokens": int(input_tokens),
                    "output_tokens": int(output_tokens),
                },
                "stop_reason": "stop" if result.get("done", False) else "length",
            }

        except Exception as e:
            logger.exception("ollama_tools_error", error=str(e))
            raise

    async def batch_generate(
        self,
        prompts: list[str],
        system: Optional[str] = None,
        max_concurrent: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Generate completions for multiple prompts concurrently.

        Args:
            prompts: List of prompts to process
            system: System prompt (same for all)
            max_concurrent: Maximum concurrent requests

        Returns:
            List of response dictionaries
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _generate_with_semaphore(prompt: str) -> dict[str, Any]:
            async with semaphore:
                return await self.generate(prompt, system=system)

        tasks = [_generate_with_semaphore(prompt) for prompt in prompts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log them
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("batch_generate_error", prompt_index=i, error=str(result))
            else:
                valid_results.append(result)

        return valid_results

    def get_usage_stats(self) -> dict[str, Any]:
        """Get API usage statistics."""
        return {
            "total_requests": self.request_count,
            "total_tokens_used": self.total_tokens_used,
            "model": self.model,
        }

    async def list_models(self) -> list[dict[str, Any]]:
        """
        List available models from Ollama.

        Returns:
            List of available models with metadata
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            result = response.json()
            return result.get("models", [])
        except Exception as e:
            logger.error("ollama_list_models_error", error=str(e))
            return []

    async def pull_model(self, model_name: str) -> bool:
        """
        Pull a model from Ollama registry.

        Args:
            model_name: Name of the model to pull

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("ollama_pulling_model", model=model_name)
            response = await self.client.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name, "stream": False},
            )
            response.raise_for_status()
            logger.info("ollama_model_pulled", model=model_name)
            return True
        except Exception as e:
            logger.error("ollama_pull_model_error", model=model_name, error=str(e))
            return False

    async def close(self) -> None:
        """Close the client connection."""
        await self.client.aclose()
        logger.info("ollama_client_closed", usage=self.get_usage_stats())


# Global client instance
_ollama_client: Optional[OllamaClient] = None


def get_ollama_client() -> OllamaClient:
    """Get or create global Ollama client instance."""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client


# Alias for backward compatibility
get_claude_client = get_ollama_client
ClaudeClient = OllamaClient
