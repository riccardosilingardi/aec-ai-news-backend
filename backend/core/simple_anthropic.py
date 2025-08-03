"""
Simple Anthropic client using HTTP requests
Avoids Rust compilation issues
"""
import httpx
import json
from typing import Dict, Any, List

class SimpleAnthropicClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1"
        self.headers = {
            "x-api-key": api_key,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01"
        }
    
    async def create_message(self, model: str, max_tokens: int, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Create a message with Claude"""
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/messages",
                json=payload,
                headers=self.headers,
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()
    
    async def chat_completion(self, prompt: str, model: str = "claude-3-sonnet-20240229", max_tokens: int = 1000) -> str:
        """Simple chat completion"""
        messages = [{"role": "user", "content": prompt}]
        response = await self.create_message(model, max_tokens, messages)
        return response["content"][0]["text"]