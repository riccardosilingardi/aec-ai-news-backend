"""
System Configuration Management

TODO:
[ ] Environment-specific configs (dev/staging/prod)
[ ] Agent-specific parameters
[ ] Source URLs and refresh intervals
[ ] Newsletter generation settings
[ ] Performance thresholds and alerts
[ ] Integration credentials (Supabase, Cloudflare)
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path

@dataclass
class ScoutConfig:
    """Scout Agent Configuration"""
    rss_feeds: List[str] = field(default_factory=lambda: [
        "https://www.archdaily.com/rss/",
        "https://feeds.feedburner.com/TEDTalks_video",
        "https://www.constructiondive.com/feeds/news/",
        "https://www.enr.com/rss/news"
    ])
    scraping_interval: int = 1800  # 30 minutes
    max_concurrent_scrapes: int = 3
    max_articles_per_source: int = 10
    rate_limit_delay: float = 2.0
    
    # Enhanced features
    enable_advanced_scraping: bool = True
    enable_search: bool = True
    enable_youtube: bool = True
    web_search_limit: int = 20
    youtube_search_limit: int = 10
    
    # Advanced scraper config
    use_scrapling: bool = True
    scraper_max_retries: int = 3
    scraper_retry_delay: float = 5.0
    scraper_timeout: float = 30.0
    max_content_length: int = 10000

@dataclass
class CuratorConfig:
    """Curator Agent Configuration"""
    quality_threshold: float = 0.6
    relevance_threshold: float = 0.7
    max_processing_time: int = 30  # seconds
    batch_size: int = 10
    
    # AEC industry categories
    categories: List[str] = field(default_factory=lambda: [
        "AI Technology", "Construction Innovation", "BIM & Digital Twins",
        "Project Management", "Sustainability", "Robotics & Automation",
        "Smart Buildings", "Industry Research", "Regulatory Changes",
        "Business Intelligence", "Market Analysis"
    ])
    
    # Quality scoring weights
    readability_weight: float = 0.3
    authority_weight: float = 0.4
    freshness_weight: float = 0.3

@dataclass
class WriterConfig:
    """Writer Agent Configuration"""
    newsletter_frequency: str = "bi-weekly"  # daily, weekly, bi-weekly
    executive_summary_length: int = 500  # words
    max_articles_per_issue: int = 15
    template_path: str = "data/templates/newsletter.html"
    
    # Style preferences
    tone: str = "professional"  # professional, casual, technical
    include_emojis: bool = True
    include_analytics: bool = True
    
    # A/B testing
    enable_ab_testing: bool = True
    subject_line_variants: int = 3

@dataclass
class OrchestratorConfig:
    """Orchestrator Agent Configuration"""
    task_queue_size: int = 1000
    max_concurrent_tasks: int = 5
    task_timeout: int = 300  # 5 minutes
    retry_attempts: int = 3
    
    # Scheduling
    discovery_interval: int = 1800  # 30 minutes
    analysis_batch_size: int = 20
    newsletter_schedule: str = "0 9 * * 1,4"  # Monday and Thursday at 9 AM

@dataclass
class MonitorConfig:
    """Monitor Agent Configuration"""
    health_check_interval: int = 300  # 5 minutes
    performance_alert_threshold: float = 0.8
    error_rate_threshold: float = 0.1
    
    # Metrics to track
    track_response_times: bool = True
    track_success_rates: bool = True
    track_content_quality: bool = True

@dataclass
class DatabaseConfig:
    """Database Configuration"""
    url: str = "sqlite:///aec_ai_news.db"
    pool_size: int = 10
    max_overflow: int = 20
    
    # For production PostgreSQL
    host: Optional[str] = None
    port: int = 5432
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None

@dataclass
class MCPConfig:
    """MCP Server Configuration"""
    host: str = "localhost"
    port: int = 8000
    debug: bool = False
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    
    # Tool configurations
    enable_agent_control: bool = True
    enable_content_management: bool = True
    enable_analytics: bool = True

@dataclass
class APIConfig:
    """External API Configuration"""
    # Search APIs
    bing_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    google_cse_id: Optional[str] = None
    serpapi_key: Optional[str] = None
    
    # Content analysis
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # YouTube integration
    klavis_api_key: Optional[str] = None
    
    # Email delivery
    sendgrid_api_key: Optional[str] = None
    from_email: str = "newsletter@aec-ai-news.com"

@dataclass
class SystemConfig:
    """Complete System Configuration"""
    environment: str = "development"  # development, staging, production
    debug: bool = True
    log_level: str = "INFO"
    
    # Component configurations
    scout: ScoutConfig = field(default_factory=ScoutConfig)
    curator: CuratorConfig = field(default_factory=CuratorConfig)
    writer: WriterConfig = field(default_factory=WriterConfig)
    orchestrator: OrchestratorConfig = field(default_factory=OrchestratorConfig)
    monitor: MonitorConfig = field(default_factory=MonitorConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    mcp: MCPConfig = field(default_factory=MCPConfig)
    apis: APIConfig = field(default_factory=APIConfig)
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    allowed_hosts: List[str] = field(default_factory=lambda: ["localhost", "127.0.0.1"])
    
    @classmethod
    def from_env(cls) -> "SystemConfig":
        """Create configuration from environment variables"""
        config = cls()
        
        # Environment
        config.environment = os.getenv("ENVIRONMENT", "development")
        config.debug = os.getenv("DEBUG", "true").lower() == "true"
        config.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # Database
        if db_url := os.getenv("DATABASE_URL"):
            config.database.url = db_url
        
        # MCP Server
        config.mcp.host = os.getenv("MCP_HOST", "localhost")
        config.mcp.port = int(os.getenv("MCP_PORT", "8000"))
        
        # API Keys
        config.apis.bing_api_key = os.getenv("BING_API_KEY")
        config.apis.google_api_key = os.getenv("GOOGLE_API_KEY")
        config.apis.google_cse_id = os.getenv("GOOGLE_CSE_ID")
        config.apis.serpapi_key = os.getenv("SERPAPI_KEY")
        config.apis.openai_api_key = os.getenv("OPENAI_API_KEY")
        config.apis.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        config.apis.klavis_api_key = os.getenv("KLAVIS_API_KEY")
        config.apis.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        config.apis.from_email = os.getenv("FROM_EMAIL", config.apis.from_email)
        
        # Security
        config.secret_key = os.getenv("SECRET_KEY", config.secret_key)
        
        return config
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary"""
        import dataclasses
        return dataclasses.asdict(self)
    
    def get_agent_config(self, agent_type: str) -> Dict:
        """Get configuration for specific agent type"""
        agent_configs = {
            "scout": self.scout,
            "curator": self.curator,
            "writer": self.writer,
            "orchestrator": self.orchestrator,
            "monitor": self.monitor
        }
        
        config = agent_configs.get(agent_type)
        if not config:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        # Convert to dict and add common config
        import dataclasses
        agent_dict = dataclasses.asdict(config)
        
        # Add API keys if relevant
        if agent_type == "scout":
            agent_dict.update({
                "bing_api_key": self.apis.bing_api_key,
                "google_api_key": self.apis.google_api_key,
                "google_cse_id": self.apis.google_cse_id,
                "serpapi_key": self.apis.serpapi_key,
                "klavis_api_key": self.apis.klavis_api_key,
                "anthropic_api_key": self.apis.anthropic_api_key
            })
        elif agent_type == "curator":
            agent_dict.update({
                "openai_api_key": self.apis.openai_api_key,
                "anthropic_api_key": self.apis.anthropic_api_key
            })
        elif agent_type == "writer":
            agent_dict.update({
                "openai_api_key": self.apis.openai_api_key,
                "anthropic_api_key": self.apis.anthropic_api_key,
                "sendgrid_api_key": self.apis.sendgrid_api_key,
                "from_email": self.apis.from_email
            })
        
        return agent_dict

# Global configuration instance
_config = None

def get_config() -> SystemConfig:
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = SystemConfig.from_env()
    return _config

def set_config(config: SystemConfig):
    """Set global configuration instance"""
    global _config
    _config = config