"""
LiteLLM provider implementation - universal LLM router.
"""

import os
from typing import Optional

import litellm

from . import ModelResponse, Provider


class LiteLLMProvider(Provider):
    """LiteLLM provider - universal router for 100+ LLM models"""
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize LiteLLM provider.
        
        Args:
            base_url: Optional custom base URL for internal LiteLLM routers
            api_key: Optional API key for custom LiteLLM instances
        
        Environment variables:
        - LITELLM_BASE_URL: Custom base URL (e.g. for internal routers)
        - LITELLM_API_KEY: API key for custom LiteLLM instances
        - LITELLM_VERBOSE: Enable verbose logging (true/false)
        - LITELLM_METADATA_*: Custom metadata fields (product, feature, owner, environment, etc.)
        
        For public LiteLLM usage, API keys are read from provider-specific env vars:
        - OPENAI_API_KEY, ANTHROPIC_API_KEY, COHERE_API_KEY, etc.
        
        See https://docs.litellm.ai/docs/providers for full list.
        """
        # Custom base URL for internal routers
        self.base_url = base_url or os.getenv("LITELLM_BASE_URL")
        self.api_key = api_key or os.getenv("LITELLM_API_KEY")
        
        # Set verbose mode based on environment variable
        litellm.set_verbose = os.getenv("LITELLM_VERBOSE", "false").lower() == "true"
        
        # Optional: Set drop_params to handle model-specific parameters
        litellm.drop_params = True
        
        # Load custom metadata from environment variables
        self.custom_metadata = self._load_metadata_from_env()
    
    def _load_metadata_from_env(self) -> dict:
        """
        Load custom metadata from environment variables.
        
        Supports the following env vars:
        - LITELLM_METADATA_PRODUCT
        - LITELLM_METADATA_FEATURE
        - LITELLM_METADATA_OWNER
        - LITELLM_METADATA_ENVIRONMENT (development/staging/production)
        - LITELLM_METADATA_REFERRERS
        - LITELLM_METADATA_CUSTOMUSER_ID
        - LITELLM_METADATA_ACCOUNT_ID
        - LITELLM_METADATA_ZAP_ID
        """
        metadata = {}
        
        # Map env var names to metadata field names
        field_mappings = {
            "LITELLM_METADATA_PRODUCT": "product",
            "LITELLM_METADATA_FEATURE": "feature",
            "LITELLM_METADATA_OWNER": "owner",
            "LITELLM_METADATA_ENVIRONMENT": "environment",
            "LITELLM_METADATA_REFERRERS": "referrers",
            "LITELLM_METADATA_CUSTOMUSER_ID": "customuser_id",
            "LITELLM_METADATA_ACCOUNT_ID": "account_id",
            "LITELLM_METADATA_ZAP_ID": "zap_id",
        }
        
        for env_var, field_name in field_mappings.items():
            value = os.getenv(env_var)
            if value:
                # Try to convert to int for ID fields
                if "id" in field_name.lower():
                    try:
                        value = int(value)
                    except ValueError:
                        pass
                metadata[field_name] = value
        
        return metadata
    
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
        
        # Add custom base URL if provided
        if self.base_url:
            gen_kwargs["api_base"] = self.base_url
        
        # Add custom API key if provided
        if self.api_key:
            gen_kwargs["api_key"] = self.api_key
        
        # Add custom metadata if available
        if self.custom_metadata:
            gen_kwargs["metadata"] = {
                "spend_logs_metadata": self.custom_metadata
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

