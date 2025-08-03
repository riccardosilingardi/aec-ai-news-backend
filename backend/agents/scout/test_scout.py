"""
Test script for ScoutAgent RSS parsing functionality
"""

import asyncio
import logging
from datetime import datetime
from agent import ScoutAgent
from multi_agent_architecture import AgentTask

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_scout_agent():
    """Test the ScoutAgent RSS parsing functionality"""
    
    # Test configuration with AEC industry RSS feeds
    config = {
        "rss_feeds": [
            "https://www.archdaily.com/rss/",
            "https://www.constructiondive.com/feeds/",
            "https://www.dezeen.com/feed/",
            "https://feeds.feedburner.com/oreilly/radar",  # Tech industry feed
        ],
        "scraping_interval": 30,
        "max_concurrent_scrapes": 3,
        "max_articles_per_source": 5,
        "content_freshness_hours": 48,
        "rate_limit_delay": 1.0
    }
    
    # Initialize Scout Agent
    scout = ScoutAgent("scout-001", config)
    
    try:
        logger.info("=== Testing ScoutAgent Health Check ===")
        health_ok = await scout.health_check()
        logger.info(f"Health check result: {health_ok}")
        
        logger.info("=== Testing RSS Discovery ===")
        
        # Create RSS discovery task
        rss_task = AgentTask(
            task_id="test-rss-001",
            agent_type="scout",
            priority=1,
            data={
                "type": "discover_rss",
                "feeds": config["rss_feeds"][:2]  # Test with first 2 feeds
            },
            created_at=datetime.now()
        )
        
        # Process the task
        result = await scout.process_task(rss_task)
        
        logger.info("=== RSS Discovery Results ===")
        logger.info(f"Status: {result.get('status')}")
        logger.info(f"Feeds processed: {result.get('feeds_processed', 0)}")
        logger.info(f"Articles discovered: {result.get('articles_discovered', 0)}")
        logger.info(f"New articles: {result.get('new_articles', 0)}")
        logger.info(f"Duplicates filtered: {result.get('duplicates_filtered', 0)}")
        
        if result.get('errors'):
            logger.warning("Errors encountered:")
            for error in result['errors']:
                logger.warning(f"  - {error}")
        
        # Display sample articles
        articles = result.get('articles', [])
        if articles:
            logger.info(f"=== Sample Articles (showing first 3 of {len(articles)}) ===")
            for i, article in enumerate(articles[:3]):
                logger.info(f"Article {i+1}:")
                logger.info(f"  Title: {article.get('title', 'N/A')[:100]}...")
                logger.info(f"  URL: {article.get('url', 'N/A')}")
                logger.info(f"  Source: {article.get('source', 'N/A')}")
                logger.info(f"  Content length: {len(article.get('content', ''))}")
                logger.info("")
        
        logger.info("=== Testing Source Metrics ===")
        
        # Get source metrics
        metrics_task = AgentTask(
            task_id="test-metrics-001",
            agent_type="scout",
            priority=1,
            data={"type": "get_metrics"},
            created_at=datetime.now()
        )
        
        metrics_result = await scout.process_task(metrics_task)
        
        logger.info(f"Total sources tracked: {metrics_result.get('total_sources', 0)}")
        logger.info(f"Total content discovered: {metrics_result.get('total_content_discovered', 0)}")
        logger.info(f"Unique content hashes: {metrics_result.get('unique_content_hashes', 0)}")
        
        # Show source performance
        source_metrics = metrics_result.get('source_metrics', [])
        if source_metrics:
            logger.info("=== Source Performance ===")
            for source in source_metrics:
                logger.info(f"Source: {source.get('name', 'Unknown')}")
                logger.info(f"  Success rate: {source.get('success_rate', 0):.2%}")
                logger.info(f"  Avg articles per scrape: {source.get('avg_articles_per_scrape', 0):.1f}")
                logger.info(f"  Total articles: {source.get('total_articles_discovered', 0)}")
                logger.info(f"  Avg response time: {source.get('response_time_avg', 0):.2f}s")
                logger.info("")
        
        logger.info("=== Testing Single URL Scraping ===")
        
        # Test single URL scraping
        if articles:
            test_url = articles[0].get('url')
            if test_url:
                url_task = AgentTask(
                    task_id="test-url-001",
                    agent_type="scout",
                    priority=1,
                    data={
                        "type": "scrape_url",
                        "url": test_url
                    },
                    created_at=datetime.now()
                )
                
                url_result = await scout.process_task(url_task)
                logger.info(f"Single URL scraping result: {url_result.get('status')}")
                if url_result.get('status') == 'success':
                    article = url_result.get('article', {})
                    logger.info(f"  Content length: {len(article.get('content', ''))}")
        
        logger.info("=== ScoutAgent Test Completed Successfully ===")
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        await scout.cleanup()

if __name__ == "__main__":
    asyncio.run(test_scout_agent())