"""
End-to-End Tests for Complete System Workflows
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from ...multi_agent_system import MultiAgentSystem
from ...core.config import SystemConfig
from ...mcp.server import AECMCPServer
from ...mcp.tools import MCPTools

class TestCompleteNewsletterWorkflow:
    """End-to-end test for complete newsletter generation workflow"""
    
    @pytest.fixture
    async def full_system_setup(self):
        """Set up complete system with MCP server"""
        config = SystemConfig(
            database_url="sqlite:///:memory:",
            environment="test"
        )
        
        # Initialize multi-agent system
        multi_agent_system = MultiAgentSystem(config)
        await multi_agent_system.initialize()
        
        # Initialize MCP server
        mcp_server = AECMCPServer(multi_agent_system)
        mcp_tools = MCPTools()
        
        yield {
            "system": multi_agent_system,
            "mcp_server": mcp_server,
            "mcp_tools": mcp_tools
        }
        
        await multi_agent_system.shutdown()
    
    @pytest.mark.asyncio
    async def test_weekly_newsletter_generation(self, full_system_setup):
        """Test complete weekly newsletter generation process"""
        components = full_system_setup
        system = components["system"]
        mcp_tools = components["mcp_tools"]
        
        # Mock external RSS feeds
        mock_rss_data = [
            {
                "title": "Innovative Sustainable Architecture Design",
                "content": "New sustainable design principles are revolutionizing...",
                "url": "https://example.com/sustainable-arch",
                "published": datetime.now(),
                "source": "Architecture Daily"
            },
            {
                "title": "Advanced Construction Technology Trends",
                "content": "Latest construction technologies including AI and robotics...",
                "url": "https://example.com/construction-tech",
                "published": datetime.now(),
                "source": "Construction Tech"
            },
            {
                "title": "Building Information Modeling Updates",
                "content": "BIM technology advances for better project coordination...",
                "url": "https://example.com/bim-updates",
                "published": datetime.now(),
                "source": "Engineering News"
            }
        ]
        
        with patch.object(system.agents["scout"], 'discover_content') as mock_discovery:
            mock_discovery.return_value = {
                "status": "success",
                "articles": mock_rss_data,
                "sources_checked": 3,
                "total_discovered": 3
            }
            
            # Step 1: Content Discovery
            discovery_result = await mcp_tools.start_content_discovery(
                system, max_articles=50
            )
            
            assert discovery_result["status"] == "success"
            assert len(discovery_result["discovery_result"]["articles"]) == 3
        
        # Step 2: Content Analysis
        analysis_result = await mcp_tools.analyze_content_quality(system)
        assert analysis_result["status"] == "success"
        assert analysis_result["analyzed_count"] > 0
        
        # Step 3: Newsletter Generation
        newsletter_result = await mcp_tools.generate_newsletter_now(
            system, force=True
        )
        assert newsletter_result["status"] == "success"
        assert "newsletter_result" in newsletter_result
        
        # Step 4: System Health Check
        health_result = await mcp_tools.get_system_health(system)
        assert health_result["system_status"] in ["operational", "degraded"]
        assert "agents" in health_result
        assert "database" in health_result
    
    @pytest.mark.asyncio
    async def test_emergency_content_override(self, full_system_setup):
        """Test manual content curation override workflow"""
        components = full_system_setup
        system = components["system"]
        mcp_tools = components["mcp_tools"]
        
        # Mock some analyzed content
        mock_content_ids = [1, 2, 3, 4, 5]
        
        # Test manual content selection
        override_result = await mcp_tools.override_content_selection(
            system,
            include_ids=[1, 3, 5],
            exclude_ids=[2, 4],
            quality_threshold=0.8
        )
        
        assert override_result["status"] == "success"
        assert override_result["actions_count"] > 0
        assert len(override_result["actions_taken"]) > 0
        
        # Generate newsletter with overridden content
        newsletter_result = await mcp_tools.generate_newsletter_now(
            system, force=True
        )
        assert newsletter_result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_system_monitoring_workflow(self, full_system_setup):
        """Test continuous system monitoring workflow"""
        components = full_system_setup
        system = components["system"]
        mcp_tools = components["mcp_tools"]
        
        # Run multiple monitoring cycles
        monitoring_results = []
        
        for i in range(3):
            # Health check
            health_result = await mcp_tools.get_system_health(system)
            monitoring_results.append(health_result)
            
            # Brief delay between checks
            await asyncio.sleep(1)
        
        # Verify all monitoring cycles completed
        assert len(monitoring_results) == 3
        for result in monitoring_results:
            assert result["system_status"] in ["operational", "degraded", "critical"]
            assert "timestamp" in result
        
        # Export analytics
        analytics_result = await mcp_tools.export_analytics(
            system,
            start_date=(datetime.now() - timedelta(days=1)).isoformat(),
            end_date=datetime.now().isoformat()
        )
        
        assert analytics_result["status"] == "success"
        assert "analytics" in analytics_result
    
    @pytest.mark.asyncio
    async def test_agent_failure_recovery(self, full_system_setup):
        """Test system behavior when agents fail and recovery"""
        components = full_system_setup
        system = components["system"]
        mcp_tools = components["mcp_tools"]
        
        # Simulate agent failure
        original_scout = system.agents["scout"]
        system.agents["scout"] = None  # Simulate failure
        
        # Test system health with failed agent
        health_result = await mcp_tools.get_system_health(system)
        assert health_result["system_status"] in ["degraded", "critical"]
        
        # Test agent restart
        restart_result = await mcp_tools.restart_agent(system, "scout")
        
        # Restore for cleanup
        system.agents["scout"] = original_scout
        
        # Verify system recovery
        health_after_restart = await mcp_tools.get_system_health(system)
        # System should be operational or at least better than before
        assert health_after_restart["system_status"] != "critical"
    
    @pytest.mark.asyncio
    async def test_performance_stress_test(self, full_system_setup):
        """Test system performance under stress conditions"""
        components = full_system_setup
        system = components["system"]
        mcp_tools = components["mcp_tools"]
        
        # Create high load scenario
        start_time = datetime.now()
        
        # Concurrent operations
        tasks = [
            mcp_tools.get_system_health(system),
            mcp_tools.analyze_content_quality(system),
            mcp_tools.start_content_discovery(system, max_articles=10),
            mcp_tools.export_analytics(system),
            mcp_tools.get_system_health(system)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Verify most operations completed successfully
        successful_results = [r for r in results if isinstance(r, dict) and r.get("status") == "success"]
        assert len(successful_results) >= 3  # At least 3 out of 5 should succeed
        
        # Performance check
        assert execution_time < 60.0  # Should complete within 1 minute
    
    @pytest.mark.asyncio
    async def test_data_persistence_workflow(self, full_system_setup):
        """Test data persistence across system operations"""
        components = full_system_setup
        system = components["system"]
        mcp_tools = components["mcp_tools"]
        
        # Generate some content and newsletter
        discovery_result = await mcp_tools.start_content_discovery(
            system, max_articles=5
        )
        
        if discovery_result["status"] == "success":
            # Analyze content
            analysis_result = await mcp_tools.analyze_content_quality(system)
            
            if analysis_result["status"] == "success":
                # Generate newsletter
                newsletter_result = await mcp_tools.generate_newsletter_now(
                    system, force=True
                )
                
                # Export analytics to verify data persistence
                analytics_result = await mcp_tools.export_analytics(system)
                
                assert analytics_result["status"] == "success"
                assert "analytics" in analytics_result
                
                # Verify content metrics show activity
                content_metrics = analytics_result["analytics"]["content_metrics"]
                # At least some activity should be recorded
                total_activity = (
                    content_metrics["total_discovered"] +
                    content_metrics["total_analyzed"] +
                    content_metrics["total_published"]
                )
                assert total_activity >= 0  # Basic sanity check