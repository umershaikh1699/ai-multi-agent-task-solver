"""LLM service wrapper for Groq API."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from groq import AsyncGroq
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential


class GroqLLMService:
    """Service for interacting with Groq LLM API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "llama-3.3-70b-versatile",
        timeout: float = 15.0,
    ) -> None:
        """Initialize Groq LLM service.
        
        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
            model: Model name to use
            timeout: Request timeout in seconds
        """
        self._api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self._api_key:
            raise ValueError("GROQ_API_KEY must be set in environment or passed to constructor")
        
        self._model = model
        self._timeout = timeout
        self._client = AsyncGroq(api_key=self._api_key, timeout=self._timeout)

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 512,
        json_mode: bool = False,
        retries: int = 3,
    ) -> str:
        """Generate completion from Groq API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            json_mode: Enable JSON response format
            retries: Number of retry attempts on failure
            
        Returns:
            Generated text content
            
        Raises:
            Exception: If API call fails after retries
        """
        response_format = {"type": "json_object"} if json_mode else None
        
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(retries),
            wait=wait_exponential(multiplier=0.5, min=1, max=10),
            reraise=True,
        ):
            with attempt:
                completion = await self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format,
                )
                
                content = completion.choices[0].message.content
                if not content:
                    raise ValueError("Empty response from Groq API")
                
                return content

    async def generate_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 512,
        retries: int = 3,
    ) -> Dict[str, Any]:
        """Generate JSON completion from Groq API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            retries: Number of retry attempts
            
        Returns:
            Parsed JSON response
            
        Raises:
            json.JSONDecodeError: If response is not valid JSON
            Exception: If API call fails after retries
        """
        content = await self.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
            retries=retries,
        )
        
        return json.loads(content)
