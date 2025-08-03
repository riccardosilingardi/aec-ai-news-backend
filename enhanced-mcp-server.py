#!/usr/bin/env python3
"""
Enhanced AEC AI News Scout - MCP Server with Multi-Agent Integration
Combines the original MCP functionality with the new Scout Agent architecture
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP

# Import original business configuration and models
import importlib.util

# Load original MCP module
spec = importlib.util.spec_from_file_location("aec_ai_news_mcp", "aec-ai-news-mcp.py")
aec_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(aec_module)

BusinessConfig = aec_module.BusinessConfig
NewsDatabase = aec_module.NewsDatabase  
AECNewsScraper = aec_module.AECNewsScraper
NewsletterGenerator = aec_module.NewsletterGenerator

# Import new Scout Agent functionality
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'agents', 'scout'))
from mcp_integration import create_scout_mcp_tools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# ENHANCED APPLICATION CONTEXT
# =============================================================================

@dataclass
class EnhancedAppContext:
    """Enhanced application context with multi-agent support"""
    # Original components
    db: NewsDatabase
    scraper: AECNewsScraper
    generator: NewsletterGenerator
    config: BusinessConfig
    
    # New Scout Agent integration
    scout_integration: Any = None

@asynccontextmanager
async def enhanced_app_lifespan(server: FastMCP) -> AsyncIterator[EnhancedAppContext]:
    """Enhanced application lifecycle with Scout Agent"""
    # Initialize original components
    config = BusinessConfig()
    db = NewsDatabase()
    scraper = AECNewsScraper(config)
    generator = NewsletterGenerator(config)
    
    # Configure Scout Agent
    scout_config = {
        "rss_feeds": config.target_sources,
        "scraping_interval": 30,
        "max_concurrent_scrapes": 5,
        "max_articles_per_source": 10,
        "content_freshness_hours": 48,
        "rate_limit_delay": 2.0
    }
    
    # Create Scout Agent MCP integration
    scout_integration = create_scout_mcp_tools(server, scout_config)
    
    try:
        yield EnhancedAppContext(
            db=db,
            scraper=scraper,
            generator=generator,
            config=config,
            scout_integration=scout_integration
        )
    finally:
        # Cleanup
        await scraper.session.aclose()
        if scout_integration:
            await scout_integration.cleanup()

# Initialize enhanced MCP server
mcp = FastMCP(
    "Enhanced AEC AI News Scout",
    dependencies=[
        "httpx", "beautifulsoup4", "feedparser", "pydantic"
    ],
    lifespan=enhanced_app_lifespan
)

# =============================================================================
# ENHANCED MCP TOOLS (combining original + Scout Agent)
# =============================================================================

@mcp.tool()
async def discover_aec_content_advanced(sources: List[str] = None, max_articles: int = 20) -> str:
    """Advanced AEC AI content discovery using Scout Agent architecture"""
    ctx = mcp.get_context()
    app_ctx = ctx.request_context.lifespan_context
    
    # Use Scout Agent for discovery
    if app_ctx.scout_integration:
        return await app_ctx.scout_integration.discover_aec_content(sources, max_articles)
    else:
        return "❌ Scout Agent not available"

@mcp.tool()
async def get_discovery_performance() -> str:
    """Get comprehensive content discovery performance metrics"""
    ctx = mcp.get_context()
    app_ctx = ctx.request_context.lifespan_context
    
    # Get Scout Agent metrics
    scout_metrics = ""
    if app_ctx.scout_integration:
        scout_metrics = await app_ctx.scout_integration.get_source_performance()
    
    # Get database metrics
    import sqlite3
    conn = sqlite3.connect(app_ctx.db.db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM articles")
    total_articles = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM articles WHERE DATE(scraped_at) >= DATE('now', '-7 days')")
    week_articles = cursor.fetchone()[0]
    
    cursor.execute("SELECT AVG(quality_score), AVG(ai_relevance) FROM articles")
    avg_quality, avg_ai_relevance = cursor.fetchone()
    
    conn.close()
    
    combined_report = f"""
🚀 **Enhanced AEC AI News Discovery Performance**

**Database Overview:**
• Total articles in database: {total_articles}
• Articles discovered this week: {week_articles}
• Average quality score: {avg_quality:.2f}/1.0
• Average AI relevance: {avg_ai_relevance:.2f}/1.0

{scout_metrics}

**System Integration Status:**
• Original scraper: ✅ Active
• Scout Agent: {"✅ Active" if app_ctx.scout_integration else "❌ Unavailable"}
• Database: ✅ Connected
• Newsletter generator: ✅ Ready
"""
    
    return combined_report

@mcp.tool()
async def test_content_source(source_url: str) -> str:
    """Test a content source using both original and Scout Agent methods"""
    ctx = mcp.get_context()
    app_ctx = ctx.request_context.lifespan_context
    
    results = f"""
🧪 **Content Source Testing: {source_url}**

"""
    
    # Test with Scout Agent
    if app_ctx.scout_integration:
        scout_result = await app_ctx.scout_integration.test_rss_feed(source_url)
        results += f"**Scout Agent Test:**\n{scout_result}\n\n"
    
    # Test with original scraper
    try:
        articles = await app_ctx.scraper.scrape_rss_feed(source_url)
        if articles:
            results += f"""**Original Scraper Test:**
