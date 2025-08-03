"""
Unit Tests for Individual Agents
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from ...agents.scout.agent import ScoutAgent
from ...agents.curator.agent import CuratorAgent
from ...agents.writer.agent import WriterAgent
from ...agents.orchestrator.agent import OrchestratorAgent
from ...agents.monitor.agent import MonitorAgent
from ...core.agent_base import AgentTask, TaskPriority

class TestScoutAgent:
    """Unit tests for Scout Agent"""
    
    @pytest.fixture
    def scout_agent(self):
        return ScoutAgent("test_scout_001", {
            "rss_feeds": ["https://example.com/rss"],
            "max_articles": 5
        })
    
    @pytest.mark.asyncio
    async def test_scout_rss_discovery(self, scout_agent):
        """Test RSS feed discovery functionality"""
        task = AgentTask(
            task_id="test_rss_001",
            agent_type="scout",
            priority=TaskPriority.MEDIUM,
            data={"type": "rss_discovery", "max_articles": 3},
            created_at=datetime.now()
        )
        
        # Mock RSS feed response
        scout_agent.rss_parser = AsyncMock()
        scout_agent.rss_parser.parse_feed = AsyncMock(return_value=[
            {"title": "Test Article 1", "url": "https://example.com/1"},
            {"title": "Test Article 2", "url": "https://example.com/2"}
        ])
        
        result = await scout_agent.process_task(task)
        
        assert result["status"] == "success"
        assert len(result["articles"]) == 2
        assert result["articles"][0]["title"] == "Test Article 1"
    
    @pytest.mark.asyncio
    async def test_scout_web_scraping(self, scout_agent):
        """Test web scraping functionality"""
        task = AgentTask(
            task_id="test_scrape_001",
            agent_type="scout",
            priority=TaskPriority.HIGH,
            data={
                "type": "scrape_content",
                "urls": ["https://example.com/article1"]
            },
            created_at=datetime.now()
        )
        
        # Mock scraper response
        scout_agent.content_scraper = AsyncMock()
        scout_agent.content_scraper.scrape_url = AsyncMock(return_value={
            "title": "Scraped Article",
            "content": "This is scraped content",
            "url": "https://example.com/article1"
        })
        
        result = await scout_agent.process_task(task)
        
        assert result["status"] == "success"
        assert result["content"]["title"] == "Scraped Article"

class TestCuratorAgent:
    """Unit tests for Curator Agent"""
    
    @pytest.fixture
    def curator_agent(self):
        return CuratorAgent("test_curator_001", {
            "quality_threshold": 0.7,
            "relevance_threshold": 0.8
        })
    
    @pytest.mark.asyncio
    async def test_content_analysis(self, curator_agent):
        """Test content quality analysis"""
        task = AgentTask(
            task_id="test_analysis_001",
            agent_type="curator",
            priority=TaskPriority.MEDIUM,
            data={
                "type": "analyze_content",
                "content": {
                    "id": 1,
                    "title": "Innovative Construction Technology",
                    "content": "Advanced BIM technology revolutionizes construction...",
                    "source": "construction-tech.com"
                }
            },
            created_at=datetime.now()
        )
        
        result = await curator_agent.process_task(task)
        
        assert result["status"] == "success"
        assert "quality_score" in result
        assert "relevance_score" in result
        assert result["quality_score"] >= 0.0
        assert result["quality_score"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_content_categorization(self, curator_agent):
        """Test content categorization"""
        task = AgentTask(
            task_id="test_category_001",
            agent_type="curator",
            priority=TaskPriority.LOW,
            data={
                "type": "categorize_content",
                "content": {
                    "title": "Sustainable Architecture Practices",
                    "content": "Green building standards and LEED certification..."
                }
            },
            created_at=datetime.now()
        )
        
        result = await curator_agent.process_task(task)
        
        assert result["status"] == "success"
        assert "categories" in result
        assert len(result["categories"]) > 0

class TestWriterAgent:
    """Unit tests for Writer Agent"""
    
    @pytest.fixture
    def writer_agent(self):
        return WriterAgent("test_writer_001", {
            "newsletter_template": "standard",
            "max_articles": 8
        })
    
    @pytest.mark.asyncio
    async def test_newsletter_generation(self, writer_agent):
        """Test newsletter generation"""
        task = AgentTask(
            task_id="test_newsletter_001",
            agent_type="writer",
            priority=TaskPriority.HIGH,
            data={
                "type": "generate_newsletter",
                "selected_content": [
                    {
                        "id": 1,
                        "title": "Article 1",
                        "summary": "Summary 1",
                        "quality_score": 0.9
                    },
                    {
                        "id": 2,
                        "title": "Article 2", 
                        "summary": "Summary 2",
                        "quality_score": 0.8
                    }
                ]
            },
            created_at=datetime.now()
        )
        
        result = await writer_agent.process_task(task)
        
        assert result["status"] == "success"
        assert "newsletter" in result
        assert "subject" in result["newsletter"]
        assert "html_content" in result["newsletter"]
        assert len(result["newsletter"]["html_content"]) > 0

class TestOrchestratorAgent:
    """Unit tests for Orchestrator Agent"""
    
    @pytest.fixture
    def orchestrator_agent(self):
        return OrchestratorAgent("test_orchestrator_001", {
            "max_concurrent_tasks": 5,
            "task_timeout": 300
        })
    
    @pytest.mark.asyncio
    async def test_task_prioritization(self, orchestrator_agent):
        """Test task prioritization logic"""
        tasks = [
            AgentTask("task1", "scout", TaskPriority.LOW, {}, datetime.now()),
            AgentTask("task2", "curator", TaskPriority.HIGH, {}, datetime.now()),
            AgentTask("task3", "writer", TaskPriority.MEDIUM, {}, datetime.now())
        ]
        
        for task in tasks:
            await orchestrator_agent.add_task(task)
        
        # High priority task should be processed first
        next_task = await orchestrator_agent.get_next_task()
        assert next_task.task_id == "task2"
        assert next_task.priority == TaskPriority.HIGH

class TestMonitorAgent:
    """Unit tests for Monitor Agent"""
    
    @pytest.fixture
    def monitor_agent(self):
        return MonitorAgent("test_monitor_001", {
            "monitoring_interval": 60,
            "alert_thresholds": {
                "cpu_threshold": 80,
                "memory_threshold": 85
            }
        })
    
    @pytest.mark.asyncio
    async def test_health_check(self, monitor_agent):
        """Test system health check"""
        task = AgentTask(
            task_id="test_health_001",
            agent_type="monitor",
            priority=TaskPriority.HIGH,
            data={"type": "health_check"},
            created_at=datetime.now()
        )
        
        result = await monitor_agent.process_task(task)
        
        assert result["overall_status"] in ["healthy", "warning", "critical", "error"]
        assert "components" in result
        assert "metrics" in result
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self, monitor_agent):
        """Test system metrics collection"""
        task = AgentTask(
            task_id="test_metrics_001",
            agent_type="monitor",
            priority=TaskPriority.MEDIUM,
            data={"type": "collect_metrics"},
            created_at=datetime.now()
        )
        
        result = await monitor_agent.process_task(task)
        
        assert "system" in result
        assert "application" in result
        assert "business" in result
        assert "timestamp" in result