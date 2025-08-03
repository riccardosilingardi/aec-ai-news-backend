import os
import json
from anthropic import Anthropic
from klavis import Klavis
from klavis.types import McpServerName, ToolFormat

# Load from environment variables
from dotenv import load_dotenv
load_dotenv()

# API keys loaded from .env file
# ANTHROPIC_API_KEY=your_key_here
# KLAVIS_API_KEY=your_key_here

# Inizializza il client Klavis
klavis_client = Klavis(api_key=os.getenv("KLAVIS_API_KEY"))

klavis_client = Klavis(api_key=os.getenv("KLAVIS_API_KEY"))

youtube_mcp_instance = klavis_client.mcp_server.create_server_instance(
    server_name=McpServerName.YOUTUBE,
    user_id="1234",
    platform_name="Klavis",
)

# print(f"🔗 YouTube MCP server created at: {youtube_mcp_instance.server_url}, and the instance id is {youtube_mcp_instance.instance_id}")

# Create general method to use MCP Server with Claude
def claude_with_mcp_server(mcp_server_url: str, user_query: str):
    claude_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    messages = [
        {"role": "user", "content": f"{user_query}"}
    ]
    
    mcp_server_tools = klavis_client.mcp_server.list_tools(
        server_url=mcp_server_url,
        format=ToolFormat.ANTHROPIC,
    )
    
    response = claude_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4000,
        system="You are a helpful assistant. Use the available tools to answer the user's question.",
        messages=messages,
        tools=mcp_server_tools.tools
    )
    
    messages.append({"role": "assistant", "content": response.content})

    if response.stop_reason == "tool_use":
        tool_results = []
        
        for content_block in response.content:
            if content_block.type == "tool_use":
                function_name = content_block.name
                function_args = content_block.input
                
                print(f"🔧 Calling: {function_name}, with args: {function_args}")
                
                result = klavis_client.mcp_server.call_tools(
                    server_url=mcp_server_url,
                    tool_name=function_name,
                    tool_args=function_args,
                )
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": content_block.id,
                    "content": str(result)
                })
        
        messages.append({"role": "user", "content": tool_results})
            
        final_response = claude_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            system="You are a helpful assistant. Use the available tools to answer the user's question.",
            messages=messages,
            tools=mcp_server_tools.tools
        )
        
        return final_response.content[0].text
    else:
        return response.content[0].text
    
# Summarize a YouTube video using the MCP server
YOUTUBE_VIDEO_URL = "https://www.youtube.com/watch?v=LCEmiRjPEtQ"  # pick a video you like!

result = claude_with_mcp_server(
    mcp_server_url=youtube_mcp_instance.server_url, 
    user_query=f"Summarize this YouTube video with timestamps: {YOUTUBE_VIDEO_URL}"
)

print(result)