# AEC AI News Scout - Multi-Agent System

## 🏗️ Overview

A professional multi-agent system for AEC (Architecture, Engineering, Construction) industry AI news curation and newsletter generation. The system uses Python MCP (Model Context Protocol) with specialized agents for content discovery, curation, and newsletter generation.

## 🚀 New Features - Scout Agent Implementation

### ✅ Phase 1 Complete: Scout Agent RSS Discovery

The Scout Agent is now fully implemented with the following capabilities:

- **Real-time RSS/feed monitoring** with configurable intervals
- **Advanced content deduplication** using hash-based detection
- **Source performance tracking** and reliability metrics
- **Rate limiting and retry logic** for stable operation
- **Content freshness validation** (configurable time windows)
- **Error handling and recovery** with detailed logging
- **MCP integration** for easy CLI and API access

## 📁 Project Structure

```
aec-ai-news/
├── backend/
│   └── agents/
│       ├── scout/
│       │   ├── agent.py              # ScoutAgent implementation
│       │   ├── mcp_integration.py    # MCP tools integration
│       │   └── test_scout.py         # Test script
│       ├── curator/                  # Future: CuratorAgent
│       ├── writer/                   # Future: WriterAgent
│       ├── orchestrator/             # Future: OrchestratorAgent
│       └── monitor/                  # Future: MonitorAgent
├── multi-agent-architecture.py      # Core architecture definitions
├── aec-ai-news-mcp.py              # Original MCP server
├── enhanced-mcp-server.py          # Enhanced server with Scout Agent
├── requirements.txt                 # Updated dependencies
└── README.md                       # This file
```

## 🛠️ Installation & Setup

### 1. Install Dependencies

```bash
cd aec-ai-news
pip install -r requirements.txt
```

### 2. Test Scout Agent

```bash
cd backend/agents/scout
python test_scout.py
```

### 3. Run Enhanced MCP Server

```bash
python enhanced-mcp-server.py
```

The enhanced server runs on port 8001 by default.

## 🎯 Usage Examples

### Scout Agent MCP Tools

The Scout Agent provides several MCP tools for content discovery:

#### 1. Discover AEC Content
```python
# Discover content from configured RSS feeds
await discover_aec_content_advanced()

# Discover from specific sources
await discover_aec_content_advanced(
    sources=["https://www.archdaily.com/rss/"],
    max_articles=10
)
```

#### 2. Performance Monitoring
```python
# Get detailed source performance metrics
await get_discovery_performance()

# Check system health
await system_health_check()
```

#### 3. Test RSS Feeds
```python
# Test a specific RSS feed
await test_content_source("https://www.archdaily.com/rss/")
```

#### 4. Enhanced Newsletter Generation
```python
# Generate newsletter with fresh Scout Agent content
await generate_enhanced_newsletter(use_scout_content=True)
```

## 📊 Scout Agent Features

### Content Discovery
- **RSS Feed Parsing**: Robust feedparser integration with error handling
- **Concurrent Processing**: Configurable semaphores for parallel feed processing
- **Content Extraction**: Advanced HTML parsing for full article content
- **Deduplication**: Hash-based duplicate detection across sources

### Performance Tracking
- **Source Metrics**: Success rates, response times, article counts
- **Error Monitoring**: Detailed error tracking and reporting
- **Health Checks**: Automated source availability testing
- **Rate Limiting**: Configurable delays to respect source limits

### Quality Assurance
- **Content Freshness**: Configurable time windows for relevant content
- **Error Recovery**: Graceful handling of failed requests
- **Data Validation**: Structured data models with type checking
- **Logging**: Comprehensive logging for debugging and monitoring

## ⚙️ Configuration

### Scout Agent Configuration
```python
scout_config = {
    "rss_feeds": [
        "https://www.archdaily.com/rss/",
        "https://www.constructiondive.com/feeds/",
        # ... more feeds
    ],
    "scraping_interval": 30,           # minutes between scrapes
    "max_concurrent_scrapes": 5,       # parallel feed processing
    "max_articles_per_source": 10,     # articles per feed
    "content_freshness_hours": 48,     # content age limit
    "rate_limit_delay": 2.0           # seconds between requests
}
```

