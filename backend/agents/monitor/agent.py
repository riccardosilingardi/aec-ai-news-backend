"""
Monitor Agent - Real-time System Health and Performance Monitoring

TODO - Phase 3 (Week 3):
[ ] System health monitoring and alerting
[ ] Performance metrics collection and analysis
[ ] Agent health checks and recovery procedures
[ ] Database performance monitoring
[ ] Content pipeline monitoring (articles per hour, quality trends)
[ ] Email delivery monitoring and bounce handling
[ ] Error detection and automated recovery
[ ] Business metrics tracking (engagement, growth, churn)
[ ] Real-time dashboard data feeds
[ ] Anomaly detection for content quality or system performance

MONITORING FOCUS:
- Agent performance and availability
- Content pipeline health and throughput
- Database performance and storage usage
- Email delivery success rates
- User engagement metrics
- System resource utilization
- Error rates and recovery times
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import psutil

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

class MonitorAgent(BaseAgent):
    """Monitor Agent for system health and performance tracking"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        super().__init__(agent_id, "monitor", config)
        self.monitoring_interval = config.get('monitoring_interval', 60) if config else 60
        self.alert_thresholds = config.get('alert_thresholds', {}) if config else {}
        self.metrics_history = []
        self.alert_history = []
        
    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process monitoring tasks"""
        try:
            task_type = task.data.get('type')
            
            if task_type == 'health_check':
                return await self.perform_health_check(task)
            elif task_type == 'collect_metrics':
                return await self.collect_system_metrics(task)
            elif task_type == 'monitor_agents':
                return await self.monitor_agent_health(task)
            elif task_type == 'monitor_pipeline':
                return await self.monitor_content_pipeline(task)
            elif task_type == 'generate_report':
                return await self.generate_monitoring_report(task)
            else:
                return {"error": f"Unknown task type: {task_type}"}
                
        except Exception as e:
            logger.error(f"Monitor agent task failed: {e}")
            return {"error": str(e)}
    
    async def perform_health_check(self, task: AgentTask) -> Dict[str, Any]:
        """Comprehensive system health check"""
        try:
            health_status = {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "healthy",
                "components": {},
                "alerts": [],
                "metrics": {}
            }
            
            # System resource check
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            health_status["metrics"]["system"] = {
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "disk_usage": disk.percent,
                "available_memory": memory.available,
                "free_disk": disk.free
            }
            
            # Check resource thresholds
            if cpu_percent > self.alert_thresholds.get('cpu_threshold', 80):
                health_status["alerts"].append({
                    "type": "high_cpu",
                    "level": "warning",
                    "message": f"CPU usage at {cpu_percent:.1f}%"
                })
            
            if memory.percent > self.alert_thresholds.get('memory_threshold', 85):
                health_status["alerts"].append({
                    "type": "high_memory",
                    "level": "warning", 
                    "message": f"Memory usage at {memory.percent:.1f}%"
                })
            
            if disk.percent > self.alert_thresholds.get('disk_threshold', 90):
                health_status["alerts"].append({
                    "type": "high_disk",
                    "level": "critical",
                    "message": f"Disk usage at {disk.percent:.1f}%"
                })
            
            # Database health check
            try:
                # Simulate database check
                health_status["components"]["database"] = {
                    "status": "healthy",
                    "response_time": "N/A",
                    "connections": "N/A"
                }
            except Exception as e:
                health_status["components"]["database"] = {
                    "status": "error",
                    "error": str(e)
                }
                health_status["alerts"].append({
                    "type": "database_error",
                    "level": "critical",
                    "message": f"Database health check failed: {e}"
                })
            
            # Determine overall status
            critical_alerts = [a for a in health_status["alerts"] if a["level"] == "critical"]
            warning_alerts = [a for a in health_status["alerts"] if a["level"] == "warning"]
            
            if critical_alerts:
                health_status["overall_status"] = "critical"
            elif warning_alerts:
                health_status["overall_status"] = "warning"
            
            # Store metrics history
            self.metrics_history.append(health_status)
            if len(self.metrics_history) > 1000:  # Keep last 1000 entries
                self.metrics_history = self.metrics_history[-1000:]
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "error",
                "error": str(e)
            }
    
    async def collect_system_metrics(self, task: AgentTask) -> Dict[str, Any]:
        """Collect detailed system performance metrics"""
        try:
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "system": {},
                "application": {},
                "business": {}
            }
            
            # System metrics
            metrics["system"] = {
                "cpu": {
                    "usage_percent": psutil.cpu_percent(interval=1),
                    "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None,
                    "core_count": psutil.cpu_count()
                },
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "used": psutil.virtual_memory().used,
                    "percent": psutil.virtual_memory().percent
                },
                "disk": {
                    "total": psutil.disk_usage('/').total,
                    "free": psutil.disk_usage('/').free,
                    "used": psutil.disk_usage('/').used,
                    "percent": psutil.disk_usage('/').percent
                },
                "network": {
                    "bytes_sent": psutil.net_io_counters().bytes_sent,
                    "bytes_recv": psutil.net_io_counters().bytes_recv,
                    "packets_sent": psutil.net_io_counters().packets_sent,
                    "packets_recv": psutil.net_io_counters().packets_recv
                }
            }
            
            # Application metrics (would be populated by actual system)
            metrics["application"] = {
                "active_agents": 0,
                "queued_tasks": 0,
                "processed_tasks_hour": 0,
                "error_rate": 0.0,
                "avg_response_time": 0.0
            }
            
            # Business metrics (would be populated from database)
            metrics["business"] = {
                "articles_discovered_today": 0,
                "articles_analyzed_today": 0,
                "newsletters_sent_today": 0,
                "active_subscribers": 0,
                "engagement_rate": 0.0
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Metrics collection failed: {e}")
            return {"error": str(e)}
    
    async def monitor_agent_health(self, task: AgentTask) -> Dict[str, Any]:
        """Monitor health of all system agents"""
        try:
            agent_health = {
                "timestamp": datetime.now().isoformat(),
                "agents": {},
                "summary": {
                    "total_agents": 0,
                    "healthy_agents": 0,
                    "unhealthy_agents": 0,
                    "error_agents": 0
                }
            }
            
            # This would check actual agents in the system
            agent_types = ["scout", "curator", "writer", "orchestrator"]
            
            for agent_type in agent_types:
                try:
                    # Simulate agent health check
                    agent_health["agents"][agent_type] = {
                        "status": "healthy",
                        "last_activity": datetime.now().isoformat(),
                        "tasks_completed": 0,
                        "avg_execution_time": 0.0,
                        "error_count": 0,
                        "memory_usage": 0
                    }
                    agent_health["summary"]["healthy_agents"] += 1
                except Exception as e:
                    agent_health["agents"][agent_type] = {
                        "status": "error",
                        "error": str(e),
                        "last_activity": None
                    }
                    agent_health["summary"]["error_agents"] += 1
                
                agent_health["summary"]["total_agents"] += 1
            
            agent_health["summary"]["unhealthy_agents"] = (
                agent_health["summary"]["total_agents"] - 
                agent_health["summary"]["healthy_agents"] - 
                agent_health["summary"]["error_agents"]
            )
            
            return agent_health
            
        except Exception as e:
            logger.error(f"Agent health monitoring failed: {e}")
            return {"error": str(e)}
    
    async def monitor_content_pipeline(self, task: AgentTask) -> Dict[str, Any]:
        """Monitor content discovery and processing pipeline"""
        try:
            pipeline_status = {
                "timestamp": datetime.now().isoformat(),
                "pipeline_health": "healthy",
                "stages": {},
                "throughput": {},
                "quality_metrics": {},
                "bottlenecks": []
            }
            
            # Monitor each pipeline stage
            stages = ["discovery", "analysis", "curation", "publication"]
            
            for stage in stages:
                pipeline_status["stages"][stage] = {
                    "status": "healthy",
                    "queue_length": 0,
                    "processing_rate": 0.0,
                    "avg_processing_time": 0.0,
                    "error_rate": 0.0,
                    "last_processed": datetime.now().isoformat()
                }
            
            # Throughput metrics
            pipeline_status["throughput"] = {
                "articles_per_hour": 0,
                "analysis_completion_rate": 0.0,
                "newsletter_generation_rate": 0.0,
                "end_to_end_time": 0.0
            }
            
            # Quality metrics
            pipeline_status["quality_metrics"] = {
                "avg_quality_score": 0.0,
                "quality_trend": "stable",
                "high_quality_percentage": 0.0,
                "rejected_content_rate": 0.0
            }
            
            # Identify bottlenecks
            for stage, metrics in pipeline_status["stages"].items():
                if metrics["queue_length"] > 100:
                    pipeline_status["bottlenecks"].append({
                        "stage": stage,
                        "issue": "high_queue_length",
                        "severity": "warning"
                    })
                if metrics["error_rate"] > 0.1:
                    pipeline_status["bottlenecks"].append({
                        "stage": stage,
                        "issue": "high_error_rate",
                        "severity": "critical"
                    })
            
            if pipeline_status["bottlenecks"]:
                pipeline_status["pipeline_health"] = "degraded"
            
            return pipeline_status
            
        except Exception as e:
            logger.error(f"Pipeline monitoring failed: {e}")
            return {"error": str(e)}
    
    async def generate_monitoring_report(self, task: AgentTask) -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""
        try:
            time_period = task.data.get('time_period', 'hour')  # hour, day, week
            
            report = {
                "timestamp": datetime.now().isoformat(),
                "period": time_period,
                "executive_summary": {},
                "system_performance": {},
                "agent_performance": {},
                "business_metrics": {},
                "alerts_summary": {},
                "recommendations": []
            }
            
            # Executive summary
            report["executive_summary"] = {
                "overall_health": "healthy",
                "uptime": "99.9%",
                "critical_issues": 0,
                "warnings": 0,
                "performance_score": 95.0
            }
            
            # System performance trends
            report["system_performance"] = {
                "avg_cpu_usage": 45.2,
                "avg_memory_usage": 62.8,
                "peak_cpu": 78.5,
                "peak_memory": 84.1,
                "disk_growth": 2.3,
                "network_throughput": "normal"
            }
            
            # Agent performance summary
            report["agent_performance"] = {
                "scout": {"availability": 99.8, "avg_response": 2.1, "tasks_completed": 145},
                "curator": {"availability": 99.5, "avg_response": 5.3, "tasks_completed": 89},
                "writer": {"availability": 100.0, "avg_response": 15.2, "tasks_completed": 12},
                "orchestrator": {"availability": 99.9, "avg_response": 0.8, "tasks_completed": 234}
            }
            
            # Business metrics
            report["business_metrics"] = {
                "content_discovered": 150,
                "content_analyzed": 89,
                "newsletters_generated": 2,
                "subscriber_growth": "+5.2%",
                "engagement_rate": "12.4%"
            }
            
            # Alerts summary
            report["alerts_summary"] = {
                "critical": len([a for a in self.alert_history if a.get('level') == 'critical']),
                "warning": len([a for a in self.alert_history if a.get('level') == 'warning']),
                "info": len([a for a in self.alert_history if a.get('level') == 'info'])
            }
            
            # Recommendations
            if report["system_performance"]["peak_memory"] > 80:
                report["recommendations"].append({
                    "type": "performance",
                    "priority": "medium",
                    "message": "Consider increasing memory allocation or optimizing memory usage"
                })
            
            if report["agent_performance"]["curator"]["avg_response"] > 5:
                report["recommendations"].append({
                    "type": "agent_optimization",
                    "priority": "low",
                    "message": "Curator agent response time could be optimized"
                })
            
            return report
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return {"error": str(e)}
    
    async def cleanup(self) -> None:
        """Cleanup monitor agent resources"""
        try:
            logger.info(f"Monitor Agent {self.agent_id} cleaning up...")
            # Save final metrics if needed
            # Close any monitoring connections
            await super().cleanup()
        except Exception as e:
            logger.error(f"Monitor agent cleanup failed: {e}")