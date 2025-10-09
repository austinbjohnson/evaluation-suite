"""
Model provider abstractions for different LLM APIs.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ModelResponse:
    """Standardized response from any model provider"""
    text: str
    model: str
    usage: Optional[Any] = None
    raw_response: Optional[Any] = None


class Provider(ABC):
    """Base class for model providers"""
    
    @abstractmethod
    def generate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        **kwargs
    ) -> ModelResponse:
        """Generate a response from the model"""
        pass
    
    @abstractmethod
    def list_models(self) -> list[str]:
        """List available models for this provider"""
        pass

