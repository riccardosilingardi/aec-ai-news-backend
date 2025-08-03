"""
Base Agent Class and System Types
Copy relevant sections from multi-agent-architecture.py
"""

# Import base classes from architecture
from .architecture import BaseAgent, AgentStatus, AgentTask, ContentItem

# Re-export for easier imports
__all__ = ['BaseAgent', 'AgentStatus', 'AgentTask', 'ContentItem']