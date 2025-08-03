"""
MCP Prompts Implementation
Provides AI assistance prompts for content generation and analysis
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class MCPPrompts:
    """MCP Prompts for AI-assisted content operations"""
    
    def __init__(self, multi_agent_system):
        self.multi_agent_system = multi_agent_system
    
    async def get_content_analysis_prompt(self, content_id: int = None, content_text: str = None) -> Dict[str, Any]:
        """Prompt: content://analyze"""
        try:
            if content_id:
                db = self.multi_agent_system.database
                content = await db.get_content_by_id(content_id)
                if not content:
                    return {"error": f"Content ID {content_id} not found"}
                content_text = content.get('content', '')
                title = content.get('title', '')
            else:
                title = "Provided Content"
            
            prompt = f"""Analyze this AEC (Architecture, Engineering, Construction) industry content for quality and relevance:

TITLE: {title}

CONTENT:
{content_text}

Please provide:
1. QUALITY SCORE (0.0-1.0): Overall content quality
2. RELEVANCE SCORE (0.0-1.0): Relevance to AEC industry
3. KEY TOPICS: Main topics covered (max 5)
4. SUMMARY: 2-sentence summary
5. RECOMMENDATION: Include/Exclude with reasoning

Focus on:
- Technical accuracy and depth
- Industry relevance (architecture, engineering, construction)
- Practical value for AEC professionals
- Innovation and emerging trends
- Regulatory and compliance aspects
"""
            
            return {
                "prompt": prompt,
                "content_id": content_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate content analysis prompt: {e}")
            return {"error": str(e)}
    
    async def get_newsletter_generation_prompt(self, selected_content: List[Dict] = None) -> Dict[str, Any]:
        """Prompt: newsletter://generate"""
        try:
            if not selected_content:
                db = self.multi_agent_system.database
                selected_content = await db.get_content_by_status("selected", limit=20)
            
            content_summaries = []
            for i, content in enumerate(selected_content[:10], 1):
                summary = f"{i}. {content.get('title', 'No Title')}\n   Source: {content.get('source_url', 'N/A')}\n   Quality: {content.get('quality_score', 'N/A')}\n   Summary: {content.get('summary', 'No summary available')}\n"
                content_summaries.append(summary)
            
            prompt = f"""Generate an AEC industry newsletter from the following curated content:

SELECTED ARTICLES ({len(selected_content)} total):
{chr(10).join(content_summaries)}

Please create:
1. SUBJECT LINE: Engaging email subject (max 60 characters)
2. NEWSLETTER STRUCTURE:
   - Opening paragraph (industry context)
   - Main articles section (group by themes)
   - Quick updates section (brief mentions)
   - Closing with actionable insights

3. CONTENT GUIDELINES:
   - Professional tone for AEC executives and professionals
   - Focus on business impact and practical applications
   - Highlight innovation, trends, and regulatory changes
   - Include brief analysis connecting articles to broader industry trends

4. FORMAT: Clean HTML structure suitable for email clients

Target audience: AEC industry professionals, executives, and decision-makers.
Newsletter length: 800-1200 words maximum.
"""
            
            return {
                "prompt": prompt,
                "content_count": len(selected_content),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate newsletter prompt: {e}")
            return {"error": str(e)}
    
    async def get_content_curation_prompt(self, articles: List[Dict]) -> Dict[str, Any]:
        """Prompt: curation://select"""
        try:
            article_list = []
            for i, article in enumerate(articles[:20], 1):
                article_info = f"{i}. {article.get('title', 'No Title')}\n   Quality: {article.get('quality_score', 'N/A')}\n   Relevance: {article.get('relevance_score', 'N/A')}\n   Source: {article.get('source_name', 'Unknown')}\n   Summary: {article.get('summary', 'No summary')[:100]}...\n"
                article_list.append(article_info)
            
            prompt = f"""Curate the best articles for this week's AEC industry newsletter:

ANALYZED ARTICLES ({len(articles)} total):
{chr(10).join(article_list)}

Selection criteria:
1. HIGH IMPACT: Articles that will significantly interest AEC professionals
2. DIVERSITY: Cover different aspects (architecture, engineering, construction, technology)
3. TIMELINESS: Recent developments and emerging trends
4. ACTIONABILITY: Content that provides practical value

Please provide:
1. SELECTED ARTICLES: List of article numbers to include (max 8-10)
2. NEWSLETTER THEMES: 2-3 main themes to organize the content
3. REASONING: Brief explanation for selections and rejections
4. PRIORITY ORDER: Rank selected articles by importance

Goal: Create a valuable, engaging newsletter that AEC professionals will want to read and share.
"""
            
            return {
                "prompt": prompt,
                "article_count": len(articles),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate curation prompt: {e}")
            return {"error": str(e)}
    
    async def get_source_evaluation_prompt(self, source_url: str, recent_articles: List[Dict] = None) -> Dict[str, Any]:
        """Prompt: sources://evaluate"""
        try:
            if recent_articles:
                article_quality = [a.get('quality_score', 0) for a in recent_articles if a.get('quality_score')]
                avg_quality = sum(article_quality) / len(article_quality) if article_quality else 0
                article_count = len(recent_articles)
            else:
                avg_quality = 0
                article_count = 0
            
            prompt = f"""Evaluate this AEC industry content source for inclusion in our monitoring system:

SOURCE URL: {source_url}
RECENT PERFORMANCE:
- Articles processed: {article_count}
- Average quality score: {avg_quality:.2f}

Please assess:
1. CONTENT QUALITY: Depth, accuracy, and professional standards
2. AEC RELEVANCE: Focus on architecture, engineering, construction topics
3. UPDATE FREQUENCY: How often new content is published
4. AUTHORITY: Credibility and expertise of the source
5. UNIQUE VALUE: What this source offers that others don't

Provide:
1. OVERALL SCORE (0.0-1.0): Recommendation for continued monitoring
2. STRENGTHS: Key advantages of this source
3. WEAKNESSES: Areas of concern or limitation
4. RECOMMENDATION: Keep/Remove/Monitor with reasoning
5. OPTIMIZATION: Suggestions for better content extraction

Focus on sources that consistently deliver high-value content for AEC professionals.
"""
            
            return {
                "prompt": prompt,
                "source_url": source_url,
                "performance_data": {
                    "article_count": article_count,
                    "avg_quality": avg_quality
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate source evaluation prompt: {e}")
            return {"error": str(e)}
    
    async def get_trend_analysis_prompt(self, time_period: str = "week") -> Dict[str, Any]:
        """Prompt: trends://analyze"""
        try:
            db = self.multi_agent_system.database
            
            # Get recent content for trend analysis
            if time_period == "week":
                days_back = 7
            elif time_period == "month":
                days_back = 30
            else:
                days_back = 7
            
            # This would query content from the specified time period
            # For now, create a generic prompt
            
            prompt = f"""Analyze AEC industry trends from content collected over the past {time_period}:

Please identify:
1. EMERGING TRENDS: New developments gaining momentum
2. HOT TOPICS: Most frequently discussed subjects
3. TECHNOLOGY SHIFTS: Changes in tools, methods, or approaches
4. REGULATORY UPDATES: New compliance requirements or policy changes
5. MARKET MOVEMENTS: Economic indicators and business impacts

Provide:
1. TREND SUMMARY: Top 5 trends with brief descriptions
2. IMPACT ASSESSMENT: How these trends affect AEC professionals
3. FUTURE OUTLOOK: Predictions for continued development
4. ACTIONABLE INSIGHTS: What industry professionals should know/do

Format for executive briefing - clear, concise, and business-focused.
Target audience: AEC industry leaders and decision-makers.
"""
            
            return {
                "prompt": prompt,
                "time_period": time_period,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate trend analysis prompt: {e}")
            return {"error": str(e)}