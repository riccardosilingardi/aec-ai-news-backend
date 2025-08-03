#!/usr/bin/env python3
"""
Setup script for Scout Agent deployment
No Unicode characters - ASCII only for compatibility
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path

def setup_directory_structure():
    """Create necessary directories for Scout Agent"""
    base_dir = Path(__file__).parent
    
    directories = [
        "backend/agents/scout",
        "backend/agents/curator", 
        "backend/agents/writer",
        "backend/agents/orchestrator",
        "backend/agents/monitor",
        "logs",
        "data"
    ]
    
    for directory in directories:
        dir_path = base_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

def install_dependencies():
    """Install required Python packages"""
    print("Installing dependencies...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        print("Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False
    
    return True

def verify_installation():
    """Verify Scout Agent can be imported and initialized"""
    print("Verifying Scout Agent installation...")
    
    try:
        # Add the backend agents directory to Python path
        sys.path.insert(0, str(Path(__file__).parent / "backend" / "agents" / "scout"))
        
        # Import Scout Agent
        from agent import ScoutAgent
        from multi_agent_architecture import AgentTask
        
        # Test configuration
        test_config = {
            "rss_feeds": [
                "https://feeds.feedburner.com/oreilly/radar"
            ],
            "scraping_interval": 30,
            "max_concurrent_scrapes": 2,
            "max_articles_per_source": 5,
            "content_freshness_hours": 48,
            "rate_limit_delay": 1.0
        }
        
        # Initialize Scout Agent
        scout = ScoutAgent("scout-test", test_config)
        print("Scout Agent initialized successfully")
        
        return True
        
    except ImportError as e:
        print(f"Import error: {e}")
        return False
    except Exception as e:
        print(f"Verification error: {e}")
        return False

async def run_scout_test():
    """Run a quick test of Scout Agent functionality"""
    print("Running Scout Agent test...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent / "backend" / "agents" / "scout"))
        from agent import ScoutAgent
        from multi_agent_architecture import AgentTask
        from datetime import datetime
        
        # Test configuration
        config = {
            "rss_feeds": [
                "https://feeds.feedburner.com/oreilly/radar"
            ],
            "scraping_interval": 30,
            "max_concurrent_scrapes": 2,
            "max_articles_per_source": 3,
            "content_freshness_hours": 48,
            "rate_limit_delay": 1.0
        }
        
        # Initialize and test Scout Agent
        scout = ScoutAgent("scout-test", config)
        
        # Health check
        health_ok = await scout.health_check()
        print(f"Health check: {'PASS' if health_ok else 'FAIL'}")
        
        # Test RSS discovery
        task = AgentTask(
            task_id="setup-test-001",
            agent_type="scout",
            priority=1,
            data={
                "type": "discover_rss",
                "feeds": config["rss_feeds"][:1]
            },
            created_at=datetime.now()
        )
        
        result = await scout.process_task(task)
        print(f"RSS discovery test: {result.get('status', 'UNKNOWN')}")
        
        if result.get('status') == 'success':
            print(f"Articles discovered: {result.get('new_articles', 0)}")
        
        # Cleanup
        await scout.cleanup()
        print("Scout Agent test completed successfully")
        return True
        
    except Exception as e:
        print(f"Test error: {e}")
        return False

def create_sample_config():
    """Create a sample configuration file"""
    config_content = '''# Scout Agent Configuration
# Copy this to .env for production use

# Database
DATABASE_URL=sqlite:///data/aec_ai_news.db

# Scout Agent Settings
SCOUT_SCRAPING_INTERVAL=30
SCOUT_MAX_CONCURRENT=5
SCOUT_MAX_ARTICLES_PER_SOURCE=10
SCOUT_CONTENT_FRESHNESS_HOURS=48
SCOUT_RATE_LIMIT_DELAY=2.0

# RSS Feed Sources (comma-separated)
SCOUT_RSS_FEEDS=https://www.archdaily.com/rss/,https://www.constructiondive.com/feeds/,https://feeds.feedburner.com/oreilly/radar

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/scout_agent.log

# MCP Server
MCP_HOST=127.0.0.1
MCP_PORT=8001
'''
    
    with open('config_sample.env', 'w') as f:
        f.write(config_content)
    
    print("Created sample configuration: config_sample.env")

def main():
    """Main setup function"""
    print("=" * 50)
    print("AEC AI News Scout Agent Setup")
    print("=" * 50)
    
    # Step 1: Create directories
    print("\n1. Setting up directory structure...")
    setup_directory_structure()
    
    # Step 2: Install dependencies
    print("\n2. Installing dependencies...")
    if not install_dependencies():
        print("Setup failed: Could not install dependencies")
        return False
    
    # Step 3: Verify installation
    print("\n3. Verifying installation...")
    if not verify_installation():
        print("Setup failed: Could not verify Scout Agent")
        return False
    
    # Step 4: Run test
    print("\n4. Running Scout Agent test...")
    test_success = asyncio.run(run_scout_test())
    if not test_success:
        print("Warning: Scout Agent test failed, but installation may still work")
    
    # Step 5: Create sample config
    print("\n5. Creating sample configuration...")
    create_sample_config()
    
    print("\n" + "=" * 50)
    print("Scout Agent Setup Complete!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Copy config_sample.env to .env and customize")
    print("2. Run: python enhanced-mcp-server.py")
    print("3. Test with MCP tools or run test_scout.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)