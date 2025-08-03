"""
Scout Agent - Content Discovery Implementation
Handles RSS/feed monitoring, web scraping, and content deduplication
"""

import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import json

import httpx
from bs4 import BeautifulSoup
import feedparser

# Import base classes from the architecture
import sys
import os
import importlib.util

# Add paths for architecture import
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Try importing architecture
try:
    from multi_agent_architecture import BaseAgent, AgentTask, ContentItem, AgentStatus
except ImportError:
    # Load from file directly
    arch_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'multi-agent-architecture.py')
    spec = importlib.util.spec_from_file_location("multi_agent_architecture", arch_path)
    arch_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(arch_module)
    BaseAgent = arch_module.BaseAgent
    AgentTask = arch_module.AgentTask
    ContentItem = arch_module.ContentItem
    AgentStatus = arch_module.AgentStatus

logger = logging.getLogger(__name__)

@dataclass
class SourceMetrics:
    """Track performance metrics for each RSS source"""
    url: str
    name: str
    last_scraped: Optional[datetime] = None
    last_success: Optional[datetime] = None
    success_count: int = 0
    error_count: int = 0
    avg_articles_per_scrape: float = 0.0
    total_articles_discovered: int = 0
    response_time_avg: float = 0.0
    is_active: bool = True
    last_error: Optional[str] = None

