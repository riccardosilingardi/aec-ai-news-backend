"""
Simple Mailjet client using HTTP requests
Avoids potential Rust compilation issues
"""
import httpx
import json
from typing import Dict, Any, List
import base64

class SimpleMailjetClient:
    def __init__(self, api_key: str, secret_key: str):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = "https://api.mailjet.com/v3.1"
        
        # Create basic auth header
        credentials = f"{api_key}:{secret_key}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        self.headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json"
        }
    
    async def send_email(self, from_email: str, from_name: str, to_email: str, 
                        subject: str, html_content: str, text_content: str = None) -> Dict[str, Any]:
        """Send email via Mailjet API"""
        payload = {
            "Messages": [{
                "From": {
                    "Email": from_email,
                    "Name": from_name
                },
                "To": [{
                    "Email": to_email
                }],
                "Subject": subject,
                "HTMLPart": html_content,
                "TextPart": text_content or ""
            }]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/send",
                json=payload,
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    async def send_newsletter(self, from_email: str, from_name: str, 
                            recipients: List[str], subject: str, 
                            html_content: str) -> Dict[str, Any]:
        """Send newsletter to multiple recipients"""
        to_list = [{"Email": email} for email in recipients]
        
        payload = {
            "Messages": [{
                "From": {
                    "Email": from_email,
                    "Name": from_name
                },
                "To": to_list,
                "Subject": subject,
                "HTMLPart": html_content
            }]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/send",
                json=payload,
                headers=self.headers,
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()