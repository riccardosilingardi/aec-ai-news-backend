"""
Curator Agent - Content Quality Analysis Implementation
Handles AI-powered content quality scoring, categorization, and trend detection
"""

import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import Counter
import json
import hashlib

# Import base classes from the architecture
import sys
import os
import importlib.util

# Try multiple paths for architecture import
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from multi_agent_architecture import BaseAgent, AgentTask, ContentItem, AgentStatus
except ImportError:
    # Load from project root
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
class QualityMetrics:
    """Content quality assessment metrics"""
    readability_score: float = 0.0
    authority_score: float = 0.0  
    freshness_score: float = 0.0
    relevance_score: float = 0.0
    engagement_potential: float = 0.0
    overall_quality: float = 0.0

@dataclass 
class AIRelevanceMetrics:
    """AI relevance assessment metrics"""
    ai_keyword_density: float = 0.0
    aec_industry_relevance: float = 0.0
    technical_depth: float = 0.0
    business_impact: str = "low"  # low, medium, high
    innovation_factor: float = 0.0
    overall_relevance: float = 0.0

@dataclass
class ContentAnalysis:
    """Complete content analysis result"""
    content_item: ContentItem
    quality_metrics: QualityMetrics
    ai_relevance: AIRelevanceMetrics
    category: str
    tags: List[str]
    sentiment: str
    summary: str
    analysis_timestamp: datetime

