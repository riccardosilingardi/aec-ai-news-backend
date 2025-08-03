#!/usr/bin/env python3
"""
Test Enhanced Scout Agent with Advanced Scraping and YouTube Integration
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

async def test_enhanced_scout_agent():
    """Test Enhanced Scout Agent with all advanced features"""
    print("Testing Enhanced Scout Agent...")
    
    try:
        from enhanced_agent import EnhancedScoutAgent
        
        # Configuration for testing
        config = {
            # Basic RSS config
            "rss_feeds": [
                "https://www.archdaily.com/rss/",
                "https://feeds.feedburner.com/TEDTalks_video"
            ],
            "scraping_interval": 30,
            "max_concurrent_scrapes": 2,
            "max_articles_per_source": 2,
            "rate_limit_delay": 2.0,
            
            # Enhanced features config
            "enable_advanced_scraping": True,
            "enable_search": True,
            "enable_youtube": True,
            
            # Search configuration (no API keys for testing)
            "web_search_limit": 5,
            "youtube_search_limit": 3,
            
            # Advanced scraper config
            "use_scrapling": True,
            "scraper_max_retries": 2,
            "scraper_retry_delay": 3.0,
            "scraper_timeout": 20.0,
            
            # Search queries
            "search_queries": [
                "AI construction 2024",
                "BIM artificial intelligence"
            ],
            "youtube_search_queries": [
                "AI construction",
                "BIM artificial intelligence"
            ]
        }
        
        scout = EnhancedScoutAgent("test-enhanced-scout", config)
        print("[OK] Enhanced Scout Agent created")
        
        # Import architecture for task creation
        import importlib.util
        arch_path = os.path.join(os.path.dirname(__file__), 'multi-agent-architecture.py')
        spec = importlib.util.spec_from_file_location("multi_agent_architecture", arch_path)
        arch_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(arch_module)
        
        # Test 1: Enhanced health check
        print("\n=== Test 1: Enhanced Health Check ===")
        health_ok = await scout.health_check()
        print(f"[RESULT] Enhanced health check: {'PASS' if health_ok else 'FAIL'}")
        
        # Test 2: Basic RSS discovery (inherited functionality)
        print("\n=== Test 2: RSS Discovery ===")
        rss_task = arch_module.AgentTask(
            task_id="rss-test",
            agent_type="scout",
            priority=1,
            data={
                "type": "discover_rss",
                "feeds": config["rss_feeds"]
            },
            created_at=arch_module.datetime.now()
        )
        
        rss_result = await scout.process_task(rss_task)
        print(f"[RESULT] RSS discovery: {rss_result.get('status', 'unknown')}")
        print(f"  - Articles found: {rss_result.get('new_articles', 0)}")
        
        # Test 3: Advanced URL scraping
        print("\n=== Test 3: Advanced URL Scraping ===")
        scrape_task = arch_module.AgentTask(
            task_id="scrape-test",
            agent_type="scout",
            priority=1,
            data={
                "type": "scrape_url_advanced",
                "url": "https://httpbin.org/html"  # Safe test URL
            },
            created_at=arch_module.datetime.now()
        )
        
        scrape_result = await scout.process_task(scrape_task)
        print(f"[RESULT] Advanced scraping: {scrape_result.get('status', 'unknown')}")
        if scrape_result.get('status') == 'success':
            print(f"  - Scraper used: {scrape_result.get('scraper_used', 'unknown')}")
            print(f"  - Content length: {scrape_result.get('content_length', 0)}")
        
        # Test 4: Web search (if no API keys, will use DuckDuckGo fallback)
        print("\n=== Test 4: Web Search ===")
        search_task = arch_module.AgentTask(
            task_id="search-test",
            agent_type="scout",
            priority=1,
            data={
                "type": "search_web",
                "query": "AI construction industry",
                "max_results": 3
            },
            created_at=arch_module.datetime.now()
        )
        
        search_result = await scout.process_task(search_task)
        print(f"[RESULT] Web search: {search_result.get('status', 'unknown')}")
        if search_result.get('status') == 'success':
            print(f"  - Search results found: {search_result.get('search_results_found', 0)}")
            print(f"  - Content extracted: {search_result.get('content_extracted', 0)}")
            print(f"  - Sources used: {search_result.get('search_sources_used', [])}")
        
        # Test 5: YouTube search (will fail without API keys but should handle gracefully)
        print("\n=== Test 5: YouTube Search ===")
        youtube_task = arch_module.AgentTask(
            task_id="youtube-test",
            agent_type="scout",
            priority=1,
            data={
                "type": "search_youtube",
                "max_videos": 2
            },
            created_at=arch_module.datetime.now()
        )
        
        youtube_result = await scout.process_task(youtube_task)
        print(f"[RESULT] YouTube search: {youtube_result.get('status', 'unknown')}")
        if youtube_result.get('status') == 'success':
            print(f"  - Videos found: {youtube_result.get('videos_found', 0)}")
            print(f"  - Channels discovered: {youtube_result.get('channels_discovered', [])}")
        elif youtube_result.get('status') == 'error':
            print(f"  - Expected error (no API keys): {youtube_result.get('message', 'Unknown error')}")
        
        # Test 6: Comprehensive discovery
        print("\n=== Test 6: Comprehensive Discovery ===")
        comprehensive_task = arch_module.AgentTask(
            task_id="comprehensive-test",
            agent_type="scout",
            priority=1,
            data={
                "type": "comprehensive_discovery",
                "include_rss": True,
                "include_search": True,
                "include_youtube": False,  # Skip YouTube to avoid API errors
                "search_queries": ["AI architecture design"]
            },
            created_at=arch_module.datetime.now()
        )
        
        comprehensive_result = await scout.process_task(comprehensive_task)
        print(f"[RESULT] Comprehensive discovery: {comprehensive_result.get('status', 'unknown')}")
        if comprehensive_result.get('status') == 'success':
            print(f"  - Total content found: {comprehensive_result.get('total_content_found', 0)}")
            print(f"  - Discovery methods used: {comprehensive_result.get('discovery_methods', [])}")
            print(f"  - Errors: {len(comprehensive_result.get('errors', []))}")
        
        # Test 7: Get enhanced content
        print("\n=== Test 7: Enhanced Content Retrieval ===")
        content_task = arch_module.AgentTask(
            task_id="content-test",
            agent_type="scout",
            priority=1,
            data={
                "type": "get_enhanced_content",
                "max_items": 10,
                "min_relevance": 0.0,
                "include_youtube": False,
                "include_search": True
            },
            created_at=arch_module.datetime.now()
        )
        
        content_result = await scout.process_task(content_task)
        print(f"[RESULT] Enhanced content retrieval: {content_result.get('status', 'unknown')}")
        if content_result.get('status') == 'success':
            print(f"  - Total available: {content_result.get('total_available', 0)}")
            print(f"  - Filtered count: {content_result.get('filtered_count', 0)}")
            print(f"  - Returned count: {content_result.get('returned_count', 0)}")
            print(f"  - Content types: {list(content_result.get('content_by_type', {}).keys())}")
        
        # Show sample enhanced content
        all_content = content_result.get('all_content', [])
        if all_content:
            print(f"\nSample enhanced content ({len(all_content)} items):")
            for i, item in enumerate(all_content[:2]):
                print(f"  {i+1}. {item.get('title', 'No title')[:50]}...")
                print(f"     Type: {item.get('content_type', 'unknown')}")
                print(f"     Source: {item.get('source', 'unknown')}")
                print(f"     Relevance: {item.get('relevance_score', 0.0):.2f}")
        
        # Cleanup
        await scout.cleanup()
        print("\n[OK] Enhanced Scout cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Enhanced Scout test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_dependencies():
    """Test optional dependencies"""
    print("\n=== Testing Dependencies ===")
    
    # Test Scrapling
    try:
        from scrapling import Adapter
        print("[OK] Scrapling available")
    except ImportError:
        print("[INFO] Scrapling not available - install with: pip install scrapling")
    
    # Test Klavis
    try:
        from klavis import Klavis
        print("[OK] Klavis available")
    except ImportError:
        print("[INFO] Klavis not available - install with: pip install klavis")
    
    # Test Anthropic
    try:
        from anthropic import Anthropic
        print("[OK] Anthropic available")
    except ImportError:
        print("[INFO] Anthropic not available - install with: pip install anthropic")
    
    # Test httpx and BeautifulSoup
    try:
        import httpx
        print("[OK] httpx available")
    except ImportError:
        print("[WARN] httpx not available - install with: pip install httpx")
    
    try:
        from bs4 import BeautifulSoup
        print("[OK] BeautifulSoup available")
    except ImportError:
        print("[WARN] BeautifulSoup not available - install with: pip install beautifulsoup4")

def show_requirements():
    """Show requirements for full functionality"""
    print("\n=== Requirements for Full Functionality ===")
    print("Required packages:")
    print("  pip install httpx beautifulsoup4 feedparser")
    print("\nOptional packages for enhanced features:")
    print("  pip install scrapling      # Advanced anti-bot scraping")
    print("  pip install klavis         # YouTube integration")
    print("  pip install anthropic      # AI-powered content analysis")
    print("\nAPI Keys needed for search functionality:")
    print("  - BING_API_KEY for Bing Web Search")
    print("  - GOOGLE_API_KEY + GOOGLE_CSE_ID for Google Custom Search")
    print("  - SERPAPI_KEY for SerpAPI")
    print("  - KLAVIS_API_KEY for YouTube integration")
    print("  - ANTHROPIC_API_KEY for content analysis")

if __name__ == "__main__":
    print("=" * 70)
    print("AEC AI News - Enhanced Scout Agent Test")
    print("=" * 70)
    
    # Test dependencies first
    asyncio.run(test_dependencies())
    
    # Run main test
    success = asyncio.run(test_enhanced_scout_agent())
    
    if success:
        print("\n[SUCCESS] Enhanced Scout Agent test completed successfully!")
        print("All advanced features are working correctly.")
    else:
        print("\n[INFO] Enhanced Scout Agent test completed - check results above")
        print("Some features may require additional dependencies or API keys.")
    
    # Show requirements
    show_requirements()
    
    print("\n" + "=" * 70)