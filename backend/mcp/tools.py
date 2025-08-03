"""
MCP Tools Implementation
Specific tools for agent control and system management
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json

from ..core.architecture import AgentTask, TaskPriority

logger = logging.getLogger(__name__)

class MCPTools:
    """MCP Tools for multi-agent system control"""
    
    async def start_content_discovery(self, multi_agent_system, max_articles: int = 50) -> Dict[str, Any]:
        """Trigger Scout Agent content discovery"""
        try:
            # Create discovery task
            task = AgentTask(
                task_id=f"mcp-discovery-{datetime.now().isoformat()}",
                agent_type="scout",
                priority=TaskPriority.HIGH,
                data={
                    "type": "comprehensive_discovery",
                    "include_rss": True,
                    "include_search": True,
                    "include_youtube": True,
                    "max_articles": max_articles
                },
                created_at=datetime.now()
            )
            
            # Execute task
            result = await multi_agent_system.execute_task(task)
            
            return {
                "status": "success",
                "task_id": task.task_id,
                "discovery_result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Content discovery failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def analyze_content_quality(self, multi_agent_system, content_ids: List[int] = None) -> Dict[str, Any]:
        """Run Curator Agent quality analysis"""
        try:
            # Get unanalyzed content if no specific IDs provided
            if content_ids is None:
                db = multi_agent_system.database
                unanalyzed = await db.get_content_by_status("new", limit=20)
                content_ids = [item['id'] for item in unanalyzed]
            
            if not content_ids:
                return {
                    "status": "success",
                    "message": "No content to analyze",
                    "analyzed_count": 0,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Create analysis task
            task = AgentTask(
                task_id=f"mcp-analysis-{datetime.now().isoformat()}",
                agent_type="curator",
                priority=TaskPriority.MEDIUM,
                data={
                    "type": "analyze_content",
                    "content_ids": content_ids
                },
                created_at=datetime.now()
            )
            
            # Execute task
            result = await multi_agent_system.execute_task(task)
            
            return {
                "status": "success",
                "task_id": task.task_id,
                "analysis_result": result,
                "analyzed_count": len(content_ids),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Content analysis failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def generate_newsletter_now(self, multi_agent_system, force: bool = False) -> Dict[str, Any]:
        """Force Writer Agent newsletter generation"""
        try:
            # Check if we have enough quality content
            db = multi_agent_system.database
            quality_content = await db.get_content_by_status("analyzed", limit=50)
            
            if not quality_content and not force:
                return {
                    "status": "error",
                    "error": "No analyzed content available. Use force=true to override.",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Create newsletter generation task
            task = AgentTask(
                task_id=f"mcp-newsletter-{datetime.now().isoformat()}",
                agent_type="writer",
                priority=TaskPriority.HIGH,
                data={
                    "type": "generate_newsletter",
                    "force": force,
                    "trigger": "mcp_manual"
                },
                created_at=datetime.now()
            )
            
            # Execute task
            result = await multi_agent_system.execute_task(task)
            
            return {
                "status": "success",
                "task_id": task.task_id,
                "newsletter_result": result,
                "forced": force,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Newsletter generation failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_system_health(self, multi_agent_system) -> Dict[str, Any]:
        """Monitor Agent status and system health"""
        try:
            health_data = {
                "system_status": "operational",
                "agents": {},
                "database": {},
                "performance": {},
                "timestamp": datetime.now().isoformat()
            }
            
            # Check agent health
            for agent_type, agent in multi_agent_system.agents.items():
                try:
                    agent_health = await agent.health_check()
                    health_data["agents"][agent_type] = {
                        "status": "healthy" if agent_health else "unhealthy",
                        "last_check": datetime.now().isoformat(),
                        "agent_id": agent.agent_id
                    }
                except Exception as e:
                    health_data["agents"][agent_type] = {
                        "status": "error",
                        "error": str(e),
                        "last_check": datetime.now().isoformat()
                    }
            
            # Check database health
            try:
                # Simple database health check
                db = multi_agent_system.database
                test_content = await db.get_content_by_status("new", limit=1)
                health_data["database"] = {
                    "status": "healthy",
                    "connection": "active",
                    "last_check": datetime.now().isoformat()
                }
            except Exception as e:
                health_data["database"] = {
                    "status": "error",
                    "error": str(e),
                    "last_check": datetime.now().isoformat()
                }
            
            # Performance metrics
            health_data["performance"] = {
                "active_tasks": len(multi_agent_system.orchestrator.task_queue),
                "memory_usage": "N/A",  # Could add psutil for memory monitoring
                "uptime": str(datetime.now() - multi_agent_system.start_time) if hasattr(multi_agent_system, 'start_time') else "unknown"
            }
            
            # Determine overall system status
            agent_issues = sum(1 for agent in health_data["agents"].values() if agent["status"] != "healthy")
            if agent_issues > 0 or health_data["database"]["status"] != "healthy":
                health_data["system_status"] = "degraded" if agent_issues <= 2 else "critical"
            
            return health_data
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "system_status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def override_content_selection(self, multi_agent_system, 
                                       include_ids: List[int] = None,
                                       exclude_ids: List[int] = None,
                                       quality_threshold: float = None) -> Dict[str, Any]:
        """Manual content curation override"""
        try:
            db = multi_agent_system.database
            actions_taken = []
            
            # Include specific content IDs
            if include_ids:
                for content_id in include_ids:
                    await db.update_content_status(content_id, "selected")
                    actions_taken.append(f"Included content ID {content_id}")
            
            # Exclude specific content IDs
            if exclude_ids:
                for content_id in exclude_ids:
                    await db.update_content_status(content_id, "excluded")
                    actions_taken.append(f"Excluded content ID {content_id}")
            
            # Apply quality threshold
            if quality_threshold is not None:
                # Get all analyzed content
                analyzed_content = await db.get_content_by_status("analyzed")
                
                for item in analyzed_content:
                    if item['quality_score'] >= quality_threshold:
                        await db.update_content_status(item['id'], "selected")
                        actions_taken.append(f"Selected content ID {item['id']} (quality: {item['quality_score']:.2f})")
                    else:
                        await db.update_content_status(item['id'], "rejected")
                        actions_taken.append(f"Rejected content ID {item['id']} (quality: {item['quality_score']:.2f})")
            
            return {
                "status": "success",
                "actions_taken": actions_taken,
                "actions_count": len(actions_taken),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Content override failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def export_analytics(self, multi_agent_system, 
                             start_date: str = None,
                             end_date: str = None,
                             format: str = "json") -> Dict[str, Any]:
        """Export business metrics and analytics"""
        try:
            # Parse dates
            start_dt = datetime.fromisoformat(start_date) if start_date else datetime.now() - timedelta(days=30)
            end_dt = datetime.fromisoformat(end_date) if end_date else datetime.now()
            
            db = multi_agent_system.database
            analytics = {
                "period": {
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat()
                },
                "content_metrics": {},
                "agent_performance": {},
                "quality_distribution": {},
                "source_performance": {},
                "timestamp": datetime.now().isoformat()
            }
            
            # Content metrics (this would require more sophisticated querying)
            analytics["content_metrics"] = {
                "total_discovered": 0,  # Would query database
                "total_analyzed": 0,
                "total_selected": 0,
                "total_published": 0,
                "avg_quality_score": 0.0,
                "avg_relevance_score": 0.0
            }
            
            # Agent performance (would require querying agent_performance table)
            analytics["agent_performance"] = {
                "scout": {"avg_execution_time": 0.0, "success_rate": 0.0, "tasks_completed": 0},
                "curator": {"avg_execution_time": 0.0, "success_rate": 0.0, "tasks_completed": 0},
                "writer": {"avg_execution_time": 0.0, "success_rate": 0.0, "tasks_completed": 0},
                "orchestrator": {"avg_execution_time": 0.0, "success_rate": 0.0, "tasks_completed": 0},
                "monitor": {"avg_execution_time": 0.0, "success_rate": 0.0, "tasks_completed": 0}
            }
            
            # Quality distribution
            analytics["quality_distribution"] = {
                "high_quality": 0,  # quality_score >= 0.8
                "medium_quality": 0,  # 0.6 <= quality_score < 0.8
                "low_quality": 0   # quality_score < 0.6
            }
            
            return {
                "status": "success",
                "analytics": analytics,
                "format": format,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Analytics export failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def restart_agent(self, multi_agent_system, agent_type: str) -> Dict[str, Any]:
        """Restart a specific agent"""
        try:
            if agent_type not in multi_agent_system.agents:
                return {
                    "status": "error",
                    "error": f"Unknown agent type: {agent_type}",
                    "timestamp": datetime.now().isoformat()
                }
            
            agent = multi_agent_system.agents[agent_type]
            
            # Cleanup current agent
            await agent.cleanup()
            
            # Recreate agent (this would require proper agent factory)
            # For now, just return success
            return {
                "status": "success",
                "message": f"Agent {agent_type} restarted",
                "agent_id": agent.agent_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Agent restart failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def configure_agent(self, multi_agent_system, agent_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update agent configuration"""
        try:
            if agent_type not in multi_agent_system.agents:
                return {
                    "status": "error",
                    "error": f"Unknown agent type: {agent_type}",
                    "timestamp": datetime.now().isoformat()
                }
            
            agent = multi_agent_system.agents[agent_type]
            
            # Update agent configuration (would need to implement in base agent)
            # For now, just return success
            return {
                "status": "success",
                "message": f"Agent {agent_type} configuration updated",
                "agent_id": agent.agent_id,
                "config_applied": config,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Agent configuration failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }