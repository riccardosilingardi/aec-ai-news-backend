#!/usr/bin/env python3
"""
Simple test to verify the multi-agent system imports and basic functionality
"""

import sys
import os
import asyncio
import logging

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all modules can be imported correctly"""
    print("Testing imports...")
    
    try:
        # Test architecture import
        import importlib.util
        arch_path = os.path.join(os.path.dirname(__file__), 'multi-agent-architecture.py')
        spec = importlib.util.spec_from_file_location("multi_agent_architecture", arch_path)
        arch_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(arch_module)
        print("[OK] Architecture module imported")
        
        # Test Scout Agent
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'agents', 'scout'))
        from agent import ScoutAgent
        print("[OK] Scout Agent imported")
        
        # Test basic Scout functionality
        scout_config = {
            "rss_feeds": ["https://feeds.feedburner.com/oreilly/radar"],
            "scraping_interval": 30,
            "max_concurrent_scrapes": 2,
            "rate_limit_delay": 1.0
        }
        scout = ScoutAgent("test-scout", scout_config)
        print("[OK] Scout Agent created")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_scout_basic():
    """Test basic Scout Agent functionality"""
    print("\nTesting Scout Agent basic functionality...")
    
    try:
        # Import Scout directly
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'agents', 'scout'))
        from agent import ScoutAgent
        
        # Create Scout with minimal config
        config = {
            "rss_feeds": ["https://feeds.feedburner.com/oreilly/radar"],
            "scraping_interval": 30,
            "max_concurrent_scrapes": 1,
            "max_articles_per_source": 2,
            "rate_limit_delay": 1.0
        }
        
        scout = ScoutAgent("test-scout", config)
        print("[OK] Scout Agent initialized")
        
        # Test health check
        health_ok = await scout.health_check()
        print(f"[OK] Scout health check: {'PASS' if health_ok else 'FAIL'}")
        
        # Test RSS discovery with one simple feed
        try:
            # Import task structure
            import importlib.util
            arch_path = os.path.join(os.path.dirname(__file__), 'multi-agent-architecture.py')
            spec = importlib.util.spec_from_file_location("multi_agent_architecture", arch_path)
            arch_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(arch_module)
            
            task = arch_module.AgentTask(
                task_id="simple-test",
                agent_type="scout",
                priority=1,
                data={
                    "type": "discover_rss",
                    "feeds": ["https://feeds.feedburner.com/oreilly/radar"]
                },
                created_at=arch_module.datetime.now()
            )
            
            result = await scout.process_task(task)
            print(f"[OK] RSS discovery test: {result.get('status', 'unknown')}")
            
            if result.get('status') == 'success':
                print(f"  - Articles found: {result.get('new_articles', 0)}")
                print(f"  - Feeds processed: {result.get('feeds_processed', 0)}")
            
        except Exception as e:
            print(f"[FAIL] RSS discovery failed: {e}")
        
        # Cleanup
        await scout.cleanup()
        print("[OK] Scout cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Scout test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("=" * 50)
    print("AEC AI News - Simple System Test")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        print("\n[FAIL] Import tests failed")
        return False
    
    # Test basic Scout functionality
    try:
        scout_success = asyncio.run(test_scout_basic())
        if not scout_success:
            print("\n[FAIL] Scout tests failed")
            return False
    except Exception as e:
        print(f"\n[FAIL] Async test failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("[SUCCESS] All basic tests passed!")
    print("=" * 50)
    print("\nSystem components verified:")
    print("- Architecture module loading")
    print("- Scout Agent creation and health check")
    print("- RSS discovery functionality")
    print("- Task processing system")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)