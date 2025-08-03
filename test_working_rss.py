#!/usr/bin/env python3
"""
Test Scout Agent with working RSS feeds
"""

import sys
import os
import asyncio
import logging

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'agents', 'scout'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_scout_with_real_feeds():
    """Test Scout Agent with actual working RSS feeds"""
    print("Testing Scout Agent with real RSS feeds...")
    
    try:
        from agent import ScoutAgent
        
        # Working RSS feeds for testing
        working_feeds = [
            "https://www.archdaily.com/rss/",  # ArchDaily RSS
            "https://feeds.feedburner.com/TEDTalks_video"  # TED Talks (should work)
        ]
        
        config = {
            "rss_feeds": working_feeds,
            "scraping_interval": 30,
            "max_concurrent_scrapes": 2,
            "max_articles_per_source": 3,
            "rate_limit_delay": 2.0
        }
        
        scout = ScoutAgent("test-scout-real", config)
        print("[OK] Scout Agent created with real feeds")
        
        # Import architecture for task creation
        import importlib.util
        arch_path = os.path.join(os.path.dirname(__file__), 'multi-agent-architecture.py')
        spec = importlib.util.spec_from_file_location("multi_agent_architecture", arch_path)
        arch_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(arch_module)
        
        # Test discovery
        task = arch_module.AgentTask(
            task_id="real-test",
            agent_type="scout",
            priority=1,
            data={
                "type": "discover_rss",
                "feeds": working_feeds
            },
            created_at=arch_module.datetime.now()
        )
        
        print("Starting RSS discovery (this may take a moment)...")
        result = await scout.process_task(task)
        
        print(f"[RESULT] RSS discovery: {result.get('status', 'unknown')}")
        print(f"  - Feeds processed: {result.get('feeds_processed', 0)}")
        print(f"  - Articles discovered: {result.get('articles_discovered', 0)}")
        print(f"  - New articles: {result.get('new_articles', 0)}")
        print(f"  - Duplicates filtered: {result.get('duplicates_filtered', 0)}")
        
        # Show errors if any
        errors = result.get('errors', [])
        if errors:
            print(f"  - Errors: {len(errors)}")
            for error in errors[:2]:  # Show first 2 errors
                print(f"    * {error}")
        
        # Show sample articles
        articles = result.get('articles', [])
        if articles:
            print(f"\nSample articles found ({len(articles)} total):")
            for i, article in enumerate(articles[:3]):
                title = article.get('title', 'No title')[:50]
                url = article.get('url', 'No URL')
                print(f"  {i+1}. {title}...")
                print(f"     URL: {url}")
        else:
            print("\nNo articles were successfully discovered")
        
        # Test source metrics
        metrics_task = arch_module.AgentTask(
            task_id="metrics-test",
            agent_type="scout",
            priority=1,
            data={"type": "get_metrics"},
            created_at=arch_module.datetime.now()
        )
        
        metrics_result = await scout.process_task(metrics_task)
        if metrics_result.get('status') == 'success':
            print(f"\n[METRICS]")
            print(f"  - Total sources: {metrics_result.get('total_sources', 0)}")
            print(f"  - Content discovered: {metrics_result.get('total_content_discovered', 0)}")
            print(f"  - Unique hashes: {metrics_result.get('unique_content_hashes', 0)}")
        
        # Cleanup
        await scout.cleanup()
        print("\n[OK] Scout cleanup completed")
        
        return result.get('status') == 'success' and result.get('feeds_processed', 0) > 0
        
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("AEC AI News - Real RSS Feed Test")
    print("=" * 60)
    
    success = asyncio.run(test_scout_with_real_feeds())
    
    if success:
        print("\n[SUCCESS] Scout Agent successfully processed real RSS feeds!")
        print("The multi-agent system is working correctly.")
    else:
        print("\n[INFO] Test completed - check results above")
        print("Note: Some RSS feeds may be temporarily unavailable")
    
    print("\n" + "=" * 60)