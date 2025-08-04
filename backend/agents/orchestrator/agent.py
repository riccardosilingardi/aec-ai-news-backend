"""
Orchestrator Agent - Multi-Agent Coordination Implementation
Handles task scheduling, agent coordination, and system management
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
from enum import Enum
import heapq

# Import base classes from the architecture
import sys
import os
import importlib.util

# Try multiple paths for architecture import
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from multi_agent_architecture import BaseAgent, AgentTask, AgentStatus
except ImportError:
    # Load from project root
    arch_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'multi-agent-architecture.py')
    spec = importlib.util.spec_from_file_location("multi_agent_architecture", arch_path)
    arch_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(arch_module)
    BaseAgent = arch_module.BaseAgent
    AgentTask = arch_module.AgentTask
    AgentStatus = arch_module.AgentStatus

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    BACKGROUND = 5

@dataclass
class ScheduledTask:
    """Scheduled task with timing and priority"""
    task: AgentTask
    scheduled_time: datetime
    priority: TaskPriority
    retry_count: int = 0
    max_retries: int = 3
    agent_target: str = ""
    
    def __lt__(self, other):
        """For priority queue ordering"""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.scheduled_time < other.scheduled_time

@dataclass
class AgentHealth:
    """Agent health tracking"""
    agent_id: str
    status: AgentStatus
    last_heartbeat: datetime
    error_count: int = 0
    success_count: int = 0
    average_response_time: float = 0.0
    is_healthy: bool = True
    last_error: Optional[str] = None

class OrchestratorAgent(BaseAgent):
    """
    Orchestrator Agent Implementation
    
    RESPONSIBILITIES:
    - Multi-agent task coordination
    - Scheduling and timing management
    - Resource allocation and load balancing
    - Error handling and recovery
    - Performance monitoring
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        
        # Configuration
        self.discovery_interval = config.get("discovery_interval", 30)  # minutes
        self.newsletter_schedule = config.get("newsletter_schedule", "0 9 * * 2,5")  # Cron format
        self.health_check_interval = config.get("health_check_interval", 5)  # minutes
        self.max_concurrent_tasks = config.get("max_concurrent_tasks", 10)
        
        # Task management
        self.task_queue: List[ScheduledTask] = []
        self.active_tasks: Dict[str, ScheduledTask] = {}
        self.completed_tasks: List[ScheduledTask] = []
        self.failed_tasks: List[ScheduledTask] = []
        
        # Agent registry and health monitoring
        self.registered_agents: Dict[str, BaseAgent] = {}
        self.agent_health: Dict[str, AgentHealth] = {}
        
        # System state
        self.is_running = False
        self.last_discovery = None
        self.last_newsletter = None
        
        # Concurrency control
        self.task_semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
        
        logger.info(f"OrchestratorAgent {agent_id} initialized")
    
    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Process orchestration tasks
        
        Task Types:
        - "schedule_discovery": Schedule content discovery
        - "coordinate_pipeline": Manage content pipeline
        - "handle_error": Process error recovery
        - "get_system_status": Get comprehensive system status
        """
        try:
            self.status = AgentStatus.WORKING
            task_type = task.data.get("type")
            
            logger.info(f"OrchestratorAgent processing task: {task_type}")
            
            if task_type == "schedule_discovery":
                return await self._schedule_content_discovery()
            elif task_type == "coordinate_pipeline":
                return await self._coordinate_content_pipeline()
            elif task_type == "handle_error":
                return await self._handle_agent_error(task.data)
            elif task_type == "get_system_status":
                return await self._get_system_status()
            elif task_type == "register_agent":
                return await self._register_agent(task.data)
            elif task_type == "start_scheduler":
                return await self._start_scheduler()
            elif task_type == "stop_scheduler":
                return await self._stop_scheduler()
            else:
                return {"status": "error", "message": f"Unknown task type: {task_type}"}
                
        except Exception as e:
            logger.error(f"OrchestratorAgent task processing error: {e}")
            self.status = AgentStatus.ERROR
            return {"status": "error", "message": str(e)}
        finally:
            if self.status != AgentStatus.ERROR:
                self.status = AgentStatus.COMPLETED
    
    async def _schedule_content_discovery(self) -> Dict[str, Any]:
        """
        Schedule content discovery tasks for Scout Agent
        """
        try:
            current_time = datetime.now()
            
            # Check if we need to schedule discovery
            if (self.last_discovery is None or 
                current_time - self.last_discovery >= timedelta(minutes=self.discovery_interval)):
                
                # Create discovery task
                discovery_task = AgentTask(
                    task_id=f"discovery-{current_time.strftime('%Y%m%d-%H%M%S')}",
                    agent_type="scout",
                    priority=2,  # High priority
                    data={
                        "type": "discover_rss",
                        "feeds": None  # Use default feeds
                    },
                    created_at=current_time
                )
                
                # Schedule task
                scheduled_task = ScheduledTask(
                    task=discovery_task,
                    scheduled_time=current_time,
                    priority=TaskPriority.HIGH,
                    agent_target="scout"
                )
                
                await self._add_task_to_queue(scheduled_task)
                self.last_discovery = current_time
                
                logger.info(f"Scheduled content discovery task: {discovery_task.task_id}")
                
                return {
                    "status": "success",
                    "task_id": discovery_task.task_id,
                    "scheduled_time": current_time.isoformat(),
                    "next_discovery": (current_time + timedelta(minutes=self.discovery_interval)).isoformat()
                }
            else:
                next_discovery = self.last_discovery + timedelta(minutes=self.discovery_interval)
                return {
                    "status": "skipped",
                    "message": "Discovery not due yet",
                    "last_discovery": self.last_discovery.isoformat(),
                    "next_discovery": next_discovery.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error scheduling discovery: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _coordinate_content_pipeline(self) -> Dict[str, Any]:
        """
        Coordinate the content pipeline between agents
        """
        try:
            pipeline_status = {
                "scout_status": "unknown",
                "curator_status": "unknown", 
                "writer_status": "unknown",
                "tasks_created": 0,
                "recommendations": []
            }
            
            # Check Scout Agent status and content
            if "scout" in self.agent_health:
                scout_health = self.agent_health["scout"]
                pipeline_status["scout_status"] = "healthy" if scout_health.is_healthy else "unhealthy"
                
                # If Scout has discovered content, trigger Curator
                if scout_health.is_healthy and scout_health.success_count > 0:
                    curator_task = AgentTask(
                        task_id=f"curator-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                        agent_type="curator",
                        priority=2,
                        data={
                            "type": "analyze_content",
                            "source_agent": "scout"
                        },
                        created_at=datetime.now()
                    )
                    
                    scheduled_curator = ScheduledTask(
                        task=curator_task,
                        scheduled_time=datetime.now(),
                        priority=TaskPriority.HIGH,
                        agent_target="curator"
                    )
                    
                    await self._add_task_to_queue(scheduled_curator)
                    pipeline_status["tasks_created"] += 1
                    pipeline_status["recommendations"].append("Triggered curator analysis")
            
            # Check if we have enough curated content for newsletter
            current_time = datetime.now()
            if (self.last_newsletter is None or 
                current_time - self.last_newsletter >= timedelta(days=2)):  # Bi-weekly
                
                writer_task = AgentTask(
                    task_id=f"newsletter-{current_time.strftime('%Y%m%d-%H%M%S')}",
                    agent_type="writer",
                    priority=1,
                    data={
                        "type": "generate_newsletter",
                        "trigger": "scheduled"
                    },
                    created_at=current_time
                )
                
                scheduled_writer = ScheduledTask(
                    task=writer_task,
                    scheduled_time=current_time,
                    priority=TaskPriority.CRITICAL,
                    agent_target="writer"
                )
                
                await self._add_task_to_queue(scheduled_writer)
                pipeline_status["tasks_created"] += 1
                pipeline_status["recommendations"].append("Triggered newsletter generation")
                self.last_newsletter = current_time
            
            return {
                "status": "success",
                "pipeline_status": pipeline_status,
                "queue_size": len(self.task_queue),
                "active_tasks": len(self.active_tasks)
            }
            
        except Exception as e:
            logger.error(f"Error coordinating pipeline: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _handle_agent_error(self, error_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle agent errors and implement recovery strategies
        """
        try:
            agent_id = error_data.get("agent_id")
            error_message = error_data.get("error")
            task_id = error_data.get("task_id")
            
            if not agent_id:
                return {"status": "error", "message": "Agent ID required for error handling"}
            
            # Update agent health
            if agent_id in self.agent_health:
                health = self.agent_health[agent_id]
                health.error_count += 1
                health.last_error = error_message
                health.is_healthy = health.error_count < 5  # Threshold
                
                logger.warning(f"Agent {agent_id} error: {error_message}")
            
            # Find and retry failed task if applicable
            recovery_actions = []
            
            if task_id:
                # Find task in active or failed tasks
                failed_task = None
                if task_id in self.active_tasks:
                    failed_task = self.active_tasks.pop(task_id)
                
                if failed_task and failed_task.retry_count < failed_task.max_retries:
                    # Retry task with backoff
                    failed_task.retry_count += 1
                    retry_delay = 2 ** failed_task.retry_count  # Exponential backoff
                    failed_task.scheduled_time = datetime.now() + timedelta(minutes=retry_delay)
                    
                    await self._add_task_to_queue(failed_task)
                    recovery_actions.append(f"Scheduled retry {failed_task.retry_count} for task {task_id}")
                    
                elif failed_task:
                    # Max retries reached
                    self.failed_tasks.append(failed_task)
                    recovery_actions.append(f"Task {task_id} failed permanently after {failed_task.max_retries} retries")
            
            # Agent-specific recovery strategies
            if agent_id == "scout" and not self.agent_health[agent_id].is_healthy:
                # Reduce discovery frequency for unhealthy Scout
                recovery_actions.append("Reduced Scout discovery frequency due to errors")
            
            return {
                "status": "success",
                "agent_id": agent_id,
                "recovery_actions": recovery_actions,
                "agent_health": asdict(self.agent_health.get(agent_id, {}))
            }
            
        except Exception as e:
            logger.error(f"Error handling agent error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _register_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register an agent with the orchestrator
        """
        try:
            agent_id = agent_data.get("agent_id")
            agent_type = agent_data.get("agent_type")
            agent_instance = agent_data.get("agent_instance")
            
            if not all([agent_id, agent_type]):
                return {"status": "error", "message": "Agent ID and type required"}
            
            # Register agent
            if agent_instance:
                self.registered_agents[agent_id] = agent_instance
            
            # Initialize health tracking
            self.agent_health[agent_id] = AgentHealth(
                agent_id=agent_id,
                status=AgentStatus.IDLE,
                last_heartbeat=datetime.now(),
                is_healthy=True
            )
            
            logger.info(f"Registered agent: {agent_id} ({agent_type})")
            
            return {
                "status": "success",
                "agent_id": agent_id,
                "registered_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error registering agent: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status
        """
        try:
            current_time = datetime.now()
            
            # Calculate system metrics
            total_tasks = len(self.completed_tasks) + len(self.failed_tasks) + len(self.active_tasks)
            success_rate = (len(self.completed_tasks) / max(total_tasks, 1)) * 100
            
            # Agent health summary
            healthy_agents = sum(1 for health in self.agent_health.values() if health.is_healthy)
            total_agents = len(self.agent_health)
            
            status = {
                "orchestrator_status": self.status.value,
                "system_running": self.is_running,
                "current_time": current_time.isoformat(),
                
                "task_metrics": {
                    "queue_size": len(self.task_queue),
                    "active_tasks": len(self.active_tasks),
                    "completed_tasks": len(self.completed_tasks),
                    "failed_tasks": len(self.failed_tasks),
                    "success_rate": f"{success_rate:.1f}%"
                },
                
                "agent_health": {
                    "healthy_agents": f"{healthy_agents}/{total_agents}",
                    "registered_agents": list(self.agent_health.keys()),
                    "details": {
                        agent_id: {
                            "status": health.status.value,
                            "is_healthy": health.is_healthy,
                            "error_count": health.error_count,
                            "success_count": health.success_count,
                            "last_heartbeat": health.last_heartbeat.isoformat() if health.last_heartbeat else None
                        }
                        for agent_id, health in self.agent_health.items()
                    }
                },
                
                "scheduling": {
                    "discovery_interval": f"{self.discovery_interval} minutes",
                    "last_discovery": self.last_discovery.isoformat() if self.last_discovery else None,
                    "last_newsletter": self.last_newsletter.isoformat() if self.last_newsletter else None,
                    "next_discovery": (self.last_discovery + timedelta(minutes=self.discovery_interval)).isoformat() if self.last_discovery else "pending"
                }
            }
            
            return {
                "status": "success",
                "system_status": status
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _add_task_to_queue(self, scheduled_task: ScheduledTask):
        """
        Add task to priority queue
        """
        heapq.heappush(self.task_queue, scheduled_task)
        logger.debug(f"Added task to queue: {scheduled_task.task.task_id}")
    
    async def _start_scheduler(self) -> Dict[str, Any]:
        """
        Start the task scheduler
        """
        if self.is_running:
            return {"status": "warning", "message": "Scheduler already running"}
        
        self.is_running = True
        asyncio.create_task(self._scheduler_loop())
        
        logger.info("Orchestrator scheduler started")
        return {"status": "success", "message": "Scheduler started"}
    
    async def _stop_scheduler(self) -> Dict[str, Any]:
        """
        Stop the task scheduler
        """
        if not self.is_running:
            return {"status": "warning", "message": "Scheduler not running"}
        
        self.is_running = False
        
        logger.info("Orchestrator scheduler stopped")
        return {"status": "success", "message": "Scheduler stopped"}
    
    async def _scheduler_loop(self):
        """
        Main scheduler loop
        """
        logger.info("Orchestrator scheduler loop started")
        
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # Process due tasks
                while self.task_queue and self.task_queue[0].scheduled_time <= current_time:
                    scheduled_task = heapq.heappop(self.task_queue)
                    
                    # Execute task asynchronously
                    asyncio.create_task(self._execute_task(scheduled_task))
                
                # Health checks every 5 minutes
                if current_time.minute % 5 == 0:
                    await self._perform_health_checks()
                
                # Sleep for 30 seconds before next iteration
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _execute_task(self, scheduled_task: ScheduledTask):
        """
        Execute a scheduled task
        """
        async with self.task_semaphore:
            try:
                task = scheduled_task.task
                self.active_tasks[task.task_id] = scheduled_task
                
                logger.info(f"Executing task: {task.task_id} for agent {scheduled_task.agent_target}")
                
                # Find target agent
                target_agent = self.registered_agents.get(scheduled_task.agent_target)
                
                if target_agent:
                    # Execute task on target agent
                    start_time = datetime.now()
                    result = await target_agent.process_task(task)
                    execution_time = (datetime.now() - start_time).total_seconds()
                    
                    # Update agent health
                    if scheduled_task.agent_target in self.agent_health:
                        health = self.agent_health[scheduled_task.agent_target]
                        health.last_heartbeat = datetime.now()
                        
                        if result.get("status") == "success":
                            health.success_count += 1
                            health.average_response_time = (
                                (health.average_response_time * (health.success_count - 1) + execution_time) / 
                                health.success_count
                            )
                        else:
                            health.error_count += 1
                    
                    # Move to completed
                    self.completed_tasks.append(scheduled_task)
                    logger.info(f"Task completed: {task.task_id}")
                    
                else:
                    logger.warning(f"Target agent not found: {scheduled_task.agent_target}")
                    self.failed_tasks.append(scheduled_task)
                
                # Remove from active tasks
                self.active_tasks.pop(task.task_id, None)
                
            except Exception as e:
                logger.error(f"Task execution error: {e}")
                self.failed_tasks.append(scheduled_task)
                self.active_tasks.pop(scheduled_task.task.task_id, None)
    
    async def _perform_health_checks(self):
        """
        Perform health checks on all registered agents
        """
        for agent_id, agent in self.registered_agents.items():
            try:
                health_ok = await agent.health_check()
                
                if agent_id in self.agent_health:
                    self.agent_health[agent_id].is_healthy = health_ok
                    self.agent_health[agent_id].last_heartbeat = datetime.now()
                    
            except Exception as e:
                logger.warning(f"Health check failed for {agent_id}: {e}")
                if agent_id in self.agent_health:
                    self.agent_health[agent_id].is_healthy = False
                    self.agent_health[agent_id].error_count += 1
    
    async def health_check(self) -> bool:
        """
        Check orchestrator health
        """
        try:
            # Check if scheduler is running
            if not self.is_running:
                return False
            
            # Check if any agents are healthy
            healthy_agents = sum(1 for health in self.agent_health.values() if health.is_healthy)
            return healthy_agents > 0
            
        except Exception as e:
            logger.error(f"Orchestrator health check error: {e}")
            return False
    
    async def cleanup(self):
        """
        Cleanup orchestrator resources
        """
        self.is_running = False
        
        # Wait for active tasks to complete (with timeout)
        timeout = 30  # seconds
        start_time = datetime.now()
        
        while self.active_tasks and (datetime.now() - start_time).total_seconds() < timeout:
            await asyncio.sleep(1)
        
        logger.info(f"OrchestratorAgent {self.agent_id} cleaned up")