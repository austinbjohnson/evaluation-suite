"""
Anthropic provider implementation for Claude models.
"""

import os
from typing import Optional

from anthropic import Anthropic

from . import ModelResponse, Provider


class AnthropicProvider(Provider):
    """Anthropic API provider for Claude models"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key not provided. Set ANTHROPIC_API_KEY environment variable.")
        
        self.client = Anthropic(api_key=self.api_key)
    
    def generate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        **kwargs
    ) -> ModelResponse:
        """Generate a response from Claude model"""
        
        # Claude uses messages format
        messages = [{"role": "user", "content": prompt}]
        
        # Prepare arguments
        gen_kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        # Add any additional kwargs
        gen_kwargs.update(kwargs)
        
        # Call API
        response = self.client.messages.create(**gen_kwargs)
        
        # Extract text from content blocks
        text = ""
        if response.content:
            for block in response.content:
                if hasattr(block, 'text'):
                    text += block.text
        
        # Create usage object compatible with our tracking
        class Usage:
            def __init__(self, input_tokens, output_tokens):
                self.input_tokens = input_tokens
                self.output_tokens = output_tokens
                self.prompt_tokens = input_tokens
                self.completion_tokens = output_tokens
        
        usage = Usage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens
        )
        
        return ModelResponse(
            text=text,
            model=response.model,
            usage=usage,
            raw_response=response
        )
    
    def list_models(self) -> list[str]:
        """List available Anthropic models"""
        return [
            # Claude 4 family (verified)
            "claude-sonnet-4-20250514",
            "claude-opus-4-1-20250805",
            "claude-3-5-haiku-20241022",
            
            # Claude 3.5 family
            "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet-20240620",
            
            # Claude 3 family
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]