✅ Successfully parsed RSS feed
• Articles found: {len(articles)}
• Sample titles:
"""
            for i, article in enumerate(articles[:3]):
                title = article.get('title', 'No title')[:60]
                results += f"  {i+1}. {title}\n"
        else:
            results += "**Original Scraper Test:**\n❌ No articles found\n"
            
    except Exception as e:
        results += f"**Original Scraper Test:**\n❌ Error: {str(e)}\n"
    
    return results

@mcp.tool()
async def generate_enhanced_newsletter(issue_number: int = None, use_scout_content: bool = True) -> str:
    """Generate newsletter using enhanced content discovery"""
    ctx = mcp.get_context()
    app_ctx = ctx.request_context.lifespan_context
    
    results = []
    
    # Optionally discover fresh content with Scout Agent
    if use_scout_content and app_ctx.scout_integration:
        discovery_result = await app_ctx.scout_integration.discover_aec_content(max_articles=15)
        results.append(f"**Fresh Content Discovery:**\n{discovery_result}\n")
    
    # Generate newsletter using original method
    newsletter_result = await aec_module.generate_newsletter(issue_number)
    results.append(f"**Newsletter Generation:**\n{newsletter_result}")
    
    return "\n".join(results)

@mcp.tool()
async def system_health_check() -> str:
    """Comprehensive system health check"""
    ctx = mcp.get_context()
    app_ctx = ctx.request_context.lifespan_context
    
    health_report = """
🏥 **Enhanced AEC AI News System Health Check**

"""
    
    # Database health
    try:
        import sqlite3
        conn = sqlite3.connect(app_ctx.db.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM articles")
        article_count = cursor.fetchone()[0]
        conn.close()
        health_report += f"✅ **Database:** Connected ({article_count} articles)\n"
    except Exception as e:
        health_report += f"❌ **Database:** Error - {str(e)}\n"
    
    # Scout Agent health
    if app_ctx.scout_integration:
        scout_health = await app_ctx.scout_integration.check_agent_health()
        health_report += f"**Scout Agent:**\n{scout_health}\n"
    else:
        health_report += "❌ **Scout Agent:** Not available\n"
    
    # Original scraper health
    try:
        test_feeds = app_ctx.config.target_sources[:2]
        working_feeds = 0
        for feed in test_feeds:
            try:
                articles = await app_ctx.scraper.scrape_rss_feed(feed)
                if articles:
                    working_feeds += 1
            except:
                pass
        
        health_report += f"✅ **Original Scraper:** {working_feeds}/{len(test_feeds)} test feeds working\n"
        
    except Exception as e:
        health_report += f"❌ **Original Scraper:** Error - {str(e)}\n"
    
    # Configuration check
    health_report += f"""
**Configuration:**
• RSS feeds configured: {len(app_ctx.config.target_sources)}
• Content categories: {len(app_ctx.config.content_categories)}
• Newsletter frequency: {app_ctx.config.newsletter_frequency}
• Monetization model: {app_ctx.config.monetization_model}

**System Status:** {"🟢 All systems operational" if "❌" not in health_report else "🟡 Some issues detected"}
"""
    
    return health_report

# =============================================================================
# ORIGINAL TOOLS (Re-exported with context)
# =============================================================================

@mcp.tool()
async def scrape_aec_news_original(sources: List[str] = None) -> str:
    """Original AEC news scraping functionality"""
    # Use original function from loaded module
    return await aec_module.scrape_aec_news(sources)

@mcp.tool()
async def generate_newsletter_original(issue_number: int = None) -> str:
    """Original newsletter generation functionality"""
    return await aec_module.generate_newsletter(issue_number)

@mcp.tool()
async def analyze_content_performance_original() -> str:
    """Original content performance analysis"""
    return await aec_module.analyze_content_performance()

# =============================================================================
# ENHANCED RESOURCES
# =============================================================================

@mcp.resource("aec://system/status", title="Enhanced System Status")
async def get_enhanced_system_status() -> str:
    """Get comprehensive system status including Scout Agent"""
    return await system_health_check()

@mcp.resource("aec://discovery/performance", title="Content Discovery Performance")
async def get_discovery_performance_resource() -> str:
    """Get detailed content discovery performance metrics"""
    return await get_discovery_performance()

# =============================================================================
# ENHANCED PROMPTS
# =============================================================================

@mcp.prompt()
async def enhanced_newsletter_prompt(topic: str = "weekly_digest", use_scout_data: bool = True) -> str:
    """Enhanced newsletter generation prompt with Scout Agent integration"""
    
    base_prompt = f"""
Create a professional yet friendly newsletter for the AEC (Architecture, Engineering, Construction) industry focusing on AI developments.

Topic focus: {topic}

**Enhanced Content Sources:**
- Multi-agent content discovery system
- Advanced RSS parsing with Scout Agent
- Deduplication and quality scoring
- Real-time source performance tracking

Style requirements:
- Executive summary in Superhuman style (friendly, actionable, emoji usage)
- Clear section divisions by category with business impact indicators
- Data-driven insights from Scout Agent metrics
- Action items for readers based on trending content
- Professional but approachable tone
- Include reading time estimates and source reliability indicators

Structure:
1. Friendly greeting with key insights preview from Scout Agent
2. Executive summary with trending topics and source performance
3. Category-based article sections with quality scores
4. Business impact analysis with Scout Agent recommendations
5. Call-to-action for engagement and feedback

**Integration Benefits:**
- Real-time content freshness validation
- Advanced deduplication (hash-based)
- Source reliability metrics
- Performance tracking and optimization
- Automated quality scoring

Make it valuable for busy AEC professionals who need reliable, AI-curated information about industry trends.
    """
    
    if use_scout_data:
        ctx = mcp.get_context()
        app_ctx = ctx.request_context.lifespan_context
        
        if app_ctx.scout_integration:
            performance_data = await app_ctx.scout_integration.get_source_performance()
            base_prompt += f"\n\n**Current Scout Agent Performance Data:**\n{performance_data}"
    
    return base_prompt

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # For development
    uvicorn.run(
        "enhanced-mcp-server:mcp",
        host="127.0.0.1",
        port=8001,  # Different port to avoid conflicts
        reload=True
    )