class ScoutAgent(BaseAgent):
    """
    Scout Agent Implementation
    
    RESPONSIBILITIES:
    - Real-time RSS/feed monitoring (every 30 minutes)
    - Web scraping with anti-bot protection
    - Content deduplication and initial filtering
    - Source reliability tracking
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        
        # Configuration
        self.rss_feeds = config.get("rss_feeds", [])
        self.scraping_interval = config.get("scraping_interval", 30)  # minutes
        self.max_concurrent_scrapes = config.get("max_concurrent_scrapes", 5)
        self.max_articles_per_source = config.get("max_articles_per_source", 10)
        self.content_freshness_hours = config.get("content_freshness_hours", 48)
        self.rate_limit_delay = config.get("rate_limit_delay", 2.0)  # seconds
        
        # HTTP client configuration
        self.session = httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/rss+xml, application/xml, text/xml, text/html, application/xhtml+xml, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            },
            timeout=30.0,
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        
        # Content storage
        self.discovered_content: List[ContentItem] = []
        self.content_hashes: set = set()  # For deduplication
        self.source_metrics: Dict[str, SourceMetrics] = {}
        
        logger.info(f"ScoutAgent {agent_id} initialized with {len(self.rss_feeds)} RSS feeds")
    
    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Process content discovery tasks
        
        Task Types:
        - "discover_rss": Monitor RSS feeds
        - "scrape_url": Extract content from specific URL  
        - "search_query": Search for content by keywords
        """
        try:
            self.status = AgentStatus.WORKING
            task_type = task.data.get("type")
            
            logger.info(f"ScoutAgent processing task: {task_type}")
            
            if task_type == "discover_rss":
                return await self._discover_from_rss(task.data.get("feeds", self.rss_feeds))
            elif task_type == "scrape_url":
                return await self._scrape_single_url(task.data.get("url"))
            elif task_type == "search_query":
                return await self._search_content(task.data.get("query"))
            elif task_type == "get_metrics":
                return await self._get_source_metrics()
            else:
                return {"status": "error", "message": f"Unknown task type: {task_type}"}
                
        except Exception as e:
            logger.error(f"ScoutAgent task processing error: {e}")
            self.status = AgentStatus.ERROR
            return {"status": "error", "message": str(e)}
        finally:
            if self.status != AgentStatus.ERROR:
                self.status = AgentStatus.COMPLETED
    
    async def _discover_from_rss(self, feeds: List[str]) -> Dict[str, Any]:
        """
        Discover content from RSS feeds with error handling and metrics
        """
        results = {
            "status": "success",
            "feeds_processed": 0,
            "articles_discovered": 0,
            "new_articles": 0,
            "duplicates_filtered": 0,
            "errors": [],
            "articles": []
        }
        
        # Limit concurrent processing
        semaphore = asyncio.Semaphore(self.max_concurrent_scrapes)
        
        async def process_single_feed(feed_url: str) -> Dict[str, Any]:
            async with semaphore:
                return await self._process_rss_feed(feed_url)
        
        # Process feeds concurrently
        feed_tasks = [process_single_feed(feed_url) for feed_url in feeds[:10]]  # Limit feeds
        feed_results = await asyncio.gather(*feed_tasks, return_exceptions=True)
        
        # Aggregate results
        for i, result in enumerate(feed_results):
            feed_url = feeds[i] if i < len(feeds) else "unknown"
            
            if isinstance(result, Exception):
                error_msg = f"Feed {feed_url}: {str(result)}"
                results["errors"].append(error_msg)
                logger.error(error_msg)
                continue
            
            if result.get("status") == "success":
                results["feeds_processed"] += 1
                results["articles_discovered"] += result.get("articles_found", 0)
                results["new_articles"] += result.get("new_articles", 0)
                results["duplicates_filtered"] += result.get("duplicates", 0)
                results["articles"].extend(result.get("articles", []))
            else:
                results["errors"].append(f"Feed {feed_url}: {result.get('error', 'Unknown error')}")
        
        logger.info(f"RSS Discovery completed: {results['feeds_processed']} feeds, {results['new_articles']} new articles")
        return results
    
    async def _process_rss_feed(self, feed_url: str) -> Dict[str, Any]:
        """
        Process a single RSS feed with metrics tracking
        """
        start_time = datetime.now()
        
        # Initialize or get source metrics
        if feed_url not in self.source_metrics:
            self.source_metrics[feed_url] = SourceMetrics(
                url=feed_url,
                name=self._extract_domain_name(feed_url)
            )
        
        metrics = self.source_metrics[feed_url]
        metrics.last_scraped = start_time
        
        try:
            # Fetch RSS feed
            response = await self.session.get(feed_url)
            response.raise_for_status()
            
            # Parse RSS feed
            feed = feedparser.parse(response.text)
            
            if feed.bozo and feed.bozo_exception:
                logger.warning(f"RSS parsing warning for {feed_url}: {feed.bozo_exception}")
            
            articles = []
            new_articles = 0
            duplicates = 0
            
            # Process feed entries
            for entry in feed.entries[:self.max_articles_per_source]:
                try:
                    article_data = await self._extract_article_from_entry(entry, feed_url)
                    
                    if article_data and self._is_content_fresh(article_data):
                        if self._is_duplicate(article_data):
                            duplicates += 1
                        else:
                            # Create ContentItem
                            content_item = ContentItem(
                                url=article_data["url"],
                                title=article_data["title"],
                                content=article_data.get("content", ""),
                                source=feed_url,
                                discovered_at=datetime.now(),
                                agent_metadata={
                                    "scout_agent_id": self.agent_id,
                                    "feed_title": feed.feed.get("title", ""),
                                    "entry_id": getattr(entry, 'id', ''),
                                    "published_parsed": getattr(entry, 'published_parsed', None)
                                }
                            )
                            
                            # Add to discovered content and hash set
                            self.discovered_content.append(content_item)
                            self.content_hashes.add(article_data["content_hash"])
                            articles.append(asdict(content_item))
                            new_articles += 1
                            
                            # Rate limiting
                            await asyncio.sleep(self.rate_limit_delay)
                
                except Exception as e:
                    logger.warning(f"Error processing entry from {feed_url}: {e}")
                    continue
            
            # Update metrics
            response_time = (datetime.now() - start_time).total_seconds()
            metrics.last_success = datetime.now()
            metrics.success_count += 1
            metrics.total_articles_discovered += new_articles
            metrics.avg_articles_per_scrape = (
                (metrics.avg_articles_per_scrape * (metrics.success_count - 1) + new_articles) / 
                metrics.success_count
            )
            metrics.response_time_avg = (
                (metrics.response_time_avg * (metrics.success_count - 1) + response_time) / 
                metrics.success_count
            )
            
            return {
                "status": "success",
                "articles_found": len(feed.entries),
                "new_articles": new_articles,
                "duplicates": duplicates,
                "articles": articles,
                "response_time": response_time
            }
            
        except Exception as e:
            # Update error metrics
            metrics.error_count += 1
            metrics.last_error = str(e)
            
            logger.error(f"Error processing RSS feed {feed_url}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "articles_found": 0,
                "new_articles": 0,
                "duplicates": 0,
                "articles": []
            }
    
    async def _extract_article_from_entry(self, entry, feed_url: str) -> Optional[Dict[str, Any]]:
        """
        Extract article data from RSS entry
        """
        try:
            # Basic article data
            article_data = {
                "url": getattr(entry, 'link', ''),
                "title": getattr(entry, 'title', ''),
                "summary": getattr(entry, 'summary', ''),
                "published_date": self._parse_published_date(entry),
                "source": feed_url
            }
            
            # Skip if no URL
            if not article_data["url"]:
                return None
            
            # Try to extract full content
            try:
                content = await self._extract_article_content(article_data["url"])
                article_data["content"] = content or article_data["summary"]
            except Exception as e:
                logger.debug(f"Could not extract full content from {article_data['url']}: {e}")
                article_data["content"] = article_data["summary"]
            
            # Generate content hash for deduplication
            content_for_hash = f"{article_data['title']}{article_data['content']}"
            article_data["content_hash"] = hashlib.md5(content_for_hash.encode()).hexdigest()
            
            return article_data
            
        except Exception as e:
            logger.warning(f"Error extracting article from entry: {e}")
            return None
    
    async def _extract_article_content(self, url: str) -> Optional[str]:
        """
        Extract full article content with bot protection bypass
        """
        try:
            response = await self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'aside', 'header', 'advertisement']):
                element.decompose()
            
            # Try common article selectors
            content_selectors = [
                'article',
                '.article-content',
                '.post-content', 
                '.entry-content',
                '.content',
                '.article-body',
                '[role="main"]',
                'main'
            ]
            
            content = ""
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text(strip=True, separator=' ')
                    break
            
            # Fallback to body if no specific content found
            if not content and soup.body:
                content = soup.body.get_text(strip=True, separator=' ')
            
            # Clean and limit content
            content = ' '.join(content.split())  # Normalize whitespace
            return content[:5000] if content else None  # Limit content length
            
        except Exception as e:
            logger.debug(f"Error extracting content from {url}: {e}")
            return None
    
    async def _scrape_single_url(self, url: str) -> Dict[str, Any]:
        """
        Scrape content from a single URL
        """
        try:
            content = await self._extract_article_content(url)
            
            if content:
                # Create basic article data
                article_data = {
                    "url": url,
                    "title": "",  # Would need to extract from content
                    "content": content,
                    "source": url,
                    "discovered_at": datetime.now(),
                    "content_hash": hashlib.md5(content.encode()).hexdigest()
                }
                
                return {
                    "status": "success",
                    "article": article_data
                }
            else:
                return {
                    "status": "error",
                    "message": "Could not extract content from URL"
                }
                
        except Exception as e:
            return {
                "status": "error", 
                "message": str(e)
            }
    
    async def _search_content(self, query: str) -> Dict[str, Any]:
        """
        Search for content by keywords (placeholder for future implementation)
        """
        # This would integrate with search APIs or web search
        # For now, return a placeholder response
        return {
            "status": "not_implemented",
            "message": f"Search functionality for query '{query}' not yet implemented"
        }
    
    def _is_content_fresh(self, article_data: Dict[str, Any]) -> bool:
        """
        Check if content is within freshness window
        """
        if "published_date" not in article_data or not article_data["published_date"]:
            return True  # If no date, assume fresh
        
        published_date = article_data["published_date"]
        if isinstance(published_date, str):
            try:
                published_date = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
            except ValueError:
                return True  # If date parsing fails, assume fresh
        
        cutoff_date = datetime.now() - timedelta(hours=self.content_freshness_hours)
        return published_date >= cutoff_date
    
    def _is_duplicate(self, article_data: Dict[str, Any]) -> bool:
        """
        Check if content is duplicate based on hash
        """
        return article_data.get("content_hash") in self.content_hashes
    
    def _parse_published_date(self, entry) -> datetime:
        """
        Parse published date from RSS entry
        """
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                import time
                return datetime.fromtimestamp(time.mktime(entry.published_parsed))
            except (ValueError, TypeError):
                pass
        
        if hasattr(entry, 'published'):
            try:
                from dateutil import parser
                return parser.parse(entry.published)
            except (ValueError, ImportError):
                pass
        
        # Fallback to current time
        return datetime.now()
    
    def _extract_domain_name(self, url: str) -> str:
        """
        Extract clean domain name from URL
        """
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception:
            return url
    
    async def _get_source_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for all sources
        """
        metrics_data = []
        
        for url, metrics in self.source_metrics.items():
            metrics_dict = asdict(metrics)
            
            # Convert datetime objects to ISO strings
            for key, value in metrics_dict.items():
                if isinstance(value, datetime):
                    metrics_dict[key] = value.isoformat()
            
            # Calculate success rate
            total_attempts = metrics.success_count + metrics.error_count
            metrics_dict["success_rate"] = (
                metrics.success_count / total_attempts if total_attempts > 0 else 0.0
            )
            
            metrics_data.append(metrics_dict)
        
        return {
            "status": "success",
            "total_sources": len(self.source_metrics),
            "total_content_discovered": len(self.discovered_content),
            "unique_content_hashes": len(self.content_hashes),
            "source_metrics": metrics_data
        }
    
    async def health_check(self) -> bool:
        """
        Check if RSS feeds are accessible and scraping works
        """
        try:
            # Test a few RSS feeds
            test_feeds = self.rss_feeds[:3] if self.rss_feeds else []
            
            for feed_url in test_feeds:
                try:
                    response = await self.session.get(feed_url, timeout=10.0)
                    if response.status_code != 200:
                        logger.warning(f"Health check failed for {feed_url}: Status {response.status_code}")
                        return False
                except Exception as e:
                    logger.warning(f"Health check failed for {feed_url}: {e}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"ScoutAgent health check error: {e}")
            return False
    
    async def cleanup(self):
        """
        Cleanup resources
        """
        if hasattr(self, 'session'):
            await self.session.aclose()
        logger.info(f"ScoutAgent {self.agent_id} cleaned up")