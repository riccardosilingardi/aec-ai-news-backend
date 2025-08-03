"""
Pytest Configuration and Shared Fixtures
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path

from ..core.config import SystemConfig
from ..core.database import DatabaseManager
from ..multi_agent_system import MultiAgentSystem

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def temp_database():
    """Create a temporary database for testing"""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test.db"
    
    config = SystemConfig(
        database_url=f"sqlite:///{db_path}",
        environment="test"
    )
    
    db_manager = DatabaseManager(config)
    await db_manager.initialize()
    
    yield db_manager
    
    await db_manager.close()
    shutil.rmtree(temp_dir)

@pytest.fixture
async def test_system():
    """Create a test multi-agent system"""
    config = SystemConfig(
        database_url="sqlite:///:memory:",
        environment="test",
        log_level="DEBUG"
    )
    
    system = MultiAgentSystem(config)
    await system.initialize()
    
    yield system
    
    await system.shutdown()

@pytest.fixture
def sample_content():
    """Sample content for testing"""
    return [
        {
            "title": "Sustainable Architecture Innovations",
            "content": "Revolutionary green building technologies are transforming the construction industry...",
            "url": "https://example.com/sustainable-arch",
            "source": "Architecture Today",
            "published": "2024-01-15T10:00:00Z"
        },
        {
            "title": "AI in Construction Management", 
            "content": "Artificial intelligence is optimizing construction workflows and project management...",
            "url": "https://example.com/ai-construction",
            "source": "Construction Tech Weekly",
            "published": "2024-01-14T15:30:00Z"
        },
        {
            "title": "Smart Building Technologies",
            "content": "Internet of Things sensors and smart systems are creating intelligent buildings...",
            "url": "https://example.com/smart-buildings",
            "source": "Engineering News",
            "published": "2024-01-13T09:15:00Z"
        }
    ]

@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return {
        "scout": {
            "rss_feeds": ["https://test.example.com/rss"],
            "scraping_interval": 300,
            "max_articles": 10
        },
        "curator": {
            "quality_threshold": 0.7,
            "relevance_threshold": 0.8,
            "batch_size": 5
        },
        "writer": {
            "newsletter_template": "test_template",
            "max_articles": 8,
            "generation_timeout": 120
        },
        "orchestrator": {
            "max_concurrent_tasks": 3,
            "task_timeout": 180
        },
        "monitor": {
            "monitoring_interval": 60,
            "alert_thresholds": {
                "cpu_threshold": 80,
                "memory_threshold": 85,
                "disk_threshold": 90
            }
        }
    }