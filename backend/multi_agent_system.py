"""
Multi-Agent System Coordinator
Main system coordinator for all agents as specified in architecture
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Import base classes and agents
import sys
import os
# Add parent directory to path for multi_agent_architecture
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.dirname(__file__))

# Try importing from different paths
try:
    from multi_agent_architecture import BaseAgent, AgentTask, AgentStatus
except ImportError:
    # Try from parent directory
    import importlib.util
    arch_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'multi-agent-architecture.py')
    spec = importlib.util.spec_from_file_location("multi_agent_architecture", arch_path)
    arch_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(arch_module)
    BaseAgent = arch_module.BaseAgent
    AgentTask = arch_module.AgentTask
    AgentStatus = arch_module.AgentStatus

# Import agent implementations
from agents.scout.agent import ScoutAgent
from agents.orchestrator.agent import OrchestratorAgent

logger = logging.getLogger(__name__)

@dataclass
class SystemConfig:
    """System-wide configuration"""
    scout_config: Dict[str, Any]
    orchestrator_config: Dict[str, Any]
    curator_config: Dict[str, Any] = None
    writer_config: Dict[str, Any] = None
    monitor_config: Dict[str, Any] = None
    
    # System settings
    startup_timeout: int = 60  # seconds
    shutdown_timeout: int = 30  # seconds
    auto_start_scheduler: bool = True

class MultiAgentSystem:
    """
    Main system coordinator for all agents
    
    Implements the MultiAgentSystem class from multi-agent-architecture.py
    """
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.agents: Dict[str, BaseAgent] = {}
        self.task_queue: List[AgentTask] = []
        self.system_status = AgentStatus.IDLE
        
        # System state
        self.is_initialized = False
        self.is_running = False
        self.startup_time = None
        
        logger.info("MultiAgentSystem initialized")
    
    async def initialize_agents(self) -> Dict[str, Any]:
        """
        Initialize all agents with configuration
        """
        try:
            logger.info("Initializing agents...")
            
            # Initialize Scout Agent
            if self.config.scout_config:
                scout_agent = ScoutAgent("scout-001", self.config.scout_config)
                self.agents["scout"] = scout_agent
                logger.info("Scout Agent initialized")
            
            # Initialize Orchestrator Agent
            if self.config.orchestrator_config:
                orchestrator_agent = OrchestratorAgent("orchestrator-001", self.config.orchestrator_config)
                self.agents["orchestrator"] = orchestrator_agent
                logger.info("Orchestrator Agent initialized")
            
            # Register agents with orchestrator
            if "orchestrator" in self.agents:
                orchestrator = self.agents["orchestrator"]
                
                for agent_id, agent in self.agents.items():
                    if agent_id != "orchestrator":  # Don't register orchestrator with itself
                        registration_task = AgentTask(
                            task_id=f"register-{agent_id}",
                            agent_type="orchestrator",
                            priority=1,
                            data={
                                "type": "register_agent",
                                "agent_id": agent_id,
                                "agent_type": agent_id,
                                "agent_instance": agent
                            },
                            created_at=datetime.now()
                        )
                        
                        result = await orchestrator.process_task(registration_task)
                        if result.get("status") == "success":
                            logger.info(f"Registered {agent_id} with orchestrator")
                        else:
                            logger.warning(f"Failed to register {agent_id}: {result.get('message')}")
            
            # TODO: Initialize other agents (Curator, Writer, Monitor) when implemented
            
            self.is_initialized = True
            
            return {
                "status": "success",
                "agents_initialized": list(self.agents.keys()),
                "total_agents": len(self.agents),
                "initialization_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Agent initialization failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "agents_initialized": list(self.agents.keys())
            }
    
    async def start_system(self) -> Dict[str, Any]:
        """
        Start the multi-agent system
        """
        try:
            if not self.is_initialized:
                init_result = await self.initialize_agents()
                if init_result.get("status") != "success":
                    return {
                        "status": "error",
                        "message": "Failed to initialize agents",
                        "details": init_result
                    }
            
            logger.info("Starting multi-agent system...")
            
            # Start orchestrator scheduler if configured
            if self.config.auto_start_scheduler and "orchestrator" in self.agents:
                start_task = AgentTask(
                    task_id="start-scheduler",
                    agent_type="orchestrator", 
                    priority=1,
                    data={"type": "start_scheduler"},
                    created_at=datetime.now()
                )
                
                result = await self.agents["orchestrator"].process_task(start_task)
                if result.get("status") == "success":
                    logger.info("Orchestrator scheduler started")
                else:
                    logger.warning(f"Failed to start scheduler: {result.get('message')}")
            
            # Trigger initial content discovery
            if "orchestrator" in self.agents:
                discovery_task = AgentTask(
                    task_id="initial-discovery",
                    agent_type="orchestrator",
                    priority=1, 
                    data={"type": "schedule_discovery"},
                    created_at=datetime.now()
                )
                
                result = await self.agents["orchestrator"].process_task(discovery_task)
                logger.info(f"Initial discovery scheduled: {result.get('status')}")
            
            # Start health monitoring
            asyncio.create_task(self._health_monitoring_loop())
            
            self.is_running = True
            self.startup_time = datetime.now()
            self.system_status = AgentStatus.WORKING
            
            logger.info("Multi-agent system started successfully")
            
            return {
                "status": "success",
                "startup_time": self.startup_time.isoformat(),
                "active_agents": list(self.agents.keys()),
                "scheduler_running": "orchestrator" in self.agents,
                "system_status": self.system_status.value
            }
            
        except Exception as e:
            logger.error(f"System startup failed: {e}")
            self.system_status = AgentStatus.ERROR
            return {
                "status": "error",
                "message": str(e),
                "system_status": self.system_status.value
            }
    
    async def stop_system(self) -> Dict[str, Any]:
        """
        Graceful system shutdown
        """
        try:
            logger.info("Stopping multi-agent system...")
            
            shutdown_results = {}
            
            # Stop orchestrator scheduler first
            if "orchestrator" in self.agents:
                stop_task = AgentTask(
                    task_id="stop-scheduler",
                    agent_type="orchestrator",
                    priority=1,
                    data={"type": "stop_scheduler"},
                    created_at=datetime.now()
                )
                
                result = await self.agents["orchestrator"].process_task(stop_task)
                shutdown_results["scheduler_stopped"] = result.get("status") == "success"
            
            # Cleanup all agents
            for agent_id, agent in self.agents.items():
                try:
                    if hasattr(agent, 'cleanup'):
                        await agent.cleanup()
                    shutdown_results[f"{agent_id}_cleanup"] = True
                    logger.info(f"Agent {agent_id} cleaned up")
                except Exception as e:
                    shutdown_results[f"{agent_id}_cleanup"] = False
                    logger.error(f"Error cleaning up {agent_id}: {e}")
            
            # Save system state (could be expanded to persist task queue, metrics, etc.)
            shutdown_report = {
                "shutdown_time": datetime.now().isoformat(),
                "uptime_seconds": (datetime.now() - self.startup_time).total_seconds() if self.startup_time else 0,
                "total_agents": len(self.agents),
                "cleanup_results": shutdown_results
            }
            
            self.is_running = False
            self.system_status = AgentStatus.IDLE
            
            logger.info("Multi-agent system stopped")
            
            return {
                "status": "success", 
                "shutdown_report": shutdown_report
            }
            
        except Exception as e:
            logger.error(f"System shutdown error: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status
        """
        try:
            current_time = datetime.now()
            
            # Get orchestrator status if available
            orchestrator_status = None
            if "orchestrator" in self.agents:
                status_task = AgentTask(
                    task_id="system-status",
                    agent_type="orchestrator",
                    priority=1,
                    data={"type": "get_system_status"},
                    created_at=current_time
                )
                
                result = await self.agents["orchestrator"].process_task(status_task)
                if result.get("status") == "success":
                    orchestrator_status = result.get("system_status")
            
            # Individual agent health
            agent_statuses = {}
            for agent_id, agent in self.agents.items():
                try:
                    health_ok = await agent.health_check()
                    agent_statuses[agent_id] = {
                        "status": agent.status.value,
                        "healthy": health_ok,
                        "last_checked": current_time.isoformat()
                    }
                except Exception as e:
                    agent_statuses[agent_id] = {
                        "status": "error",
                        "healthy": False,
                        "error": str(e),
                        "last_checked": current_time.isoformat()
                    }
            
            system_health = all(status["healthy"] for status in agent_statuses.values())
            
            return {
                "status": "success",
                "system_overview": {
                    "is_running": self.is_running,
                    "is_initialized": self.is_initialized,
                    "system_status": self.system_status.value,
                    "system_healthy": system_health,
                    "startup_time": self.startup_time.isoformat() if self.startup_time else None,
                    "uptime_seconds": (current_time - self.startup_time).total_seconds() if self.startup_time else 0,
                    "total_agents": len(self.agents),
                    "healthy_agents": sum(1 for status in agent_statuses.values() if status["healthy"])
                },
                "agent_statuses": agent_statuses,
                "orchestrator_details": orchestrator_status
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Execute a task on the appropriate agent
        """
        try:
            agent_type = task.agent_type
            
            if agent_type not in self.agents:
                return {
                    "status": "error",
                    "message": f"Agent type '{agent_type}' not available"
                }
            
            agent = self.agents[agent_type]
            result = await agent.process_task(task)
            
            logger.info(f"Task {task.task_id} executed on {agent_type}: {result.get('status')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Task execution error: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def trigger_discovery(self) -> Dict[str, Any]:
        """
        Manually trigger content discovery
        """
        if "orchestrator" not in self.agents:
            return {
                "status": "error",
                "message": "Orchestrator not available"
            }
        
        task = AgentTask(
            task_id=f"manual-discovery-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            agent_type="orchestrator",
            priority=1,
            data={"type": "schedule_discovery"},
            created_at=datetime.now()
        )
        
        return await self.execute_task(task)
    
    async def trigger_pipeline_coordination(self) -> Dict[str, Any]:
        """
        Manually trigger pipeline coordination
        """
        if "orchestrator" not in self.agents:
            return {
                "status": "error", 
                "message": "Orchestrator not available"
            }
        
        task = AgentTask(
            task_id=f"manual-pipeline-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            agent_type="orchestrator",
            priority=1,
            data={"type": "coordinate_pipeline"},
            created_at=datetime.now()
        )
        
        return await self.execute_task(task)
    
    async def _health_monitoring_loop(self):
        """
        Background health monitoring
        """
        logger.info("Health monitoring started")
        
        while self.is_running:
            try:
                # Check system health every 5 minutes
                await asyncio.sleep(300)
                
                if not self.is_running:
                    break
                
                status = await self.get_system_status()
                if status.get("status") == "success":
                    overview = status.get("system_overview", {})
                    if not overview.get("system_healthy"):
                        logger.warning("System health check: Some agents are unhealthy")
                
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
        
        logger.info("Health monitoring stopped")

# Factory function for easy system creation
def create_aec_news_system(business_config=None) -> MultiAgentSystem:
    """
    Create a pre-configured AEC News multi-agent system
    """
    if business_config is None:
        # Default configuration for AEC News system
        business_config = {
            "rss_feeds": [
                "https://www.archdaily.com/rss/",
                "https://www.constructiondive.com/feeds/",
                "https://www.dezeen.com/feed/",
                "https://feeds.feedburner.com/oreilly/radar"
            ],
            "content_categories": [
                "BIM & Digital Twins",
                "Construction Automation", 
                "AI Design Tools",
                "Smart Buildings & IoT",
                "Government & Policy AI"
            ]
        }
    
    # Create system configuration
    config = SystemConfig(
        scout_config={
            "rss_feeds": business_config.get("rss_feeds", []),
            "scraping_interval": 30,
            "max_concurrent_scrapes": 5,
            "max_articles_per_source": 10,
            "content_freshness_hours": 48,
            "rate_limit_delay": 2.0
        },
        orchestrator_config={
            "discovery_interval": 30,
            "newsletter_schedule": "0 9 * * 2,5",
            "health_check_interval": 5,
            "max_concurrent_tasks": 10
        },
        auto_start_scheduler=True
    )
    
    return MultiAgentSystem(config)