"""
MCP Integration for ScoutAgent
Provides MCP tools for Scout Agent RSS discovery functionality
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List

from agent import ScoutAgent
from multi_agent_architecture import AgentTask

logger = logging.getLogger(__name__)

class ScoutAgentMCPIntegration:
    """
    MCP integration layer for ScoutAgent
    Provides tools for content discovery and source management
    """
    
    def __init__(self, agent_config: Dict[str, Any]):
        self.scout_agent = ScoutAgent("scout-mcp-001", agent_config)
        self.agent_config = agent_config
    
    async def discover_aec_content(self, sources: List[str] = None, max_articles: int = 20) -> str:
        """
        MCP Tool: Discover AEC AI content from RSS feeds
        """
        try:
            if sources is None:
                sources = self.agent_config.get("rss_feeds", [])
            
            # Create discovery task
            task = AgentTask(
                task_id=f"mcp-discovery-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                agent_type="scout",
                priority=1,
                data={
                    "type": "discover_rss",
                    "feeds": sources[:10]  # Limit sources for MCP
                },
                created_at=datetime.now()
            )
            
            # Execute discovery
            result = await self.scout_agent.process_task(task)
            
            if result.get("status") == "success":
                feeds_processed = result.get("feeds_processed", 0)
                new_articles = result.get("new_articles", 0)
                duplicates = result.get("duplicates_filtered", 0)
                articles = result.get("articles", [])
                
                # Format response
                response = f"""
🔍 **AEC AI Content Discovery Results**

**Discovery Summary:**
• Feeds processed: {feeds_processed}
• New articles found: {new_articles}
• Duplicates filtered: {duplicates}
• Total articles: {len(articles)}

**Latest Discoveries:**
"""
                
                # Show top articles (limited for MCP output)
                for i, article in enumerate(articles[:max_articles]):
                    title = article.get("title", "No title")[:80]
                    url = article.get("url", "")
                    source_domain = self._extract_domain(article.get("source", ""))
                    content_length = len(article.get("content", ""))
                    
                    response += f"""
**{i+1}. {title}**
• Source: {source_domain}
• URL: {url}
• Content: {content_length} characters
• Discovered: {article.get("discovered_at", "")[:19]}
"""
                
                # Show errors if any
                errors = result.get("errors", [])
                if errors:
                    response += f"\n**Issues encountered:**\n"
                    for error in errors[:3]:  # Limit errors shown
                        response += f"• {error}\n"
                
                return response
                
            else:
                return f"❌ Discovery failed: {result.get('message', 'Unknown error')}"
                
        except Exception as e:
            logger.error(f"MCP discovery error: {e}")
            return f"❌ Discovery error: {str(e)}"
    
    async def get_source_performance(self) -> str:
        """
        MCP Tool: Get RSS source performance metrics
        """
        try:
            # Create metrics task
            task = AgentTask(
                task_id=f"mcp-metrics-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                agent_type="scout",
                priority=1,
                data={"type": "get_metrics"},
                created_at=datetime.now()
            )
            
            # Get metrics
            result = await self.scout_agent.process_task(task)
            
            if result.get("status") == "success":
                total_sources = result.get("total_sources", 0)
                total_content = result.get("total_content_discovered", 0)
                unique_hashes = result.get("unique_content_hashes", 0)
                source_metrics = result.get("source_metrics", [])
                
                response = f"""
📊 **Scout Agent Performance Dashboard**

**Overall Metrics:**
• Total RSS sources: {total_sources}
• Content items discovered: {total_content}
• Unique content pieces: {unique_hashes}
• Deduplication rate: {((total_content - unique_hashes) / max(total_content, 1)) * 100:.1f}%

**Source Performance:**
"""
                
                # Sort sources by success rate
                sorted_sources = sorted(
                    source_metrics, 
                    key=lambda x: x.get("success_rate", 0), 
                    reverse=True
                )
                
                for source in sorted_sources[:10]:  # Top 10 sources
                    name = source.get("name", "Unknown")
                    success_rate = source.get("success_rate", 0) * 100
                    avg_articles = source.get("avg_articles_per_scrape", 0)
                    total_articles = source.get("total_articles_discovered", 0)
                    response_time = source.get("response_time_avg", 0)
                    
                    status_emoji = "✅" if success_rate > 80 else "⚠️" if success_rate > 50 else "❌"
                    
                    response += f"""
{status_emoji} **{name}**
• Success rate: {success_rate:.1f}%
• Avg articles/scrape: {avg_articles:.1f}
• Total articles: {total_articles}
• Response time: {response_time:.2f}s
"""
                
                return response
                
            else:
                return f"❌ Metrics unavailable: {result.get('message', 'Unknown error')}"
                
        except Exception as e:
            logger.error(f"MCP metrics error: {e}")
            return f"❌ Metrics error: {str(e)}"
    
    async def test_rss_feed(self, feed_url: str) -> str:
        """
        MCP Tool: Test a single RSS feed
        """
        try:
            # Create single feed test task
            task = AgentTask(
                task_id=f"mcp-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                agent_type="scout",
                priority=1,
                data={
                    "type": "discover_rss",
                    "feeds": [feed_url]
                },
                created_at=datetime.now()
            )
            
            # Test the feed
            result = await self.scout_agent.process_task(task)
            
            if result.get("status") == "success":
                articles_found = result.get("articles_discovered", 0)
                new_articles = result.get("new_articles", 0)
                duplicates = result.get("duplicates_filtered", 0)
                
                response = f"""
🧪 **RSS Feed Test Results**

**Feed:** {feed_url}

**Results:**
• Articles found: {articles_found}
• New articles: {new_articles}
• Duplicates: {duplicates}
• Status: ✅ Working

**Sample Articles:**
"""
                
                articles = result.get("articles", [])
                for i, article in enumerate(articles[:3]):
                    title = article.get("title", "No title")[:60]
                    response += f"  {i+1}. {title}\n"
                
                return response
                
            else:
                errors = result.get("errors", [])
                error_msg = errors[0] if errors else "Unknown error"
                return f"""
🧪 **RSS Feed Test Results**

**Feed:** {feed_url}
**Status:** ❌ Failed
**Error:** {error_msg}

Please check if the feed URL is correct and accessible.
"""
                
        except Exception as e:
            logger.error(f"MCP feed test error: {e}")
            return f"❌ Feed test error: {str(e)}"
    
    async def check_agent_health(self) -> str:
        """
        MCP Tool: Check Scout Agent health status
        """
        try:
            health_ok = await self.scout_agent.health_check()
            
            if health_ok:
                return """
🏥 **Scout Agent Health Check**

**Status:** ✅ Healthy
**RSS Feeds:** Accessible
**HTTP Client:** Working
**Parsing:** Functional

The Scout Agent is ready for content discovery.
"""
            else:
                return """
🏥 **Scout Agent Health Check**

**Status:** ❌ Issues Detected
**Problems:** One or more RSS feeds are not accessible

Please check your network connection and RSS feed URLs.
"""
                
        except Exception as e:
            logger.error(f"MCP health check error: {e}")
            return f"❌ Health check error: {str(e)}"
    
    def _extract_domain(self, url: str) -> str:
        """Extract clean domain name from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception:
            return url
    
    async def cleanup(self):
        """Cleanup Scout Agent resources"""
        await self.scout_agent.cleanup()

# Factory function for easy MCP integration
def create_scout_mcp_tools(mcp_server, config: Dict[str, Any]):
    """
    Create and register Scout Agent MCP tools
    """
    integration = ScoutAgentMCPIntegration(config)
    
    @mcp_server.tool()
    async def discover_aec_content(sources: List[str] = None, max_articles: int = 20) -> str:
        """Discover AEC AI content from RSS feeds using Scout Agent"""
        return await integration.discover_aec_content(sources, max_articles)
    
    @mcp_server.tool()
    async def get_scout_performance() -> str:
        """Get Scout Agent RSS source performance metrics"""
        return await integration.get_source_performance()
    
    @mcp_server.tool()
    async def test_rss_feed(feed_url: str) -> str:
        """Test a single RSS feed with Scout Agent"""
        return await integration.test_rss_feed(feed_url)
    
    @mcp_server.tool()
    async def check_scout_health() -> str:
        """Check Scout Agent health status"""
        return await integration.check_agent_health()
    
    return integration