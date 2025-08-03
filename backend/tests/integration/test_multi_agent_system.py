"""
Integration Tests for Multi-Agent System
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from ...multi_agent_system import MultiAgentSystem
from ...core.config import SystemConfig
from ...core.database import DatabaseManager
from ...core.agent_base import AgentTask, TaskPriority

class TestMultiAgentSystemIntegration:
    """Integration tests for the complete multi-agent system"""
    
    @pytest.fixture
    async def system_setup(self):
        """Set up test multi-agent system"""
        config = SystemConfig(
            database_url="sqlite:///:memory:",
            environment="test"
        )
        
        system = MultiAgentSystem(config)
        await system.initialize()
        
        yield system
        
        await system.shutdown()
    
    @pytest.mark.asyncio
    async def test_end_to_end_content_pipeline(self, system_setup):
        """Test complete content discovery to newsletter pipeline"""
        system = system_setup
        
        # Mock external dependencies
        system.agents["scout"].rss_parser = AsyncMock()
        system.agents["scout"].rss_parser.parse_feed = AsyncMock(return_value=[
            {
                "title": "Revolutionary BIM Technology",
                "url": "https://example.com/bim-tech",
                "content": "Advanced Building Information Modeling systems...",
                "published": datetime.now()
            }
        ])
        
        # Step 1: Content Discovery
        discovery_task = AgentTask(
            task_id="integration_test_001",
            agent_type="scout",
            priority=TaskPriority.HIGH,
            data={"type": "rss_discovery", "max_articles": 1},
            created_at=datetime.now()
        )
        
        discovery_result = await system.execute_task(discovery_task)
        assert discovery_result["status"] == "success"
        
        # Step 2: Content Analysis
        content_id = discovery_result["articles"][0]["id"]
        analysis_task = AgentTask(
            task_id="integration_test_002",
            agent_type="curator",
            priority=TaskPriority.MEDIUM,
            data={"type": "analyze_content", "content_id": content_id},
            created_at=datetime.now()
        )
        
        analysis_result = await system.execute_task(analysis_task)
        assert analysis_result["status"] == "success"
        assert "quality_score" in analysis_result
        
        # Step 3: Newsletter Generation (if quality is good)
        if analysis_result["quality_score"] > 0.7:
            newsletter_task = AgentTask(
                task_id="integration_test_003",
                agent_type="writer",
                priority=TaskPriority.HIGH,
                data={"type": "generate_newsletter"},
                created_at=datetime.now()
            )
            
            newsletter_result = await system.execute_task(newsletter_task)
            assert newsletter_result["status"] == "success"
            assert "newsletter" in newsletter_result
    
    @pytest.mark.asyncio
    async def test_agent_communication_flow(self, system_setup):
        """Test inter-agent communication and task coordination"""
        system = system_setup
        
        # Create a workflow that requires multiple agents
        workflow_tasks = [
            AgentTask("workflow_001", "scout", TaskPriority.HIGH, 
                     {"type": "comprehensive_discovery"}, datetime.now()),
            AgentTask("workflow_002", "curator", TaskPriority.MEDIUM,
                     {"type": "bulk_analysis"}, datetime.now()),
            AgentTask("workflow_003", "monitor", TaskPriority.LOW,
                     {"type": "health_check"}, datetime.now())
        ]
        
        # Execute tasks and verify coordination
        results = []
        for task in workflow_tasks:
            result = await system.execute_task(task)
            results.append(result)
        
        # Verify all tasks completed
        for result in results:
            assert "status" in result
            assert result["status"] in ["success", "error"]
    
    @pytest.mark.asyncio
    async def test_system_resilience(self, system_setup):
        """Test system behavior under failure conditions"""
        system = system_setup
        
        # Test with invalid task
        invalid_task = AgentTask(
            task_id="invalid_test_001",
            agent_type="nonexistent",
            priority=TaskPriority.HIGH,
            data={"type": "invalid_operation"},
            created_at=datetime.now()
        )
        
        result = await system.execute_task(invalid_task)
        assert result["status"] == "error"
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self, system_setup):
        """Test system performance with multiple concurrent tasks"""
        system = system_setup
        
        # Create multiple concurrent tasks
        tasks = []
        for i in range(10):
            task = AgentTask(
                task_id=f"load_test_{i:03d}",
                agent_type="monitor",
                priority=TaskPriority.LOW,
                data={"type": "health_check"},
                created_at=datetime.now()
            )
            tasks.append(task)
        
        # Execute tasks concurrently
        start_time = datetime.now()
        results = await asyncio.gather(*[
            system.execute_task(task) for task in tasks
        ])
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Verify all tasks completed
        assert len(results) == 10
        for result in results:
            assert result["status"] in ["success", "error"]
        
        # Performance assertion (should complete within reasonable time)
        assert execution_time < 30.0  # 30 seconds max for 10 health checks
    
    @pytest.mark.asyncio
    async def test_database_integration(self, system_setup):
        """Test database operations across the system"""
        system = system_setup
        
        # Test content storage and retrieval
        test_content = {
            "title": "Test Article",
            "content": "Test content for integration testing",
            "source_url": "https://test.example.com",
            "quality_score": 0.85
        }
        
        # Store content via scout agent
        scout_task = AgentTask(
            task_id="db_test_001",
            agent_type="scout",
            priority=TaskPriority.MEDIUM,
            data={"type": "store_content", "content": test_content},
            created_at=datetime.now()
        )
        
        result = await system.execute_task(scout_task)
        assert result["status"] == "success"
        
        # Retrieve content via curator agent
        curator_task = AgentTask(
            task_id="db_test_002",
            agent_type="curator",
            priority=TaskPriority.MEDIUM,
            data={"type": "get_content", "content_id": result["content_id"]},
            created_at=datetime.now()
        )
        
        retrieval_result = await system.execute_task(curator_task)
        assert retrieval_result["status"] == "success"
        assert retrieval_result["content"]["title"] == test_content["title"]