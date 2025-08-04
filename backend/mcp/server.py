"""
MCP Server Integration Layer

TODO - Phase 4 (Week 4):
[ ] MCP tools for agent management and control
[ ] MCP resources for real-time system status
[ ] MCP prompts for content generation assistance  
[ ] Integration with multi-agent system
[ ] Real-time monitoring dashboard
[ ] Manual override capabilities for emergency control

MCP TOOLS TO IMPLEMENT:
- start_content_discovery(): Trigger Scout Agent
- analyze_content_quality(): Run Curator analysis
- generate_newsletter_now(): Force Writer Agent execution
- get_system_health(): Monitor Agent status
- override_content_selection(): Manual content curation
- export_analytics(): Business metrics extraction

MCP RESOURCES:
- system://agents/status: Real-time agent status
- content://articles/queue: Current content pipeline
- metrics://performance: System performance data
- newsletter://latest: Most recent newsletter data
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime

try:
    from mcp.server.fastmcp import FastMCP
    from mcp.server.models import InitializationOptions
    from mcp.types import Tool, Resource, Prompt
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    FastMCP = None

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from core.config import get_config
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from multi_agent_system import MultiAgentSystem
from mcp.tools import MCPTools
from mcp.resources import MCPResources
from mcp.prompts import MCPPrompts

logger = logging.getLogger(__name__)

class AECMCPServer:
    """AEC AI News MCP Server"""
    
    def __init__(self):
        if not MCP_AVAILABLE:
            raise ImportError("FastMCP not available. Install with: pip install fastmcp")
        
        self.config = get_config()
        self.multi_agent_system = None
        self.mcp_server = None
        self.tools = MCPTools()
        self.resources = MCPResources()
        self.prompts = MCPPrompts()
        
        self._initialize_server()
    
    def _initialize_server(self):
        """Initialize MCP server with tools, resources, and prompts"""
        self.mcp_server = FastMCP("AEC AI News Multi-Agent System")
        
        # Register tools
        self._register_tools()
        
        # Register resources
        self._register_resources()
        
        # Register prompts
        self._register_prompts()
        
        logger.info("MCP server initialized with tools, resources, and prompts")
    
    def _register_tools(self):
        """Register MCP tools for agent control"""
        
        @self.mcp_server.tool()
        async def start_content_discovery(max_articles: int = 50) -> Dict[str, Any]:
            """Trigger Scout Agent content discovery"""
            if not self.multi_agent_system:
                return {"error": "Multi-agent system not initialized"}
            
            try:
                result = await self.tools.start_content_discovery(
                    self.multi_agent_system, max_articles
                )
                return result
            except Exception as e:
                logger.error(f"Content discovery error: {e}")
                return {"error": str(e)}
        
        @self.mcp_server.tool()
        async def analyze_content_quality(content_ids: List[int] = None) -> Dict[str, Any]:
            """Run Curator Agent quality analysis"""
            if not self.multi_agent_system:
                return {"error": "Multi-agent system not initialized"}
            
            try:
                result = await self.tools.analyze_content_quality(
                    self.multi_agent_system, content_ids
                )
                return result
            except Exception as e:
                logger.error(f"Content analysis error: {e}")
                return {"error": str(e)}
        
        @self.mcp_server.tool()
        async def generate_newsletter_now(force: bool = False) -> Dict[str, Any]:
            """Force Writer Agent newsletter generation"""
            if not self.multi_agent_system:
                return {"error": "Multi-agent system not initialized"}
            
            try:
                result = await self.tools.generate_newsletter_now(
                    self.multi_agent_system, force
                )
                return result
            except Exception as e:
                logger.error(f"Newsletter generation error: {e}")
                return {"error": str(e)}
        
        @self.mcp_server.tool()
        async def get_system_health() -> Dict[str, Any]:
            """Monitor Agent status and system health"""
            if not self.multi_agent_system:
                return {"error": "Multi-agent system not initialized"}
            
            try:
                result = await self.tools.get_system_health(self.multi_agent_system)
                return result
            except Exception as e:
                logger.error(f"Health check error: {e}")
                return {"error": str(e)}
        
        @self.mcp_server.tool()
        async def override_content_selection(
            include_ids: List[int] = None,
            exclude_ids: List[int] = None,
            quality_threshold: float = None
        ) -> Dict[str, Any]:
            """Manual content curation override"""
            if not self.multi_agent_system:
                return {"error": "Multi-agent system not initialized"}
            
            try:
                result = await self.tools.override_content_selection(
                    self.multi_agent_system, include_ids, exclude_ids, quality_threshold
                )
                return result
            except Exception as e:
                logger.error(f"Content override error: {e}")
                return {"error": str(e)}
        
        @self.mcp_server.tool()
        async def export_analytics(
            start_date: str = None,
            end_date: str = None,
            format: str = "json"
        ) -> Dict[str, Any]:
            """Export business metrics and analytics"""
            if not self.multi_agent_system:
                return {"error": "Multi-agent system not initialized"}
            
            try:
                result = await self.tools.export_analytics(
                    self.multi_agent_system, start_date, end_date, format
                )
                return result
            except Exception as e:
                logger.error(f"Analytics export error: {e}")
                return {"error": str(e)}
        
        @self.mcp_server.tool()
        async def restart_agent(agent_type: str) -> Dict[str, Any]:
            """Restart a specific agent"""
            if not self.multi_agent_system:
                return {"error": "Multi-agent system not initialized"}
            
            try:
                result = await self.tools.restart_agent(self.multi_agent_system, agent_type)
                return result
            except Exception as e:
                logger.error(f"Agent restart error: {e}")
                return {"error": str(e)}
        
        @self.mcp_server.tool()
        async def configure_agent(agent_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
            """Update agent configuration"""
            if not self.multi_agent_system:
                return {"error": "Multi-agent system not initialized"}
            
            try:
                result = await self.tools.configure_agent(
                    self.multi_agent_system, agent_type, config
                )
                return result
            except Exception as e:
                logger.error(f"Agent configuration error: {e}")
                return {"error": str(e)}
    
    def _register_resources(self):
        """Register MCP resources for real-time data access"""
        
        @self.mcp_server.resource("system://agents/status")
        async def agents_status() -> str:
            """Real-time agent status"""
            if not self.multi_agent_system:
                return "Multi-agent system not initialized"
            
            try:
                status = await self.resources.get_agents_status(self.multi_agent_system)
                return status
            except Exception as e:
                logger.error(f"Agent status error: {e}")
                return f"Error: {e}"
        
        @self.mcp_server.resource("content://articles/queue")
        async def articles_queue() -> str:
            """Current content pipeline"""
            if not self.multi_agent_system:
                return "Multi-agent system not initialized"
            
            try:
                queue = await self.resources.get_articles_queue(self.multi_agent_system)
                return queue
            except Exception as e:
                logger.error(f"Articles queue error: {e}")
                return f"Error: {e}"
        
        @self.mcp_server.resource("metrics://performance")
        async def performance_metrics() -> str:
            """System performance data"""
            if not self.multi_agent_system:
                return "Multi-agent system not initialized"
            
            try:
                metrics = await self.resources.get_performance_metrics(self.multi_agent_system)
                return metrics
            except Exception as e:
                logger.error(f"Performance metrics error: {e}")
                return f"Error: {e}"
        
        @self.mcp_server.resource("newsletter://latest")
        async def latest_newsletter() -> str:
            """Most recent newsletter data"""
            if not self.multi_agent_system:
                return "Multi-agent system not initialized"
            
            try:
                newsletter = await self.resources.get_latest_newsletter(self.multi_agent_system)
                return newsletter
            except Exception as e:
                logger.error(f"Latest newsletter error: {e}")
                return f"Error: {e}"
    
    def _register_prompts(self):
        """Register MCP prompts for content generation assistance"""
        
        @self.mcp_server.prompt()
        async def generate_newsletter_summary(articles: str) -> str:
            """Generate newsletter executive summary"""
            try:
                summary = await self.prompts.generate_newsletter_summary(articles)
                return summary
            except Exception as e:
                logger.error(f"Newsletter summary error: {e}")
                return f"Error generating summary: {e}"
        
        @self.mcp_server.prompt()
        async def analyze_content_quality(content: str) -> str:
            """Analyze content quality and relevance"""
            try:
                analysis = await self.prompts.analyze_content_quality(content)
                return analysis
            except Exception as e:
                logger.error(f"Content quality analysis error: {e}")
                return f"Error analyzing content: {e}"
        
        @self.mcp_server.prompt()
        async def categorize_content(content: str) -> str:
            """Categorize content by AEC industry topics"""
            try:
                category = await self.prompts.categorize_content(content)
                return category
            except Exception as e:
                logger.error(f"Content categorization error: {e}")
                return f"Error categorizing content: {e}"
    
    async def start(self):
        """Start the MCP server and multi-agent system"""
        try:
            # Initialize multi-agent system
            self.multi_agent_system = MultiAgentSystem()
            await self.multi_agent_system.initialize()
            
            # Start MCP server
            logger.info(f"Starting MCP server on {self.config.mcp.host}:{self.config.mcp.port}")
            await self.mcp_server.run(
                host=self.config.mcp.host,
                port=self.config.mcp.port
            )
            
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            raise
    
    async def stop(self):
        """Stop the MCP server and multi-agent system"""
        try:
            if self.multi_agent_system:
                await self.multi_agent_system.cleanup()
            
            logger.info("MCP server stopped")
            
        except Exception as e:
            logger.error(f"Error stopping MCP server: {e}")

# CLI entry point
async def main():
    """Main entry point for MCP server"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AEC AI News MCP Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Update config with CLI args
    config = get_config()
    config.mcp.host = args.host
    config.mcp.port = args.port
    config.debug = args.debug
    
    # Start server
    server = AECMCPServer()
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await server.stop()

if __name__ == "__main__":
    if not MCP_AVAILABLE:
        print("FastMCP not available. Install with: pip install fastmcp")
        exit(1)
    
    asyncio.run(main())