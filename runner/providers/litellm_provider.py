"""
LiteLLM provider implementation - universal LLM router.
"""

import os
from typing import Optional

import litellm

from . import ModelResponse, Provider


class LiteLLMProvider(Provider):
    """LiteLLM provider - universal router for 100+ LLM models"""
    
    def __init__(self):
        """
        Initialize LiteLLM provider.
        
        LiteLLM reads API keys from environment variables based on the provider:
        - OPENAI_API_KEY for OpenAI
        - ANTHROPIC_API_KEY for Anthropic
        - COHERE_API_KEY for Cohere
        - HUGGINGFACE_API_KEY for Hugging Face
        - TOGETHER_API_KEY for Together AI
        - etc.
        
        See https://docs.litellm.ai/docs/providers for full list.
        """
        # LiteLLM automatically handles API keys from environment
        # Set verbose mode based on environment variable
        litellm.set_verbose = os.getenv("LITELLM_VERBOSE", "false").lower() == "true"
        
        # Optional: Set drop_params to handle model-specific parameters
        litellm.drop_params = True
    
    def generate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        seed: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """Generate a response using LiteLLM router"""
        
        # Build messages
        messages = [{"role": "user", "content": prompt}]
        
        # Prepare arguments
        gen_kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        # Add seed if provided (not all models support it)
        if seed is not None:
            gen_kwargs["seed"] = seed
        
        # Add any additional kwargs
        gen_kwargs.update(kwargs)
        
        try:
            # Call LiteLLM (which routes to appropriate provider)
            response = litellm.completion(**gen_kwargs)
            
            # Extract text
            text = ""
            if response.choices and len(response.choices) > 0:
                message = response.choices[0].message
                if hasattr(message, 'content') and message.content:
                    text = message.content
            
            # Create usage object compatible with our tracking
            class Usage:
                def __init__(self, prompt_tokens, completion_tokens):
                    self.input_tokens = prompt_tokens
                    self.output_tokens = completion_tokens
                    self.prompt_tokens = prompt_tokens
                    self.completion_tokens = completion_tokens
            
            # Extract usage info
            prompt_tokens = 0
            completion_tokens = 0
            if hasattr(response, 'usage') and response.usage:
                prompt_tokens = getattr(response.usage, 'prompt_tokens', 0)
                completion_tokens = getattr(response.usage, 'completion_tokens', 0)
            
            usage = Usage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)
            
            return ModelResponse(
                text=text,
                model=response.model if hasattr(response, 'model') else model,
                usage=usage,
                raw_response=response
            )
            
        except Exception as e:
            raise RuntimeError(f"LiteLLM error: {e}") from e
    
    def list_models(self) -> list[str]:
        """
        List example models supported by LiteLLM.
        
        Note: LiteLLM supports 100+ models. This is just a sample.
        See https://docs.litellm.ai/docs/providers for complete list.
        """
        return [
            # OpenAI
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            
            # Anthropic
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            
            # Google
            "gemini/gemini-2.0-flash-exp",
            "gemini/gemini-1.5-pro",
            
            # Cohere
            "command-r-plus",
            "command-r",
            
            # Together AI (OSS models)
            "together_ai/meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            "together_ai/mistralai/Mixtral-8x7B-Instruct-v0.1",
            "together_ai/Qwen/Qwen2.5-72B-Instruct-Turbo",
            "together_ai/deepseek-ai/deepseek-coder-33b-instruct",
            
            # Groq (fast inference)
            "groq/llama-3.1-70b-versatile",
            "groq/mixtral-8x7b-32768",
            
            # Replicate
            "replicate/meta/llama-2-70b-chat",
            
            # Hugging Face
            "huggingface/meta-llama/Llama-3-70b-chat-hf",
            "huggingface/mistralai/Mixtral-8x7B-Instruct-v0.1",
            
            # Perplexity
            "perplexity/llama-3.1-sonar-large-128k-online",
            
            # Anyscale
            "anyscale/meta-llama/Llama-3-70b-chat-hf",
            
            # DeepInfra
            "deepinfra/meta-llama/Meta-Llama-3-70B-Instruct",
            
            # OpenRouter (meta-provider)
            "openrouter/anthropic/claude-3-opus",
            "openrouter/meta-llama/llama-3-70b-instruct",
        ]