class CuratorAgent(BaseAgent):
    """
    Curator Agent Implementation
    
    RESPONSIBILITIES:
    - AI-powered content quality scoring
    - AEC industry relevance analysis
    - Content categorization and tagging
    - Duplicate detection and merging
    - Trend identification
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        
        # Configuration
        self.quality_threshold = config.get("quality_threshold", 0.6)
        self.relevance_threshold = config.get("relevance_threshold", 0.4)
        self.content_categories = config.get("content_categories", self._default_categories())
        self.trend_analysis_days = config.get("trend_analysis_days", 7)
        
        # Analysis results storage
        self.analyzed_content: List[ContentAnalysis] = []
        self.content_trends: Dict[str, Any] = {}
        self.category_stats: Dict[str, int] = {}
        
        # AI/AEC keyword databases
        self.ai_keywords = self._initialize_ai_keywords()
        self.aec_keywords = self._initialize_aec_keywords()
        self.authority_indicators = self._initialize_authority_indicators()
        
        logger.info(f"CuratorAgent {agent_id} initialized with {len(self.content_categories)} categories")
    
    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Process content curation tasks
        
        Task Types:
        - "analyze_content": Score and categorize content
        - "detect_trends": Identify trending topics
        - "filter_quality": Remove low-quality content
        - "get_curated_content": Get curated content for newsletter
        """
        try:
            self.status = AgentStatus.WORKING
            task_type = task.data.get("type")
            
            logger.info(f"CuratorAgent processing task: {task_type}")
            
            if task_type == "analyze_content":
                return await self._analyze_content_batch(task.data.get("content_items", []))
            elif task_type == "detect_trends":
                return await self._detect_trends(task.data.get("timeframe", "7d"))
            elif task_type == "filter_quality":
                return await self._filter_by_quality(task.data.get("content_items", []))
            elif task_type == "get_curated_content":
                return await self._get_curated_content(task.data)
            elif task_type == "categorize_content":
                return await self._categorize_content(task.data.get("content_items", []))
            else:
                return {"status": "error", "message": f"Unknown task type: {task_type}"}
                
        except Exception as e:
            logger.error(f"CuratorAgent task processing error: {e}")
            self.status = AgentStatus.ERROR
            return {"status": "error", "message": str(e)}
        finally:
            if self.status != AgentStatus.ERROR:
                self.status = AgentStatus.COMPLETED
    
    async def _analyze_content_batch(self, content_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze a batch of content items for quality and relevance
        """
        try:
            results = {
                "status": "success",
                "total_analyzed": 0,
                "high_quality_count": 0,
                "medium_quality_count": 0,
                "low_quality_count": 0,
                "categories_found": {},
                "analysis_results": []
            }
            
            for item_data in content_items:
                try:
                    # Convert to ContentItem if needed
                    if isinstance(item_data, dict):
                        content_item = ContentItem(
                            url=item_data.get("url", ""),
                            title=item_data.get("title", ""),
                            content=item_data.get("content", ""),
                            source=item_data.get("source", ""),
                            discovered_at=datetime.fromisoformat(item_data.get("discovered_at", datetime.now().isoformat()))
                        )
                    else:
                        content_item = item_data
                    
                    # Perform analysis
                    analysis = await self._analyze_single_content(content_item)
                    
                    if analysis:
                        self.analyzed_content.append(analysis)
                        results["analysis_results"].append(asdict(analysis))
                        results["total_analyzed"] += 1
                        
                        # Categorize by quality
                        overall_quality = analysis.quality_metrics.overall_quality
                        if overall_quality >= 0.7:
                            results["high_quality_count"] += 1
                        elif overall_quality >= 0.4:
                            results["medium_quality_count"] += 1
                        else:
                            results["low_quality_count"] += 1
                        
                        # Track categories
                        category = analysis.category
                        results["categories_found"][category] = results["categories_found"].get(category, 0) + 1
                        
                except Exception as e:
                    logger.warning(f"Error analyzing content item: {e}")
                    continue
            
            # Update category statistics
            for category, count in results["categories_found"].items():
                self.category_stats[category] = self.category_stats.get(category, 0) + count
            
            logger.info(f"Analyzed {results['total_analyzed']} content items")
            return results
            
        except Exception as e:
            logger.error(f"Error in content batch analysis: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _analyze_single_content(self, content_item: ContentItem) -> Optional[ContentAnalysis]:
        """
        Perform comprehensive analysis of a single content item
        """
        try:
            # Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(content_item)
            
            # Calculate AI relevance
            ai_relevance = self._calculate_ai_relevance(content_item)
            
            # Determine category
            category = self._categorize_single_item(content_item)
            
            # Generate tags
            tags = self._generate_tags(content_item)
            
            # Analyze sentiment
            sentiment = self._analyze_sentiment(content_item)
            
            # Generate summary
            summary = self._generate_summary(content_item)
            
            # Create analysis result
            analysis = ContentAnalysis(
                content_item=content_item,
                quality_metrics=quality_metrics,
                ai_relevance=ai_relevance,
                category=category,
                tags=tags,
                sentiment=sentiment,
                summary=summary,
                analysis_timestamp=datetime.now()
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing single content: {e}")
            return None
    
    def _calculate_quality_metrics(self, content_item: ContentItem) -> QualityMetrics:
        """
        Calculate content quality metrics
        """
        content = content_item.content + " " + content_item.title
        
        # Readability score (simplified)
        readability = self._calculate_readability(content)
        
        # Authority score based on source and content quality indicators
        authority = self._calculate_authority_score(content_item)
        
        # Freshness score based on publication date
        freshness = self._calculate_freshness_score(content_item)
        
        # Relevance score (separate from AI relevance)
        relevance = self._calculate_content_relevance(content)
        
        # Engagement potential based on content characteristics
        engagement = self._calculate_engagement_potential(content)
        
        # Overall quality (weighted average)
        overall = (
            readability * 0.2 +
            authority * 0.25 +
            freshness * 0.15 +
            relevance * 0.25 +
            engagement * 0.15
        )
        
        return QualityMetrics(
            readability_score=readability,
            authority_score=authority,
            freshness_score=freshness,
            relevance_score=relevance,
            engagement_potential=engagement,
            overall_quality=overall
        )
    
    def _calculate_ai_relevance(self, content_item: ContentItem) -> AIRelevanceMetrics:
        """
        Calculate AI relevance metrics
        """
        content = (content_item.content + " " + content_item.title).lower()
        
        # AI keyword density
        ai_keywords_found = sum(content.count(keyword) for keyword in self.ai_keywords.keys())
        ai_density = min(ai_keywords_found / max(len(content.split()), 1) * 100, 1.0)
        
        # AEC industry relevance
        aec_keywords_found = sum(content.count(keyword) for keyword in self.aec_keywords.keys())
        aec_relevance = min(aec_keywords_found / max(len(content.split()), 1) * 100, 1.0)
        
        # Technical depth (based on technical terms and complexity)
        technical_depth = self._calculate_technical_depth(content)
        
        # Innovation factor (mentions of new/emerging technologies)
        innovation = self._calculate_innovation_factor(content)
        
        # Business impact assessment
        business_impact = self._assess_business_impact(content, ai_density, aec_relevance)
        
        # Overall relevance
        overall_relevance = (
            ai_density * 0.3 +
            aec_relevance * 0.3 +
            technical_depth * 0.2 +
            innovation * 0.2
        )
        
        return AIRelevanceMetrics(
            ai_keyword_density=ai_density,
            aec_industry_relevance=aec_relevance,
            technical_depth=technical_depth,
            business_impact=business_impact,
            innovation_factor=innovation,
            overall_relevance=overall_relevance
        )
    
    def _calculate_readability(self, content: str) -> float:
        """
        Calculate readability score (simplified Flesch Reading Ease)
        """
        if not content:
            return 0.0
        
        sentences = len(re.split(r'[.!?]+', content))
        words = len(content.split())
        syllables = sum(self._count_syllables(word) for word in content.split())
        
        if sentences == 0 or words == 0:
            return 0.0
        
        # Simplified Flesch formula
        avg_sentence_length = words / sentences
        avg_syllables_per_word = syllables / words
        
        score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        
        # Normalize to 0-1 range
        return max(0.0, min(1.0, score / 100.0))
    
    def _count_syllables(self, word: str) -> int:
        """
        Count syllables in a word (simplified)
        """
        word = word.lower()
        vowels = 'aeiouy'
        syllables = 0
        prev_was_vowel = False
        
        for char in word:
            if char in vowels:
                if not prev_was_vowel:
                    syllables += 1
                prev_was_vowel = True
            else:
                prev_was_vowel = False
        
        # Handle silent 'e'
        if word.endswith('e') and syllables > 1:
            syllables -= 1
        
        return max(1, syllables)
    
    def _calculate_authority_score(self, content_item: ContentItem) -> float:
        """
        Calculate authority score based on source and content indicators
        """
        score = 0.0
        content = content_item.content.lower()
        source = content_item.source.lower()
        
        # Source authority indicators
        authority_domains = [
            'archdaily.com', 'dezeen.com', 'engineering.com', 'autodesk.com',
            'bentley.com', 'trimble.com', 'constructiondive.com', 'aecmag.com'
        ]
        
        for domain in authority_domains:
            if domain in source:
                score += 0.3
                break
        
        # Content authority indicators
        for indicator, weight in self.authority_indicators.items():
            if indicator in content:
                score += weight
        
        return min(1.0, score)
    
    def _calculate_freshness_score(self, content_item: ContentItem) -> float:
        """
        Calculate freshness score based on publication date
        """
        if not hasattr(content_item, 'discovered_at') or not content_item.discovered_at:
            return 0.5  # Neutral score if no date
        
        now = datetime.now()
        age_hours = (now - content_item.discovered_at).total_seconds() / 3600
        
        # Fresher content gets higher scores
        if age_hours <= 24:
            return 1.0
        elif age_hours <= 72:
            return 0.8
        elif age_hours <= 168:  # 1 week
            return 0.6
        elif age_hours <= 720:  # 1 month
            return 0.4
        else:
            return 0.2
    
    def _calculate_content_relevance(self, content: str) -> float:
        """
        Calculate general content relevance for AEC industry
        """
        content_lower = content.lower()
        relevance_score = 0.0
        
        # Industry-specific terms
        industry_terms = {
            'construction': 0.1, 'architecture': 0.1, 'engineering': 0.1,
            'building': 0.05, 'design': 0.05, 'infrastructure': 0.08,
            'project management': 0.08, 'sustainability': 0.06
        }
        
        for term, weight in industry_terms.items():
            if term in content_lower:
                relevance_score += weight
        
        return min(1.0, relevance_score)
    
    def _calculate_engagement_potential(self, content: str) -> float:
        """
        Calculate engagement potential based on content characteristics
        """
        content_lower = content.lower()
        engagement_score = 0.0
        
        # Engagement indicators
        engagement_words = [
            'breakthrough', 'innovative', 'revolutionary', 'game-changing',
            'efficiency', 'productivity', 'cost-saving', 'future', 'trend'
        ]
        
        for word in engagement_words:
            if word in content_lower:
                engagement_score += 0.1
        
        # Content length factor (not too short, not too long)
        word_count = len(content.split())
        if 200 <= word_count <= 1000:
            engagement_score += 0.2
        elif 100 <= word_count < 200 or 1000 < word_count <= 2000:
            engagement_score += 0.1
        
        return min(1.0, engagement_score)
    
    def _calculate_technical_depth(self, content: str) -> float:
        """
        Calculate technical depth score
        """
        technical_terms = [
            'algorithm', 'machine learning', 'neural network', 'api', 'cloud',
            'automation', 'sensor', 'iot', 'data analytics', 'modeling'
        ]
        
        found_terms = sum(1 for term in technical_terms if term in content)
        return min(1.0, found_terms / len(technical_terms))
    
    def _calculate_innovation_factor(self, content: str) -> float:
        """
        Calculate innovation factor score
        """
        innovation_terms = [
            'breakthrough', 'cutting-edge', 'next-generation', 'revolutionary',
            'emerging', 'novel', 'prototype', 'pilot project', 'beta'
        ]
        
        found_terms = sum(1 for term in innovation_terms if term in content)
        return min(1.0, found_terms / len(innovation_terms))
    
    def _assess_business_impact(self, content: str, ai_density: float, aec_relevance: float) -> str:
        """
        Assess business impact level
        """
        impact_keywords = {
            'high': ['cost reduction', 'efficiency gain', 'productivity', 'competitive advantage', 'roi'],
            'medium': ['improvement', 'optimization', 'enhanced', 'better', 'upgrade'],
            'low': ['concept', 'research', 'study', 'analysis', 'review']
        }
        
        high_score = sum(1 for keyword in impact_keywords['high'] if keyword in content)
        medium_score = sum(1 for keyword in impact_keywords['medium'] if keyword in content)
        
        # Combine with AI and AEC relevance
        combined_score = (ai_density + aec_relevance) / 2
        
        if high_score >= 2 or combined_score >= 0.7:
            return "high"
        elif medium_score >= 2 or combined_score >= 0.4:
            return "medium"
        else:
            return "low"
    
    def _categorize_single_item(self, content_item: ContentItem) -> str:
        """
        Categorize a single content item
        """
        content = (content_item.content + " " + content_item.title).lower()
        
        category_keywords = {
            "BIM & Digital Twins": ['bim', 'digital twin', 'revit', 'modeling', '3d', 'cad'],
            "Construction Automation": ['automation', 'robotics', 'machinery', 'equipment', 'automated'],
            "AI Design Tools": ['design ai', 'generative design', 'parametric', 'ai design', 'cad ai'],
            "Smart Buildings & IoT": ['iot', 'smart building', 'sensors', 'connectivity', 'intelligent'],
            "Project Management AI": ['project management', 'scheduling', 'planning', 'coordination'],
            "Sustainability & Green Tech": ['sustainability', 'green', 'energy', 'environment', 'carbon'],
            "Robotics in Construction": ['robot', 'autonomous', 'drone', 'automated construction'],
            "Government & Policy AI": ['policy', 'government', 'regulation', 'compliance', 'legislation'],
            "Financial Tech in AEC": ['fintech', 'financial', 'investment', 'funding', 'economics'],
            "Industry Productivity": ['productivity', 'efficiency', 'workflow', 'optimization']
        }
        
        best_category = "General AI in AEC"
        best_score = 0
        
        for category, keywords in category_keywords.items():
            score = sum(content.count(keyword) for keyword in keywords)
            if score > best_score:
                best_score = score
                best_category = category
        
        return best_category
    
    def _generate_tags(self, content_item: ContentItem) -> List[str]:
        """
        Generate tags for content item
        """
        content = (content_item.content + " " + content_item.title).lower()
        tags = []
        
        # Technology tags
        tech_tags = {
            'artificial intelligence': 'ai',
            'machine learning': 'ml',
            'deep learning': 'deep-learning',
            'computer vision': 'computer-vision',
            'robotics': 'robotics',
            'automation': 'automation',
            'iot': 'iot',
            'blockchain': 'blockchain'
        }
        
        for term, tag in tech_tags.items():
            if term in content:
                tags.append(tag)
        
        # Industry tags
        industry_tags = {
            'construction': 'construction',
            'architecture': 'architecture', 
            'engineering': 'engineering',
            'infrastructure': 'infrastructure',
            'real estate': 'real-estate'
        }
        
        for term, tag in industry_tags.items():
            if term in content:
                tags.append(tag)
        
        return list(set(tags))  # Remove duplicates
    
    def _analyze_sentiment(self, content_item: ContentItem) -> str:
        """
        Analyze sentiment of content (simplified)
        """
        content = content_item.content.lower()
        
        positive_words = [
            'innovation', 'breakthrough', 'success', 'efficient', 'improved',
            'revolutionary', 'advancement', 'opportunity', 'growth', 'benefit'
        ]
        
        negative_words = [
            'challenge', 'problem', 'difficulty', 'concern', 'risk',
            'limitation', 'failure', 'decline', 'issue', 'barrier'
        ]
        
        positive_count = sum(1 for word in positive_words if word in content)
        negative_count = sum(1 for word in negative_words if word in content)
        
        if positive_count > negative_count + 1:
            return "positive"
        elif negative_count > positive_count + 1:
            return "negative"
        else:
            return "neutral"
    
    def _generate_summary(self, content_item: ContentItem) -> str:
        """
        Generate a summary of the content (simplified)
        """
        content = content_item.content
        title = content_item.title
        
        # For now, use first sentence(s) as summary
        sentences = re.split(r'[.!?]+', content)
        
        if len(sentences) >= 2:
            summary = sentences[0] + "." + sentences[1] + "."
        elif len(sentences) == 1:
            summary = sentences[0]
        else:
            summary = title
        
        # Limit length
        return summary[:300] + "..." if len(summary) > 300 else summary
    
    async def _detect_trends(self, timeframe: str) -> Dict[str, Any]:
        """
        Detect trending topics and patterns
        """
        try:
            # Parse timeframe
            if timeframe.endswith('d'):
                days = int(timeframe[:-1])
            else:
                days = 7  # Default
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Filter recent content
            recent_content = [
                analysis for analysis in self.analyzed_content
                if analysis.analysis_timestamp >= cutoff_date
            ]
            
            if not recent_content:
                return {
                    "status": "success",
                    "message": "No recent content for trend analysis",
                    "trends": {}
                }
            
            # Analyze trends
            trends = {
                "category_trends": self._analyze_category_trends(recent_content),
                "keyword_trends": self._analyze_keyword_trends(recent_content),
                "sentiment_trends": self._analyze_sentiment_trends(recent_content),
                "quality_trends": self._analyze_quality_trends(recent_content),
                "timeframe": f"{days} days",
                "total_content_analyzed": len(recent_content)
            }
            
            self.content_trends = trends
            
            return {
                "status": "success",
                "trends": trends
            }
            
        except Exception as e:
            logger.error(f"Error detecting trends: {e}")
            return {"status": "error", "message": str(e)}
    
    def _analyze_category_trends(self, content_analyses: List[ContentAnalysis]) -> Dict[str, Any]:
        """
        Analyze category trends
        """
        categories = [analysis.category for analysis in content_analyses]
        category_counts = Counter(categories)
        
        total = len(categories)
        category_percentages = {
            category: (count / total) * 100
            for category, count in category_counts.items()
        }
        
        # Find trending categories (above average)
        avg_percentage = 100 / len(self.content_categories)
        trending = {
            category: percentage
            for category, percentage in category_percentages.items()
            if percentage > avg_percentage * 1.5  # 50% above average
        }
        
        return {
            "category_distribution": dict(category_counts),
            "category_percentages": category_percentages,
            "trending_categories": trending,
            "total_categories": len(category_counts)
        }
    
    def _analyze_keyword_trends(self, content_analyses: List[ContentAnalysis]) -> Dict[str, Any]:
        """
        Analyze keyword trends
        """
        all_tags = []
        for analysis in content_analyses:
            all_tags.extend(analysis.tags)
        
        tag_counts = Counter(all_tags)
        
        return {
            "most_common_tags": dict(tag_counts.most_common(10)),
            "total_unique_tags": len(tag_counts),
            "tag_frequency": dict(tag_counts)
        }
    
    def _analyze_sentiment_trends(self, content_analyses: List[ContentAnalysis]) -> Dict[str, Any]:
        """
        Analyze sentiment trends
        """
        sentiments = [analysis.sentiment for analysis in content_analyses]
        sentiment_counts = Counter(sentiments)
        
        total = len(sentiments)
        sentiment_percentages = {
            sentiment: (count / total) * 100
            for sentiment, count in sentiment_counts.items()
        }
        
        return {
            "sentiment_distribution": dict(sentiment_counts),
            "sentiment_percentages": sentiment_percentages,
            "overall_sentiment": max(sentiment_counts, key=sentiment_counts.get)
        }
    
    def _analyze_quality_trends(self, content_analyses: List[ContentAnalysis]) -> Dict[str, Any]:
        """
        Analyze quality trends
        """
        quality_scores = [analysis.quality_metrics.overall_quality for analysis in content_analyses]
        
        if not quality_scores:
            return {"message": "No quality scores available"}
        
        avg_quality = sum(quality_scores) / len(quality_scores)
        high_quality_count = sum(1 for score in quality_scores if score >= 0.7)
        medium_quality_count = sum(1 for score in quality_scores if 0.4 <= score < 0.7)
        low_quality_count = sum(1 for score in quality_scores if score < 0.4)
        
        return {
            "average_quality": avg_quality,
            "quality_distribution": {
                "high": high_quality_count,
                "medium": medium_quality_count,
                "low": low_quality_count
            },
            "quality_percentages": {
                "high": (high_quality_count / len(quality_scores)) * 100,
                "medium": (medium_quality_count / len(quality_scores)) * 100,
                "low": (low_quality_count / len(quality_scores)) * 100
            }
        }
    
    async def _filter_by_quality(self, content_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Filter content by quality thresholds
        """
        try:
            # First analyze the content
            analysis_result = await self._analyze_content_batch(content_items)
            
            if analysis_result.get("status") != "success":
                return analysis_result
            
            # Filter by quality and relevance thresholds
            high_quality = []
            medium_quality = []
            low_quality = []
            
            for analysis_data in analysis_result["analysis_results"]:
                quality_score = analysis_data["quality_metrics"]["overall_quality"]
                relevance_score = analysis_data["ai_relevance"]["overall_relevance"]
                
                if (quality_score >= self.quality_threshold and 
                    relevance_score >= self.relevance_threshold):
                    high_quality.append(analysis_data)
                elif quality_score >= 0.4 or relevance_score >= 0.3:
                    medium_quality.append(analysis_data)
                else:
                    low_quality.append(analysis_data)
            
            return {
                "status": "success",
                "filtering_criteria": {
                    "quality_threshold": self.quality_threshold,
                    "relevance_threshold": self.relevance_threshold
                },
                "results": {
                    "high_quality": high_quality,
                    "medium_quality": medium_quality,
                    "low_quality": low_quality
                },
                "counts": {
                    "high_quality": len(high_quality),
                    "medium_quality": len(medium_quality),
                    "low_quality": len(low_quality),
                    "total_processed": len(content_items)
                }
            }
            
        except Exception as e:
            logger.error(f"Error filtering content by quality: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _get_curated_content(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get curated content for newsletter or other purposes
        """
        try:
            max_articles = request_data.get("max_articles", 20)
            category_filter = request_data.get("category", None)
            quality_min = request_data.get("quality_min", 0.6)
            
            # Filter analyzed content
            filtered_content = []
            
            for analysis in self.analyzed_content:
                # Apply filters
                if category_filter and analysis.category != category_filter:
                    continue
                
                if analysis.quality_metrics.overall_quality < quality_min:
                    continue
                
                filtered_content.append(analysis)
            
            # Sort by quality and relevance
            filtered_content.sort(
                key=lambda x: (x.quality_metrics.overall_quality + x.ai_relevance.overall_relevance) / 2,
                reverse=True
            )
            
            # Limit results
            curated_content = filtered_content[:max_articles]
            
            # Group by category
            by_category = {}
            for analysis in curated_content:
                category = analysis.category
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(asdict(analysis))
            
            return {
                "status": "success",
                "curated_content": [asdict(analysis) for analysis in curated_content],
                "by_category": by_category,
                "total_curated": len(curated_content),
                "total_available": len(filtered_content),
                "filters_applied": {
                    "max_articles": max_articles,
                    "category_filter": category_filter,
                    "quality_min": quality_min
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting curated content: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _categorize_content(self, content_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Categorize content items
        """
        try:
            categorized = {}
            
            for item_data in content_items:
                if isinstance(item_data, dict):
                    content_item = ContentItem(
                        url=item_data.get("url", ""),
                        title=item_data.get("title", ""),
                        content=item_data.get("content", ""),
                        source=item_data.get("source", ""),
                        discovered_at=datetime.now()
                    )
                else:
                    content_item = item_data
                
                category = self._categorize_single_item(content_item)
                
                if category not in categorized:
                    categorized[category] = []
                
                categorized[category].append(asdict(content_item))
            
            return {
                "status": "success",
                "categorized_content": categorized,
                "category_counts": {cat: len(items) for cat, items in categorized.items()},
                "total_items": len(content_items)
            }
            
        except Exception as e:
            logger.error(f"Error categorizing content: {e}")
            return {"status": "error", "message": str(e)}
    
    def _default_categories(self) -> List[str]:
        """
        Default content categories for AEC AI news
        """
        return [
            "BIM & Digital Twins",
            "Construction Automation", 
            "AI Design Tools",
            "Parametric & Generative Design",
            "Smart Buildings & IoT",
            "Project Management AI",
            "Sustainability & Green Tech",
            "Robotics in Construction",
            "Government & Policy AI",
            "Financial Tech in AEC",
            "Industry Productivity"
        ]
    
    def _initialize_ai_keywords(self) -> Dict[str, float]:
        """
        Initialize AI keywords with weights
        """
        return {
            'artificial intelligence': 3.0,
            'machine learning': 2.5,
            'ai': 2.0,
            'neural network': 2.5,
            'deep learning': 2.5,
            'algorithm': 1.5,
            'automation': 2.0,
            'digital twin': 3.0,
            'predictive': 2.0,
            'computer vision': 2.5,
            'robotics': 2.0,
            'smart': 1.5,
            'llm': 2.5,
            'chatgpt': 2.0,
            'generative': 2.5,
            'gpt': 2.0
        }
    
    def _initialize_aec_keywords(self) -> Dict[str, float]:
        """
        Initialize AEC industry keywords with weights
        """
        return {
            'bim': 3.0,
            'construction': 2.5,
            'architecture': 2.0,
            'engineering': 2.0,
            'building': 2.0,
            'design': 1.5,
            'parametric': 2.5,
            'generative': 2.5,
            'revit': 2.0,
            'autocad': 2.0,
            'sustainability': 2.0,
            'project management': 2.0,
            'real estate': 1.5,
            'infrastructure': 2.0,
            'facility': 1.5
        }
    
    def _initialize_authority_indicators(self) -> Dict[str, float]:
        """
        Initialize content authority indicators
        """
        return {
            'research': 0.1,
            'study': 0.1,
            'whitepaper': 0.2,
            'case study': 0.15,
            'published': 0.1,
            'peer reviewed': 0.3,
            'industry report': 0.2,
            'analysis': 0.1,
            'expert': 0.15,
            'professor': 0.2,
            'phd': 0.15
        }
    
    async def health_check(self) -> bool:
        """
        Check curator health
        """
        try:
            # Basic functionality test
            test_content = ContentItem(
                url="test://test",
                title="Test AI in Construction",
                content="This is a test article about artificial intelligence in construction automation.",
                source="test",
                discovered_at=datetime.now()
            )
            
            analysis = await self._analyze_single_content(test_content)
            return analysis is not None
            
        except Exception as e:
            logger.error(f"Curator health check error: {e}")
            return False
    
    async def cleanup(self):
        """
        Cleanup curator resources
        """
        # Clear analysis cache if needed for memory management
        if len(self.analyzed_content) > 1000:
            # Keep only recent analyses
            cutoff_date = datetime.now() - timedelta(days=30)
            self.analyzed_content = [
                analysis for analysis in self.analyzed_content
                if analysis.analysis_timestamp >= cutoff_date
            ]
        
        logger.info(f"CuratorAgent {self.agent_id} cleaned up")