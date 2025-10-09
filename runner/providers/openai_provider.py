"""
OpenAI provider implementation.
"""

import os
from typing import Optional

from openai import OpenAI

from . import ModelResponse, Provider


class OpenAIProvider(Provider):
    """OpenAI API provider"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def generate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        seed: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """Generate a response from OpenAI model"""
        
        # Build messages
        messages = [{"role": "user", "content": prompt}]
        
        # Prepare arguments
        gen_kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        # Add seed if provided and model supports it
        if seed is not None:
            gen_kwargs["seed"] = seed
        
        # Add any additional kwargs
        gen_kwargs.update(kwargs)
        
        # Call API
        response = self.client.chat.completions.create(**gen_kwargs)
        
        # Extract text
        text = response.choices[0].message.content or ""
        
        return ModelResponse(
            text=text,
            model=response.model,
            usage=response.usage,
            raw_response=response
        )
    
    def list_models(self) -> list[str]:
        """List available OpenAI models"""
        return [
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-3.5-turbo",
        ]

