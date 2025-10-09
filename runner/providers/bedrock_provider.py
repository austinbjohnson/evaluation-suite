"""
AWS Bedrock provider implementation for hosted models.
"""

import json
import os
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from . import ModelResponse, Provider


class BedrockProvider(Provider):
    """AWS Bedrock provider for hosted models (Llama, Mistral, Claude, etc.)"""
    
    def __init__(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: Optional[str] = None
    ):
        self.aws_access_key_id = aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")
        
        if not self.aws_access_key_id or not self.aws_secret_access_key:
            raise ValueError(
                "AWS credentials not provided. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY "
                "environment variables."
            )
        
        self.client = boto3.client(
            "bedrock-runtime",
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name
        )
    
    def generate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        **kwargs
    ) -> ModelResponse:
        """Generate a response from Bedrock-hosted model"""
        
        # Build request body based on model family
        if "llama" in model.lower() or "meta" in model.lower():
            body = self._build_llama_request(prompt, temperature, max_tokens)
        elif "mistral" in model.lower():
            body = self._build_mistral_request(prompt, temperature, max_tokens)
        elif "claude" in model.lower():
            body = self._build_claude_request(prompt, temperature, max_tokens)
        elif "titan" in model.lower() or "amazon" in model.lower():
            body = self._build_titan_request(prompt, temperature, max_tokens)
        elif "cohere" in model.lower():
            body = self._build_cohere_request(prompt, temperature, max_tokens)
        else:
            # Generic fallback
            body = self._build_generic_request(prompt, temperature, max_tokens)
        
        try:
            # Call Bedrock
            response = self.client.invoke_model(
                modelId=model,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json"
            )
            
            # Parse response
            response_body = json.loads(response["body"].read())
            
            # Extract text and usage based on model family
            text, input_tokens, output_tokens = self._parse_response(model, response_body)
            
            # Create usage object compatible with our tracking
            class Usage:
                def __init__(self, input_tokens, output_tokens):
                    self.input_tokens = input_tokens
                    self.output_tokens = output_tokens
                    self.prompt_tokens = input_tokens
                    self.completion_tokens = output_tokens
            
            usage = Usage(input_tokens=input_tokens, output_tokens=output_tokens)
            
            return ModelResponse(
                text=text,
                model=model,
                usage=usage,
                raw_response=response_body
            )
            
        except ClientError as e:
            raise RuntimeError(f"Bedrock API error: {e}") from e
    
    def _build_llama_request(self, prompt: str, temperature: float, max_tokens: int) -> dict:
        """Build request for Llama models"""
        return {
            "prompt": prompt,
            "temperature": temperature,
            "max_gen_len": max_tokens,
            "top_p": 0.9
        }
    
    def _build_mistral_request(self, prompt: str, temperature: float, max_tokens: int) -> dict:
        """Build request for Mistral models"""
        return {
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 0.9
        }
    
    def _build_claude_request(self, prompt: str, temperature: float, max_tokens: int) -> dict:
        """Build request for Claude models on Bedrock"""
        return {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
    
    def _build_titan_request(self, prompt: str, temperature: float, max_tokens: int) -> dict:
        """Build request for Amazon Titan models"""
        return {
            "inputText": prompt,
            "textGenerationConfig": {
                "temperature": temperature,
                "maxTokenCount": max_tokens,
                "topP": 0.9
            }
        }
    
    def _build_cohere_request(self, prompt: str, temperature: float, max_tokens: int) -> dict:
        """Build request for Cohere models"""
        return {
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "p": 0.9
        }
    
    def _build_generic_request(self, prompt: str, temperature: float, max_tokens: int) -> dict:
        """Generic request format"""
        return {
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
    
    def _parse_response(self, model: str, response_body: dict) -> tuple[str, int, int]:
        """Parse response based on model family"""
        
        # Default values
        text = ""
        input_tokens = 0
        output_tokens = 0
        
        if "llama" in model.lower() or "meta" in model.lower():
            text = response_body.get("generation", "")
            input_tokens = response_body.get("prompt_token_count", 0)
            output_tokens = response_body.get("generation_token_count", 0)
            
        elif "mistral" in model.lower():
            outputs = response_body.get("outputs", [])
            if outputs:
                text = outputs[0].get("text", "")
            # Mistral may not always return token counts
            input_tokens = response_body.get("prompt_token_count", 0)
            output_tokens = response_body.get("generation_token_count", 0)
            
        elif "claude" in model.lower():
            content = response_body.get("content", [])
            if content:
                text = content[0].get("text", "")
            usage = response_body.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            
        elif "titan" in model.lower() or "amazon" in model.lower():
            results = response_body.get("results", [])
            if results:
                text = results[0].get("outputText", "")
            input_tokens = response_body.get("inputTextTokenCount", 0)
            output_tokens = response_body.get("outputTextTokenCount", 0) or \
                           response_body.get("results", [{}])[0].get("tokenCount", 0)
            
        elif "cohere" in model.lower():
            generations = response_body.get("generations", [])
            if generations:
                text = generations[0].get("text", "")
            # Cohere may not return token counts
            input_tokens = response_body.get("prompt_token_count", 0)
            output_tokens = response_body.get("generation_token_count", 0)
            
        else:
            # Generic fallback - try common fields
            text = response_body.get("completion", "") or \
                   response_body.get("text", "") or \
                   response_body.get("output", "") or \
                   str(response_body)
            input_tokens = response_body.get("input_tokens", 0) or \
                          response_body.get("prompt_tokens", 0)
            output_tokens = response_body.get("output_tokens", 0) or \
                           response_body.get("completion_tokens", 0)
        
        return text, input_tokens, output_tokens
    
    def list_models(self) -> list[str]:
        """List popular Bedrock models"""
        return [
            # Meta Llama
            "meta.llama3-70b-instruct-v1:0",
            "meta.llama3-8b-instruct-v1:0",
            "meta.llama2-70b-chat-v1",
            "meta.llama2-13b-chat-v1",
            
            # Mistral
            "mistral.mistral-7b-instruct-v0:2",
            "mistral.mixtral-8x7b-instruct-v0:1",
            "mistral.mistral-large-2402-v1:0",
            
            # Anthropic Claude (via Bedrock)
            "anthropic.claude-3-sonnet-20240229-v1:0",
            "anthropic.claude-3-haiku-20240307-v1:0",
            "anthropic.claude-3-opus-20240229-v1:0",
            
            # Amazon Titan
            "amazon.titan-text-express-v1",
            "amazon.titan-text-lite-v1",
            
            # Cohere
            "cohere.command-text-v14",
            "cohere.command-light-text-v14",
        ]