### RSS Feed Sources
The system is pre-configured with high-quality AEC industry feeds:

- **Architecture**: ArchDaily, Dezeen, Architect's Journal
- **Construction**: Construction Dive, BDC Network
- **Engineering**: Engineering.com, AEC Magazine
- **BIM/CAD**: Autodesk, Trimble, Bentley blogs
- **AI/Tech**: ArXiv AI papers, tech journalism feeds

## 📈 Performance Metrics

### Scout Agent Metrics Dashboard
- **Total Sources**: Number of configured RSS feeds
- **Success Rates**: Per-source reliability statistics  
- **Response Times**: Average API response performance
- **Content Discovery**: Articles found vs. duplicates filtered
- **Error Tracking**: Failed requests and error patterns

### Example Output
```
📊 Scout Agent Performance Dashboard

Overall Metrics:
• Total RSS sources: 15
• Content items discovered: 342
• Unique content pieces: 298
• Deduplication rate: 12.9%

Source Performance:
✅ archdaily.com
• Success rate: 98.5%
• Avg articles/scrape: 8.2
• Total articles: 164
• Response time: 1.23s
```

## 🧪 Testing

### Run Scout Agent Tests
```bash
cd backend/agents/scout
python test_scout.py
```

### Test Individual Features
```python
# Test RSS discovery
task = AgentTask(
    task_id="test-001",
    agent_type="scout", 
    priority=1,
    data={"type": "discover_rss", "feeds": ["feed_url"]},
    created_at=datetime.now()
)
result = await scout_agent.process_task(task)
```

## 🚧 Roadmap - Next Phases

### Phase 2: Curator Agent (Week 2)
- [ ] AI-powered content quality scoring
- [ ] AEC industry relevance analysis  
- [ ] Content categorization and tagging
- [ ] Trend identification

### Phase 3: Writer Agent (Week 3)
- [ ] Superhuman-style executive summaries
- [ ] Newsletter HTML/text generation
- [ ] Personalization and tone adjustment
- [ ] A/B testing framework

### Phase 4: Orchestrator Agent (Week 4)
- [ ] Multi-agent task coordination
- [ ] Scheduling and automation
- [ ] Resource allocation
- [ ] Error handling and recovery

### Phase 5: Monitor Agent (Week 5)
- [ ] Business metrics tracking
- [ ] User engagement analysis
- [ ] Performance optimization
- [ ] Alert generation

## 🔧 Development

### Adding New RSS Sources
```python
# In scout agent configuration
new_feeds = [
    "https://new-aec-site.com/rss",
    "https://another-source.com/feed.xml"
]
```

### Extending Scout Agent
```python
# Add new task types to ScoutAgent.process_task()
elif task_type == "custom_discovery":
    return await self._custom_discovery_method(task.data)
```

### MCP Tool Development
```python
# Add new MCP tools in mcp_integration.py
@mcp_server.tool()
async def new_scout_feature() -> str:
    """New Scout Agent functionality"""
    return await integration.new_feature_method()
```

## 📝 Logging

The system provides comprehensive logging at multiple levels:

```python
# Debug: Detailed request/response info
# Info: Operation status and metrics
# Warning: Non-critical issues (parsing errors, timeouts)
# Error: Critical failures requiring attention
```

## 🤝 Contributing

1. **Follow Architecture**: Use the BaseAgent interface from `multi-agent-architecture.py`
2. **Add Tests**: Include test scripts for new functionality
3. **Update Docs**: Keep README and docstrings current
4. **Error Handling**: Implement robust error recovery
5. **Metrics**: Add performance tracking for new features

## 📄 License

MIT License - See LICENSE file for details.

## 🎯 Business Model

**Free Newsletter** with alternative monetization:
- Affiliate partnerships with AEC software vendors
- Sponsored content from industry leaders  
- Premium industry reports and consulting
- Speaking engagements and advisory services

**Target Revenue**: €102,000 ARR by Year 1

---

**Ready to revolutionize AEC industry AI intelligence! 🚀**