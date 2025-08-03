"""
Simple Supabase client using HTTP requests
Avoids Rust compilation issues on Render
"""
import httpx
from typing import Dict, Any, List

class SimpleSupabaseClient:
    def __init__(self, url: str, key: str):
        self.url = url.rstrip('/')
        self.key = key
        self.headers = {
            'apikey': key,
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json'
        }
    
    async def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.url}/rest/v1/{table}",
                json=data,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def select(self, table: str, columns: str = "*") -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.url}/rest/v1/{table}?select={columns}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()