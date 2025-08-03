"""
Advanced Web Scraper with Scrapling and Search Integration
Enhanced scraping capabilities for protected sites and search functionality
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup
import feedparser

# Scrapling integration (will be installed)
try:
    from scrapling import Adapter
    SCRAPLING_AVAILABLE = True
except ImportError:
    SCRAPLING_AVAILABLE = False
    Adapter = None

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Search result structure"""
    title: str
    url: str
    snippet: str
    source: str
    published_date: Optional[datetime] = None
    relevance_score: float = 0.0

@dataclass
class ScrapingSession:
    """Advanced scraping session with rotation"""
    session_id: str
    user_agent: str
    proxy: Optional[str] = None
    created_at: datetime = None
    requests_count: int = 0
    success_rate: float = 1.0
    is_blocked: bool = False

class AdvancedScraper:
    """
    Advanced web scraper with anti-bot protection and search capabilities
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.use_scrapling = config.get("use_scrapling", True) and SCRAPLING_AVAILABLE
        self.max_retries = config.get("max_retries", 3)
        self.retry_delay = config.get("retry_delay", 5.0)
        self.request_timeout = config.get("request_timeout", 30.0)
        self.enable_search = config.get("enable_search", True)
        
        # User agent rotation
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"
        ]
        
        # Initialize sessions
        self.scraping_sessions: List[ScrapingSession] = []
        self.current_session_index = 0
        
        # Search APIs configuration
        self.search_apis = {
            "bing": config.get("bing_api_key"),
            "google": config.get("google_api_key"),
            "serpapi": config.get("serpapi_key")
        }
        
        # Initialize Scrapling if available
        if self.use_scrapling:
            try:
                self.scrapling_adapter = Adapter()
                logger.info("Scrapling adapter initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Scrapling: {e}")
                self.use_scrapling = False
        
        # Initialize HTTP sessions
        self._initialize_sessions()
        
        logger.info(f"AdvancedScraper initialized - Scrapling: {self.use_scrapling}, Search: {self.enable_search}")
    
    def _initialize_sessions(self):
        """Initialize multiple scraping sessions with different configurations"""
        for i, user_agent in enumerate(self.user_agents):
            session = ScrapingSession(
                session_id=f"session-{i}",
                user_agent=user_agent,
                created_at=datetime.now()
            )
            self.scraping_sessions.append(session)
    
    def _get_next_session(self) -> ScrapingSession:
        """Get next available scraping session with rotation"""
        # Filter out blocked sessions
        available_sessions = [s for s in self.scraping_sessions if not s.is_blocked]
        
        if not available_sessions:
            # Reset all sessions if all are blocked
            for session in self.scraping_sessions:
                session.is_blocked = False
                session.requests_count = 0
            available_sessions = self.scraping_sessions
        
        # Use round-robin selection
        session = available_sessions[self.current_session_index % len(available_sessions)]
        self.current_session_index += 1
        
        return session
    
    async def scrape_url_advanced(self, url: str, use_fallback: bool = True) -> Optional[Dict[str, Any]]:
        """
        Advanced URL scraping with anti-bot protection
        """
        logger.info(f"Advanced scraping: {url}")
        
        # Try Scrapling first if available
        if self.use_scrapling:
            try:
                result = await self._scrape_with_scrapling(url)
                if result:
                    logger.info(f"Scrapling successful for {url}")
                    return result
            except Exception as e:
                logger.warning(f"Scrapling failed for {url}: {e}")
        
        # Fallback to advanced HTTP scraping
        if use_fallback:
            return await self._scrape_with_rotation(url)
        
        return None
    
    async def _scrape_with_scrapling(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape using Scrapling for protected sites
        """
        if not self.use_scrapling:
            return None
        
        try:
            # Use Scrapling with stealth mode
            response = self.scrapling_adapter.get(
                url,
                stealth=True,
                wait_for_selector="body",
                timeout=self.request_timeout
            )
            
            if response.ok:
                # Extract content using Scrapling's enhanced parsing
                title = response.css('title::text').get('').strip()
                
                # Try multiple content selectors
                content_selectors = [
                    'article',
                    '.article-content',
                    '.post-content',
                    '.entry-content',
                    '.content',
                    'main',
                    '.story-body',
                    '.article-body'
                ]
                
                content = ""
                for selector in content_selectors:
                    elements = response.css(f'{selector}::text').getall()
                    if elements:
                        content = ' '.join(elements)
                        break
                
                # Fallback to body text
                if not content:
                    content = response.css('body::text').get('')
                
                # Extract metadata
                description = response.css('meta[name="description"]::attr(content)').get('')
                keywords = response.css('meta[name="keywords"]::attr(content)').get('')
                
                return {
                    "url": url,
                    "title": title,
                    "content": self._clean_content(content),
                    "description": description,
                    "keywords": keywords.split(',') if keywords else [],
                    "scraped_at": datetime.now(),
                    "scraper": "scrapling",
                    "content_length": len(content)
                }
            
        except Exception as e:
            logger.error(f"Scrapling error for {url}: {e}")
            return None
    
    async def _scrape_with_rotation(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape with session rotation and advanced evasion
        """
        for attempt in range(self.max_retries):
            session = self._get_next_session()
            
            try:
                # Create HTTP client with session configuration
                async with httpx.AsyncClient(
                    headers={
                        "User-Agent": session.user_agent,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Accept-Encoding": "gzip, deflate, br",
                        "DNT": "1",
                        "Connection": "keep-alive",
                        "Upgrade-Insecure-Requests": "1",
                        "Sec-Fetch-Dest": "document",
                        "Sec-Fetch-Mode": "navigate",
                        "Sec-Fetch-Site": "none",
                        "Cache-Control": "max-age=0"
                    },
                    timeout=self.request_timeout,
                    follow_redirects=True
                ) as client:
                    
                    # Add random delay to appear more human
                    await asyncio.sleep(0.5 + (attempt * 0.3))
                    
                    response = await client.get(url)
                    
                    # Update session metrics
                    session.requests_count += 1
                    
                    if response.status_code == 200:
                        # Parse content
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Remove unwanted elements
                        for element in soup(['script', 'style', 'nav', 'footer', 'aside', 'header', 'advertisement', 'iframe']):
                            element.decompose()
                        
                        # Extract title
                        title_tag = soup.find('title')
                        title = title_tag.get_text().strip() if title_tag else ""
                        
                        # Extract content with multiple strategies
                        content = self._extract_content_advanced(soup)
                        
                        # Extract metadata
                        description_tag = soup.find('meta', attrs={'name': 'description'})
                        description = description_tag.get('content', '') if description_tag else ""
                        
                        keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
                        keywords = keywords_tag.get('content', '').split(',') if keywords_tag else []
                        
                        # Update session success rate
                        session.success_rate = (session.success_rate * (session.requests_count - 1) + 1.0) / session.requests_count
                        
                        return {
                            "url": url,
                            "title": title,
                            "content": self._clean_content(content),
                            "description": description,
                            "keywords": [k.strip() for k in keywords],
                            "scraped_at": datetime.now(),
                            "scraper": "advanced_http",
                            "session_id": session.session_id,
                            "content_length": len(content)
                        }
                    
                    elif response.status_code == 403 or response.status_code == 429:
                        # Mark session as potentially blocked
                        session.is_blocked = True
                        logger.warning(f"Session {session.session_id} potentially blocked for {url}")
                        
                    else:
                        logger.warning(f"HTTP {response.status_code} for {url}")
            
            except Exception as e:
                logger.warning(f"Scraping attempt {attempt + 1} failed for {url}: {e}")
                session.success_rate = (session.success_rate * (session.requests_count - 1) + 0.0) / session.requests_count
            
            # Wait before retry
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay * (attempt + 1))
        
        logger.error(f"All scraping attempts failed for {url}")
        return None
    
    def _extract_content_advanced(self, soup: BeautifulSoup) -> str:
        """
        Advanced content extraction with multiple strategies
        """
        content_strategies = [
            # Strategy 1: Semantic HTML5 elements
            lambda: self._extract_by_semantic_tags(soup),
            
            # Strategy 2: Common content classes
            lambda: self._extract_by_content_classes(soup),
            
            # Strategy 3: Text density analysis
            lambda: self._extract_by_text_density(soup),
            
            # Strategy 4: Fallback to body
            lambda: soup.body.get_text(strip=True, separator=' ') if soup.body else ""
        ]
        
        for strategy in content_strategies:
            try:
                content = strategy()
                if content and len(content) > 100:  # Minimum content length
                    return content
            except Exception as e:
                logger.debug(f"Content extraction strategy failed: {e}")
                continue
        
        return ""
    
    def _extract_by_semantic_tags(self, soup: BeautifulSoup) -> str:
        """Extract content using semantic HTML5 tags"""
        semantic_tags = ['article', 'main', 'section']
        
        for tag in semantic_tags:
            elements = soup.find_all(tag)
            for element in elements:
                text = element.get_text(strip=True, separator=' ')
                if len(text) > 200:  # Reasonable content length
                    return text
        
        return ""
    
    def _extract_by_content_classes(self, soup: BeautifulSoup) -> str:
        """Extract content using common content class names"""
        content_selectors = [
            '.article-content', '.post-content', '.entry-content',
            '.content', '.article-body', '.story-body',
            '.post-body', '.content-body', '.main-content'
        ]
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True, separator=' ')
                if len(text) > 200:
                    return text
        
        return ""
    
    def _extract_by_text_density(self, soup: BeautifulSoup) -> str:
        """Extract content by analyzing text density"""
        # Find paragraphs with substantial text
        paragraphs = soup.find_all('p')
        content_paragraphs = []
        
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 50:  # Substantial paragraph
                content_paragraphs.append(text)
        
        if len(content_paragraphs) >= 3:  # Multiple substantial paragraphs
            return ' '.join(content_paragraphs)
        
        return ""
    
    def _clean_content(self, content: str) -> str:
        """Clean and normalize content"""
        if not content:
            return ""
        
        # Remove excessive whitespace
        content = ' '.join(content.split())
        
        # Remove common noise
        noise_patterns = [
            'Share this article', 'Subscribe to our newsletter',
            'Follow us on', 'Like us on Facebook', 'Cookie policy',
            'Privacy policy', 'Terms of service', 'Advertisement'
        ]
        
        for pattern in noise_patterns:
            content = content.replace(pattern, '')
        
        # Limit content length
        max_length = self.config.get("max_content_length", 10000)
        if len(content) > max_length:
            content = content[:max_length] + "..."
        
        return content.strip()
    
    async def search_web(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """
        Search the web using available search APIs
        """
        if not self.enable_search:
            return []
        
        results = []
        
        # Try different search APIs in order of preference
        if self.search_apis.get("bing"):
            bing_results = await self._search_bing(query, max_results)
            results.extend(bing_results)
        
        if len(results) < max_results and self.search_apis.get("google"):
            google_results = await self._search_google(query, max_results - len(results))
            results.extend(google_results)
        
        if len(results) < max_results and self.search_apis.get("serpapi"):
            serp_results = await self._search_serpapi(query, max_results - len(results))
            results.extend(serp_results)
        
        # Fallback to DuckDuckGo (no API key required)
        if not results:
            ddg_results = await self._search_duckduckgo(query, max_results)
            results.extend(ddg_results)
        
        return results[:max_results]
    
    async def _search_bing(self, query: str, max_results: int) -> List[SearchResult]:
        """Search using Bing Web Search API"""
        if not self.search_apis.get("bing"):
            return []
        
        try:
            headers = {
                "Ocp-Apim-Subscription-Key": self.search_apis["bing"],
                "User-Agent": self.user_agents[0]
            }
            
            params = {
                "q": query,
                "count": max_results,
                "offset": 0,
                "mkt": "en-US",
                "safesearch": "Off",
                "textDecorations": False,
                "textFormat": "Raw"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.bing.microsoft.com/v7.0/search",
                    headers=headers,
                    params=params,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    for item in data.get("webPages", {}).get("value", []):
                        result = SearchResult(
                            title=item.get("name", ""),
                            url=item.get("url", ""),
                            snippet=item.get("snippet", ""),
                            source="bing",
                            relevance_score=0.8  # Bing generally has good relevance
                        )
                        results.append(result)
                    
                    return results
                
        except Exception as e:
            logger.error(f"Bing search error: {e}")
        
        return []
    
    async def _search_google(self, query: str, max_results: int) -> List[SearchResult]:
        """Search using Google Custom Search API"""
        if not self.search_apis.get("google"):
            return []
        
        try:
            params = {
                "key": self.search_apis["google"],
                "cx": self.config.get("google_cse_id", ""),  # Custom Search Engine ID
                "q": query,
                "num": min(max_results, 10),
                "safe": "off"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.googleapis.com/customsearch/v1",
                    params=params,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    for item in data.get("items", []):
                        result = SearchResult(
                            title=item.get("title", ""),
                            url=item.get("link", ""),
                            snippet=item.get("snippet", ""),
                            source="google",
                            relevance_score=0.9  # Google has excellent relevance
                        )
                        results.append(result)
                    
                    return results
                
        except Exception as e:
            logger.error(f"Google search error: {e}")
        
        return []
    
    async def _search_serpapi(self, query: str, max_results: int) -> List[SearchResult]:
        """Search using SerpAPI"""
        if not self.search_apis.get("serpapi"):
            return []
        
        try:
            params = {
                "api_key": self.search_apis["serpapi"],
                "engine": "google",
                "q": query,
                "num": max_results,
                "hl": "en",
                "gl": "us"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://serpapi.com/search",
                    params=params,
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    for item in data.get("organic_results", []):
                        result = SearchResult(
                            title=item.get("title", ""),
                            url=item.get("link", ""),
                            snippet=item.get("snippet", ""),
                            source="serpapi",
                            relevance_score=0.85
                        )
                        results.append(result)
                    
                    return results
                
        except Exception as e:
            logger.error(f"SerpAPI search error: {e}")
        
        return []
    
    async def _search_duckduckgo(self, query: str, max_results: int) -> List[SearchResult]:
        """Search using DuckDuckGo (no API key required)"""
        try:
            # DuckDuckGo instant answer API (limited but free)
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.duckduckgo.com/",
                    params=params,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    # DuckDuckGo API is limited, mainly for instant answers
                    if data.get("AbstractText"):
                        result = SearchResult(
                            title=data.get("Heading", query),
                            url=data.get("AbstractURL", ""),
                            snippet=data.get("AbstractText", ""),
                            source="duckduckgo",
                            relevance_score=0.6
                        )
                        results.append(result)
                    
                    # Add related topics
                    for topic in data.get("RelatedTopics", [])[:max_results-1]:
                        if isinstance(topic, dict) and topic.get("Text"):
                            result = SearchResult(
                                title=topic.get("Text", "")[:100],
                                url=topic.get("FirstURL", ""),
                                snippet=topic.get("Text", ""),
                                source="duckduckgo",
                                relevance_score=0.5
                            )
                            results.append(result)
                    
                    return results
                
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
        
        return []
    
    async def cleanup(self):
        """Cleanup scraper resources"""
        if hasattr(self, 'scrapling_adapter') and self.scrapling_adapter:
            try:
                await self.scrapling_adapter.close()
            except Exception as e:
                logger.warning(f"Error closing Scrapling adapter: {e}")
        
        logger.info("AdvancedScraper cleaned up")