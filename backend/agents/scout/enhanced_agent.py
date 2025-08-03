"""
Enhanced Scout Agent with Advanced Scraping and Search
Integrates advanced scraping, search functionality, and YouTube content discovery
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import json

# Import original Scout Agent and base classes
from agent import ScoutAgent, SourceMetrics, AgentStatus

# Import enhanced capabilities
from advanced_scraper import AdvancedScraper, SearchResult

# Import integrations
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'integrations'))
from klavis_youtube import KlavisYouTubeIntegration, YouTubeVideo

logger = logging.getLogger(__name__)

@dataclass
class EnhancedContentItem:
    """Enhanced content item with additional metadata"""
    url: str
    title: str
    content: str
    source: str
    discovered_at: datetime
    content_type: str = "rss"  # rss, web, youtube, search
    quality_score: float = 0.0
    ai_relevance: float = 0.0
    category: str = ""
    sentiment: str = ""
    processing_status: str = "new"
    agent_metadata: Dict[str, Any] = None
    
    # Enhanced fields
    description: str = ""
    keywords: List[str] = None
    content_length: int = 0
    scraped_with: str = ""
    search_query: str = ""
    relevance_score: float = 0.0
    
    # YouTube specific
    video_duration: str = ""
    view_count: int = 0
    channel_name: str = ""
    transcript: str = ""
    video_summary: str = ""

class EnhancedScoutAgent(ScoutAgent):
    """
    Enhanced Scout Agent with advanced scraping and search capabilities
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        
        # Enhanced configuration
        self.enable_advanced_scraping = config.get("enable_advanced_scraping", True)
        self.enable_search = config.get("enable_search", True)
        self.enable_youtube = config.get("enable_youtube", True)
        self.search_queries = config.get("search_queries", self._default_search_queries())
        self.youtube_search_limit = config.get("youtube_search_limit", 10)
        self.web_search_limit = config.get("web_search_limit", 20)
        
        # Initialize enhanced components
        self.advanced_scraper = None
        self.youtube_integration = None
        
        if self.enable_advanced_scraping:
            scraper_config = {
                "use_scrapling": config.get("use_scrapling", True),
                "max_retries": config.get("scraper_max_retries", 3),
                "retry_delay": config.get("scraper_retry_delay", 5.0),
                "request_timeout": config.get("scraper_timeout", 30.0),
                "enable_search": self.enable_search,
                "bing_api_key": config.get("bing_api_key"),
                "google_api_key": config.get("google_api_key"),
                "google_cse_id": config.get("google_cse_id"),
                "serpapi_key": config.get("serpapi_key")
            }
            self.advanced_scraper = AdvancedScraper(scraper_config)
        
        if self.enable_youtube:
            youtube_config = {
                "klavis_api_key": config.get("klavis_api_key"),
                "anthropic_api_key": config.get("anthropic_api_key"),
                "aec_search_queries": config.get("youtube_search_queries", self._youtube_search_queries())
            }
            self.youtube_integration = KlavisYouTubeIntegration(youtube_config)
        
        # Enhanced storage
        self.enhanced_content: List[EnhancedContentItem] = []
        self.search_results: List[SearchResult] = []
        self.youtube_videos: List[YouTubeVideo] = []
        
        logger.info(f"EnhancedScoutAgent {agent_id} initialized - Advanced: {self.enable_advanced_scraping}, Search: {self.enable_search}, YouTube: {self.enable_youtube}")
    
    async def process_task(self, task) -> Dict[str, Any]:
        """
        Enhanced task processing with new task types
        """
        try:
            self.status = AgentStatus.WORKING
            task_type = task.data.get("type")
            
            logger.info(f"EnhancedScoutAgent processing task: {task_type}")
            
            # Original task types
            if task_type == "discover_rss":
                return await self._discover_from_rss(task.data.get("feeds", self.rss_feeds))
            elif task_type == "scrape_url":
                return await self._scrape_single_url(task.data.get("url"))
            elif task_type == "get_metrics":
                return await self._get_source_metrics()
            
            # Enhanced task types
            elif task_type == "scrape_url_advanced":
                return await self._scrape_url_advanced(task.data.get("url"))
            elif task_type == "search_web":
                return await self._search_web_content(task.data.get("query"), task.data.get("max_results", 10))
            elif task_type == "search_youtube":
                return await self._search_youtube_content(task.data.get("max_videos", 10))
            elif task_type == "process_youtube_video":
                return await self._process_youtube_video(task.data.get("video_url"))
            elif task_type == "comprehensive_discovery":
                return await self._comprehensive_content_discovery(task.data)
            elif task_type == "get_enhanced_content":
                return await self._get_enhanced_content(task.data)
            else:
                return {"status": "error", "message": f"Unknown task type: {task_type}"}
                
        except Exception as e:
            logger.error(f"EnhancedScoutAgent task processing error: {e}")
            self.status = AgentStatus.ERROR
            return {"status": "error", "message": str(e)}
        finally:
            if self.status != AgentStatus.ERROR:
                self.status = AgentStatus.COMPLETED
    
    async def _scrape_url_advanced(self, url: str) -> Dict[str, Any]:
        """
        Advanced URL scraping with anti-bot protection
        """
        if not self.advanced_scraper:
            return {"status": "error", "message": "Advanced scraper not available"}
        
        try:
            result = await self.advanced_scraper.scrape_url_advanced(url)
            
            if result:
                # Convert to EnhancedContentItem
                enhanced_item = EnhancedContentItem(
                    url=result["url"],
                    title=result["title"],
                    content=result["content"],
                    source=url,
                    discovered_at=result["scraped_at"],
                    content_type="web_advanced",
                    description=result.get("description", ""),
                    keywords=result.get("keywords", []),
                    content_length=result.get("content_length", 0),
                    scraped_with=result.get("scraper", ""),
                    agent_metadata={
                        "session_id": result.get("session_id"),
                        "scraper_type": result.get("scraper")
                    }
                )
                
                self.enhanced_content.append(enhanced_item)
                
                return {
                    "status": "success",
                    "content_item": asdict(enhanced_item),
                    "scraper_used": result.get("scraper"),
                    "content_length": result.get("content_length", 0)
                }
            else:
                return {"status": "error", "message": "Failed to scrape URL"}
                
        except Exception as e:
            logger.error(f"Advanced scraping error for {url}: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _search_web_content(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Search web content using available search APIs
        """
        if not self.advanced_scraper or not self.enable_search:
            return {"status": "error", "message": "Web search not available"}
        
        try:
            search_results = await self.advanced_scraper.search_web(query, max_results)
            
            enhanced_items = []
            
            # Process search results and scrape content
            for result in search_results:
                try:
                    # Scrape content from search result URL
                    scraped_content = await self.advanced_scraper.scrape_url_advanced(result.url, use_fallback=True)
                    
                    if scraped_content:
                        enhanced_item = EnhancedContentItem(
                            url=result.url,
                            title=result.title or scraped_content.get("title", ""),
                            content=scraped_content.get("content", result.snippet),
                            source=result.source,
                            discovered_at=datetime.now(),
                            content_type="search",
                            description=result.snippet,
                            content_length=scraped_content.get("content_length", 0),
                            scraped_with=scraped_content.get("scraper", ""),
                            search_query=query,
                            relevance_score=result.relevance_score,
                            agent_metadata={
                                "search_source": result.source,
                                "search_query": query,
                                "search_snippet": result.snippet
                            }
                        )
                        
                        enhanced_items.append(enhanced_item)
                        self.enhanced_content.append(enhanced_item)
                    
                except Exception as e:
                    logger.warning(f"Error processing search result {result.url}: {e}")
                    continue
            
            self.search_results.extend(search_results)
            
            return {
                "status": "success",
                "query": query,
                "search_results_found": len(search_results),
                "content_extracted": len(enhanced_items),
                "enhanced_items": [asdict(item) for item in enhanced_items],
                "search_sources_used": list(set(r.source for r in search_results))
            }
            
        except Exception as e:
            logger.error(f"Web search error for '{query}': {e}")
            return {"status": "error", "message": str(e)}
    
    async def _search_youtube_content(self, max_videos: int = 10) -> Dict[str, Any]:
        """
        Search YouTube for AEC AI content
        """
        if not self.youtube_integration or not self.enable_youtube:
            return {"status": "error", "message": "YouTube search not available"}
        
        try:
            youtube_videos = await self.youtube_integration.search_aec_videos(max_videos)
            
            enhanced_items = []
            
            for video in youtube_videos:
                enhanced_item = EnhancedContentItem(
                    url=video.url,
                    title=video.title,
                    content=video.transcript or video.description,
                    source="youtube",
                    discovered_at=video.scraped_at,
                    content_type="youtube",
                    description=video.description,
                    keywords=video.tags or [],
                    content_length=len(video.transcript) if video.transcript else len(video.description),
                    relevance_score=video.relevance_score,
                    
                    # YouTube specific fields
                    video_duration=video.duration,
                    view_count=video.view_count,
                    channel_name=video.channel_name,
                    transcript=video.transcript,
                    video_summary=video.summary,
                    
                    agent_metadata={
                        "video_id": video.video_id,
                        "published_date": video.published_date.isoformat() if video.published_date else None,
                        "view_count": video.view_count,
                        "duration": video.duration
                    }
                )
                
                enhanced_items.append(enhanced_item)
                self.enhanced_content.append(enhanced_item)
            
            self.youtube_videos.extend(youtube_videos)
            
            return {
                "status": "success",
                "videos_found": len(youtube_videos),
                "enhanced_items": [asdict(item) for item in enhanced_items],
                "average_relevance": sum(v.relevance_score for v in youtube_videos) / len(youtube_videos) if youtube_videos else 0,
                "channels_discovered": list(set(v.channel_name for v in youtube_videos if v.channel_name))
            }
            
        except Exception as e:
            logger.error(f"YouTube search error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _process_youtube_video(self, video_url: str) -> Dict[str, Any]:
        """
        Process a specific YouTube video
        """
        if not self.youtube_integration:
            return {"status": "error", "message": "YouTube integration not available"}
        
        try:
            video = await self.youtube_integration.process_specific_video(video_url)
            
            if video:
                enhanced_item = EnhancedContentItem(
                    url=video.url,
                    title=video.title,
                    content=video.transcript or video.description,
                    source="youtube",
                    discovered_at=video.scraped_at,
                    content_type="youtube_specific",
                    description=video.description,
                    keywords=video.tags or [],
                    content_length=len(video.transcript) if video.transcript else len(video.description),
                    relevance_score=video.relevance_score,
                    video_duration=video.duration,
                    view_count=video.view_count,
                    channel_name=video.channel_name,
                    transcript=video.transcript,
                    video_summary=video.summary,
                    agent_metadata={
                        "video_id": video.video_id,
                        "processed_specifically": True
                    }
                )
                
                self.enhanced_content.append(enhanced_item)
                self.youtube_videos.append(video)
                
                return {
                    "status": "success",
                    "video": asdict(video),
                    "enhanced_item": asdict(enhanced_item),
                    "has_transcript": bool(video.transcript),
                    "has_summary": bool(video.summary)
                }
            else:
                return {"status": "error", "message": "Failed to process video"}
                
        except Exception as e:
            logger.error(f"YouTube video processing error for {video_url}: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _comprehensive_content_discovery(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive content discovery using all available methods
        """
        try:
            results = {
                "status": "success",
                "discovery_methods": [],
                "total_content_found": 0,
                "rss_results": {},
                "search_results": {},
                "youtube_results": {},
                "errors": []
            }
            
            # RSS Discovery
            if task_data.get("include_rss", True):
                try:
                    rss_result = await self._discover_from_rss(self.rss_feeds)
                    results["rss_results"] = rss_result
                    results["discovery_methods"].append("rss")
                    results["total_content_found"] += rss_result.get("new_articles", 0)
                except Exception as e:
                    results["errors"].append(f"RSS discovery error: {str(e)}")
            
            # Web Search
            if task_data.get("include_search", True) and self.enable_search:
                try:
                    search_queries = task_data.get("search_queries", self.search_queries)
                    all_search_results = []
                    
                    for query in search_queries:
                        search_result = await self._search_web_content(query, 5)
                        if search_result.get("status") == "success":
                            all_search_results.extend(search_result.get("enhanced_items", []))
                    
                    results["search_results"] = {
                        "queries_processed": len(search_queries),
                        "content_found": len(all_search_results),
                        "items": all_search_results
                    }
                    results["discovery_methods"].append("web_search")
                    results["total_content_found"] += len(all_search_results)
                    
                except Exception as e:
                    results["errors"].append(f"Web search error: {str(e)}")
            
            # YouTube Discovery
            if task_data.get("include_youtube", True) and self.enable_youtube:
                try:
                    youtube_result = await self._search_youtube_content(self.youtube_search_limit)
                    results["youtube_results"] = youtube_result
                    results["discovery_methods"].append("youtube")
                    results["total_content_found"] += youtube_result.get("videos_found", 0)
                except Exception as e:
                    results["errors"].append(f"YouTube discovery error: {str(e)}")
            
            logger.info(f"Comprehensive discovery completed: {results['total_content_found']} items from {len(results['discovery_methods'])} methods")
            
            return results
            
        except Exception as e:
            logger.error(f"Comprehensive discovery error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _get_enhanced_content(self, filter_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get enhanced content with filtering options
        """
        try:
            content_type_filter = filter_data.get("content_type")  # rss, web, youtube, search
            min_relevance = filter_data.get("min_relevance", 0.0)
            max_items = filter_data.get("max_items", 50)
            include_youtube = filter_data.get("include_youtube", True)
            include_search = filter_data.get("include_search", True)
            
            filtered_content = []
            
            for item in self.enhanced_content:
                # Apply filters
                if content_type_filter and item.content_type != content_type_filter:
                    continue
                
                if item.relevance_score < min_relevance:
                    continue
                
                if not include_youtube and item.content_type == "youtube":
                    continue
                
                if not include_search and item.content_type == "search":
                    continue
                
                filtered_content.append(item)
            
            # Sort by relevance and discovery time
            sorted_content = sorted(
                filtered_content,
                key=lambda x: (x.relevance_score, x.discovered_at),
                reverse=True
            )
            
            limited_content = sorted_content[:max_items]
            
            # Group by content type
            by_type = {}
            for item in limited_content:
                content_type = item.content_type
                if content_type not in by_type:
                    by_type[content_type] = []
                by_type[content_type].append(asdict(item))
            
            return {
                "status": "success",
                "total_available": len(self.enhanced_content),
                "filtered_count": len(filtered_content),
                "returned_count": len(limited_content),
                "content_by_type": by_type,
                "all_content": [asdict(item) for item in limited_content],
                "filters_applied": filter_data
            }
            
        except Exception as e:
            logger.error(f"Error getting enhanced content: {e}")
            return {"status": "error", "message": str(e)}
    
    def _default_search_queries(self) -> List[str]:
        """Default search queries for AEC AI content"""
        return [
            "AI construction industry 2024",
            "artificial intelligence architecture design",
            "BIM machine learning integration",
            "construction automation robotics",
            "smart buildings IoT AI",
            "digital twins construction industry",
            "parametric design artificial intelligence",
            "project management AI construction"
        ]
    
    def _youtube_search_queries(self) -> List[str]:
        """YouTube specific search queries"""
        return [
            "AI construction",
            "artificial intelligence architecture",
            "BIM artificial intelligence",
            "construction automation",
            "smart buildings AI",
            "digital twins construction",
            "robotics construction",
            "machine learning architecture"
        ]
    
    async def health_check(self) -> bool:
        """Enhanced health check including advanced components"""
        try:
            # Original health check
            base_health = await super().health_check()
            
            # Check advanced scraper
            advanced_health = True
            if self.advanced_scraper:
                try:
                    # Simple test of advanced scraper
                    test_result = await self.advanced_scraper.scrape_url_advanced("https://httpbin.org/get", use_fallback=True)
                    advanced_health = test_result is not None
                except Exception:
                    advanced_health = False
            
            # Check YouTube integration
            youtube_health = True
            if self.youtube_integration:
                youtube_health = self.youtube_integration.klavis_client is not None
            
            overall_health = base_health and (not self.enable_advanced_scraping or advanced_health)
            
            logger.info(f"Enhanced health check - Base: {base_health}, Advanced: {advanced_health}, YouTube: {youtube_health}")
            return overall_health
            
        except Exception as e:
            logger.error(f"Enhanced health check error: {e}")
            return False
    
    async def cleanup(self):
        """Enhanced cleanup including advanced components"""
        try:
            # Original cleanup
            await super().cleanup()
            
            # Cleanup advanced scraper
            if self.advanced_scraper:
                await self.advanced_scraper.cleanup()
            
            # Cleanup YouTube integration
            if self.youtube_integration:
                await self.youtube_integration.cleanup()
            
            logger.info(f"EnhancedScoutAgent {self.agent_id} cleaned up")
            
        except Exception as e:
            logger.error(f"Enhanced cleanup error: {e}")