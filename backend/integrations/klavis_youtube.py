"""
Klavis YouTube Integration for AEC AI News
Searches and extracts content from YouTube videos related to AEC and AI
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Klavis integration (will be installed)
try:
    from klavis import Klavis
    from klavis.types import McpServerName, ToolFormat
    KLAVIS_AVAILABLE = True
except ImportError:
    KLAVIS_AVAILABLE = False
    Klavis = None

# Anthropic integration (optional for enhanced processing)
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    Anthropic = None

logger = logging.getLogger(__name__)

@dataclass
class YouTubeVideo:
    """YouTube video content structure"""
    video_id: str
    title: str
    url: str
    description: str
    transcript: str = ""
    summary: str = ""
    duration: str = ""
    published_date: Optional[datetime] = None
    view_count: int = 0
    channel_name: str = ""
    relevance_score: float = 0.0
    tags: List[str] = None
    scraped_at: datetime = None

class KlavisYouTubeIntegration:
    """
    YouTube content discovery and analysis using Klavis MCP
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.klavis_api_key = config.get("klavis_api_key") or os.getenv("KLAVIS_API_KEY")
        self.anthropic_api_key = config.get("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY")
        
        # Search queries for AEC AI content
        self.aec_search_queries = config.get("aec_search_queries", [
            "AI in construction",
            "artificial intelligence architecture",
            "BIM artificial intelligence",
            "construction automation AI",
            "smart buildings AI",
            "digital twins construction",
            "parametric design AI",
            "robotics construction",
            "machine learning architecture",
            "AI project management construction"
        ])
        
        # Initialize clients
        self.klavis_client = None
        self.anthropic_client = None
        self.youtube_mcp_instance = None
        
        if not KLAVIS_AVAILABLE:
            logger.warning("Klavis not available - YouTube integration disabled")
            return
        
        if self.klavis_api_key:
            try:
                self.klavis_client = Klavis(api_key=self.klavis_api_key)
                self._initialize_youtube_mcp()
                logger.info("Klavis YouTube integration initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Klavis: {e}")
        
        if self.anthropic_api_key and ANTHROPIC_AVAILABLE:
            try:
                self.anthropic_client = Anthropic(api_key=self.anthropic_api_key)
                logger.info("Anthropic client initialized for enhanced processing")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic: {e}")
    
    def _initialize_youtube_mcp(self):
        """Initialize YouTube MCP server instance"""
        try:
            self.youtube_mcp_instance = self.klavis_client.mcp_server.create_server_instance(
                server_name=McpServerName.YOUTUBE,
                user_id="aec-ai-news",
                platform_name="AEC_AI_News",
            )
            logger.info(f"YouTube MCP server created: {self.youtube_mcp_instance.server_url}")
        except Exception as e:
            logger.error(f"Failed to create YouTube MCP server: {e}")
    
    async def search_aec_videos(self, max_videos: int = 20) -> List[YouTubeVideo]:
        """
        Search for AEC AI related YouTube videos
        """
        if not self.klavis_client or not self.youtube_mcp_instance:
            logger.warning("Klavis YouTube not available")
            return []
        
        all_videos = []
        
        for query in self.aec_search_queries:
            try:
                videos = await self._search_videos_by_query(query, max_videos // len(self.aec_search_queries))
                all_videos.extend(videos)
            except Exception as e:
                logger.error(f"Error searching for '{query}': {e}")
        
        # Remove duplicates and sort by relevance
        unique_videos = self._deduplicate_videos(all_videos)
        sorted_videos = sorted(unique_videos, key=lambda v: v.relevance_score, reverse=True)
        
        return sorted_videos[:max_videos]
    
    async def _search_videos_by_query(self, query: str, max_results: int = 5) -> List[YouTubeVideo]:
        """
        Search YouTube for videos matching a specific query
        """
        try:
            # Get MCP tools
            mcp_tools = self.klavis_client.mcp_server.list_tools(
                server_url=self.youtube_mcp_instance.server_url,
                format=ToolFormat.ANTHROPIC,
            )
            
            # Search for videos
            search_result = self.klavis_client.mcp_server.call_tools(
                server_url=self.youtube_mcp_instance.server_url,
                tool_name="search_videos",
                tool_args={
                    "query": query,
                    "max_results": max_results,
                    "order": "relevance"
                },
            )
            
            videos = []
            
            if search_result and hasattr(search_result, 'items'):
                for item in search_result.items[:max_results]:
                    video = await self._process_video_item(item, query)
                    if video:
                        videos.append(video)
            
            return videos
            
        except Exception as e:
            logger.error(f"Error in video search for '{query}': {e}")
            return []
    
    async def _process_video_item(self, video_item: Any, search_query: str) -> Optional[YouTubeVideo]:
        """
        Process a single video item from search results
        """
        try:
            video_id = self._extract_video_id(video_item)
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            # Get video details
            video_details = await self._get_video_details(video_url)
            
            if not video_details:
                return None
            
            # Calculate relevance score
            relevance_score = self._calculate_aec_relevance(
                video_details.get("title", ""),
                video_details.get("description", ""),
                search_query
            )
            
            # Get transcript if available
            transcript = await self._get_video_transcript(video_url)
            
            # Generate summary if we have Anthropic
            summary = ""
            if transcript and self.anthropic_client:
                summary = await self._generate_video_summary(video_details, transcript)
            
            video = YouTubeVideo(
                video_id=video_id,
                title=video_details.get("title", ""),
                url=video_url,
                description=video_details.get("description", ""),
                transcript=transcript,
                summary=summary,
                duration=video_details.get("duration", ""),
                published_date=self._parse_published_date(video_details.get("published_date")),
                view_count=video_details.get("view_count", 0),
                channel_name=video_details.get("channel_name", ""),
                relevance_score=relevance_score,
                tags=video_details.get("tags", []),
                scraped_at=datetime.now()
            )
            
            return video
            
        except Exception as e:
            logger.error(f"Error processing video item: {e}")
            return None
    
    def _extract_video_id(self, video_item: Any) -> str:
        """Extract video ID from search result item"""
        # This depends on the Klavis API response format
        if hasattr(video_item, 'id'):
            if hasattr(video_item.id, 'videoId'):
                return video_item.id.videoId
            elif isinstance(video_item.id, str):
                return video_item.id
        
        # Fallback extraction from URL
        if hasattr(video_item, 'url'):
            url = video_item.url
            if "watch?v=" in url:
                return url.split("watch?v=")[1].split("&")[0]
        
        return ""
    
    async def _get_video_details(self, video_url: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a video
        """
        try:
            result = self.klavis_client.mcp_server.call_tools(
                server_url=self.youtube_mcp_instance.server_url,
                tool_name="get_video_info",
                tool_args={"video_url": video_url},
            )
            
            if result:
                return {
                    "title": getattr(result, 'title', ''),
                    "description": getattr(result, 'description', ''),
                    "duration": getattr(result, 'duration', ''),
                    "published_date": getattr(result, 'published_date', ''),
                    "view_count": getattr(result, 'view_count', 0),
                    "channel_name": getattr(result, 'channel_name', ''),
                    "tags": getattr(result, 'tags', [])
                }
            
        except Exception as e:
            logger.error(f"Error getting video details for {video_url}: {e}")
        
        return None
    
    async def _get_video_transcript(self, video_url: str) -> str:
        """
        Get video transcript/captions
        """
        try:
            result = self.klavis_client.mcp_server.call_tools(
                server_url=self.youtube_mcp_instance.server_url,
                tool_name="get_transcript",
                tool_args={"video_url": video_url},
            )
            
            if result and hasattr(result, 'text'):
                return result.text
            
        except Exception as e:
            logger.debug(f"No transcript available for {video_url}: {e}")
        
        return ""
    
    async def _generate_video_summary(self, video_details: Dict[str, Any], transcript: str) -> str:
        """
        Generate AI summary of video content
        """
        if not self.anthropic_client:
            return ""
        
        try:
            prompt = f"""
Analyze this AEC (Architecture, Engineering, Construction) industry YouTube video and provide a concise summary focusing on AI and technology aspects.

Title: {video_details.get('title', '')}
Description: {video_details.get('description', '')[:500]}
Transcript: {transcript[:2000]}

Please provide:
1. A 2-sentence summary of the main content
2. Key AI/technology topics mentioned
3. Relevance to AEC industry (1-10 scale)
4. Key takeaways for AEC professionals

Keep the response concise and focused on actionable insights.
"""
            
            response = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",  # Use faster model for summaries
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text if response.content else ""
            
        except Exception as e:
            logger.error(f"Error generating video summary: {e}")
            return ""
    
    def _calculate_aec_relevance(self, title: str, description: str, search_query: str) -> float:
        """
        Calculate relevance score for AEC AI content
        """
        content = (title + " " + description).lower()
        
        # AEC keywords with weights
        aec_keywords = {
            'construction': 3.0, 'architecture': 3.0, 'engineering': 3.0,
            'bim': 4.0, 'building': 2.0, 'design': 2.0,
            'project management': 3.0, 'infrastructure': 2.5,
            'real estate': 2.0, 'facility': 2.0, 'contractor': 2.5
        }
        
        # AI keywords with weights
        ai_keywords = {
            'artificial intelligence': 4.0, 'ai': 3.0, 'machine learning': 3.5,
            'automation': 3.0, 'robotics': 3.5, 'digital twin': 4.0,
            'smart': 2.0, 'intelligent': 2.5, 'algorithm': 2.5,
            'neural network': 3.0, 'deep learning': 3.5
        }
        
        # Calculate scores
        aec_score = sum(weight for keyword, weight in aec_keywords.items() if keyword in content)
        ai_score = sum(weight for keyword, weight in ai_keywords.items() if keyword in content)
        
        # Bonus for search query match
        query_bonus = 2.0 if search_query.lower() in content else 0.0
        
        # Normalize to 0-1 range
        total_score = aec_score + ai_score + query_bonus
        max_possible = 15.0  # Approximate maximum reasonable score
        
        return min(1.0, total_score / max_possible)
    
    def _parse_published_date(self, date_str: str) -> Optional[datetime]:
        """Parse published date from various formats"""
        if not date_str:
            return None
        
        # Common YouTube date formats
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def _deduplicate_videos(self, videos: List[YouTubeVideo]) -> List[YouTubeVideo]:
        """Remove duplicate videos by video ID"""
        seen_ids = set()
        unique_videos = []
        
        for video in videos:
            if video.video_id not in seen_ids:
                seen_ids.add(video.video_id)
                unique_videos.append(video)
        
        return unique_videos
    
    async def process_specific_video(self, video_url: str) -> Optional[YouTubeVideo]:
        """
        Process a specific YouTube video URL
        """
        if not self.klavis_client or not self.youtube_mcp_instance:
            return None
        
        try:
            video_id = self._extract_video_id_from_url(video_url)
            video_details = await self._get_video_details(video_url)
            
            if not video_details:
                return None
            
            transcript = await self._get_video_transcript(video_url)
            summary = ""
            
            if transcript and self.anthropic_client:
                summary = await self._generate_video_summary(video_details, transcript)
            
            relevance_score = self._calculate_aec_relevance(
                video_details.get("title", ""),
                video_details.get("description", ""),
                "AEC AI"
            )
            
            return YouTubeVideo(
                video_id=video_id,
                title=video_details.get("title", ""),
                url=video_url,
                description=video_details.get("description", ""),
                transcript=transcript,
                summary=summary,
                duration=video_details.get("duration", ""),
                published_date=self._parse_published_date(video_details.get("published_date")),
                view_count=video_details.get("view_count", 0),
                channel_name=video_details.get("channel_name", ""),
                relevance_score=relevance_score,
                tags=video_details.get("tags", []),
                scraped_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error processing video {video_url}: {e}")
            return None
    
    def _extract_video_id_from_url(self, url: str) -> str:
        """Extract video ID from YouTube URL"""
        if "watch?v=" in url:
            return url.split("watch?v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            return url.split("youtu.be/")[1].split("?")[0]
        return ""
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.klavis_client and self.youtube_mcp_instance:
            try:
                # Cleanup MCP server instance if needed
                pass
            except Exception as e:
                logger.warning(f"Error cleaning up Klavis YouTube: {e}")
        
        logger.info("Klavis YouTube integration cleaned up")