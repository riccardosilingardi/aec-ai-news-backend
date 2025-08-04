"""
Writer Agent - Newsletter Generation Implementation
Handles Superhuman-style newsletter creation, content organization, and formatting
"""

import logging
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import json

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
class NewsletterMetrics:
    """Newsletter performance metrics"""
    total_articles: int = 0
    high_impact_articles: int = 0
    categories_covered: int = 0
    estimated_read_time: int = 0  # minutes
    content_freshness_avg: float = 0.0
    quality_score_avg: float = 0.0

@dataclass
class NewsletterSection:
    """Newsletter section structure"""
    title: str
    content: str
    articles: List[Dict[str, Any]]
    priority: int = 1

@dataclass
class Newsletter:
    """Complete newsletter structure"""
    issue_number: int
    date: datetime
    subject_line: str
    executive_summary: str
    sections: List[NewsletterSection]
    metrics: NewsletterMetrics
    html_content: str = ""
    text_content: str = ""
    generation_timestamp: datetime = None

class WriterAgent(BaseAgent):
    """
    Writer Agent Implementation
    
    RESPONSIBILITIES:
    - Executive summary generation (Superhuman style)
    - Content organization and structuring
    - Newsletter HTML/text generation
    - Personalization and tone adjustment
    - A/B testing for different styles
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        
        # Configuration
        self.newsletter_style = config.get("newsletter_style", "superhuman")
        self.max_articles_per_newsletter = config.get("max_articles_per_newsletter", 25)
        self.summary_length = config.get("summary_length", 500)
        self.personalization_enabled = config.get("personalization_enabled", False)
        self.ab_testing_enabled = config.get("ab_testing_enabled", False)
        
        # Newsletter template settings
        self.brand_colors = config.get("brand_colors", {
            "primary": "#667eea",
            "secondary": "#764ba2",
            "accent": "#f093fb"
        })
        
        # Generated newsletters storage
        self.generated_newsletters: List[Newsletter] = []
        self.template_variations: Dict[str, str] = {}
        
        # Content formatting rules
        self.formatting_rules = self._initialize_formatting_rules()
        
        logger.info(f"WriterAgent {agent_id} initialized with {self.newsletter_style} style")
    
    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Process newsletter generation tasks
        
        Task Types:
        - "generate_newsletter": Create complete newsletter
        - "create_summary": Generate executive summary only
        - "format_content": Apply formatting and structure
        - "test_subject_lines": A/B test subject lines
        """
        try:
            self.status = AgentStatus.WORKING
            task_type = task.data.get("type")
            
            logger.info(f"WriterAgent processing task: {task_type}")
            
            if task_type == "generate_newsletter":
                return await self._generate_complete_newsletter(task.data)
            elif task_type == "create_summary":
                return await self._create_executive_summary(task.data.get("content_items", []))
            elif task_type == "format_content":
                return await self._format_newsletter_content(task.data)
            elif task_type == "test_subject_lines":
                return await self._test_subject_lines(task.data)
            elif task_type == "get_newsletter_metrics":
                return await self._get_newsletter_metrics()
            else:
                return {"status": "error", "message": f"Unknown task type: {task_type}"}
                
        except Exception as e:
            logger.error(f"WriterAgent task processing error: {e}")
            self.status = AgentStatus.ERROR
            return {"status": "error", "message": str(e)}
        finally:
            if self.status != AgentStatus.ERROR:
                self.status = AgentStatus.COMPLETED
    
    async def _generate_complete_newsletter(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate complete newsletter with all sections
        """
        try:
            content_items = data.get("content_items", [])
            issue_number = data.get("issue_number")
            date = datetime.fromisoformat(data.get("date", datetime.now().isoformat()))
            
            if not content_items:
                return {"status": "error", "message": "No content items provided"}
            
            # Auto-generate issue number if not provided
            if issue_number is None:
                issue_number = len(self.generated_newsletters) + 1
            
            # Calculate newsletter metrics
            metrics = self._calculate_newsletter_metrics(content_items)
            
            # Generate executive summary
            summary_result = await self._create_executive_summary(content_items)
            if summary_result.get("status") != "success":
                return summary_result
            
            executive_summary = summary_result.get("summary", "")
            
            # Organize content into sections
            sections = self._organize_content_into_sections(content_items)
            
            # Generate subject line variations
            subject_lines = self._generate_subject_lines(content_items, metrics)
            primary_subject = subject_lines[0] if subject_lines else f"AEC AI Weekly #{issue_number}"
            
            # Create newsletter object
            newsletter = Newsletter(
                issue_number=issue_number,
                date=date,
                subject_line=primary_subject,
                executive_summary=executive_summary,
                sections=sections,
                metrics=metrics,
                generation_timestamp=datetime.now()
            )
            
            # Generate HTML content
            html_content = self._generate_html_newsletter(newsletter)
            newsletter.html_content = html_content
            
            # Generate text content
            text_content = self._generate_text_newsletter(newsletter)
            newsletter.text_content = text_content
            
            # Store newsletter
            self.generated_newsletters.append(newsletter)
            
            logger.info(f"Generated newsletter #{issue_number} with {metrics.total_articles} articles")
            
            return {
                "status": "success",
                "newsletter": asdict(newsletter),
                "subject_line_variations": subject_lines,
                "metrics": asdict(metrics),
                "html_content": html_content,
                "text_content": text_content,
                "estimated_size_kb": len(html_content.encode('utf-8')) / 1024
            }
            
        except Exception as e:
            logger.error(f"Error generating newsletter: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _create_executive_summary(self, content_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate Superhuman-style executive summary
        """
        try:
            if not content_items:
                return {"status": "error", "message": "No content items provided"}
            
            # Analyze content for summary generation
            analysis = self._analyze_content_for_summary(content_items)
            
            # Generate summary based on style
            if self.newsletter_style == "superhuman":
                summary = self._generate_superhuman_summary(analysis)
            else:
                summary = self._generate_standard_summary(analysis)
            
            # Calculate reading time
            reading_time = self._calculate_reading_time(summary + " ".join(
                item.get("content", "") for item in content_items
            ))
            
            return {
                "status": "success",
                "summary": summary,
                "reading_time_minutes": reading_time,
                "content_analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"Error creating executive summary: {e}")
            return {"status": "error", "message": str(e)}
    
    def _analyze_content_for_summary(self, content_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze content to extract key insights for summary
        """
        total_articles = len(content_items)
        categories = {}
        high_impact_count = 0
        trending_topics = []
        innovation_mentions = 0
        
        # Keywords that indicate innovation/trending topics
        trending_keywords = [
            'breakthrough', 'revolutionary', 'first-of-its-kind', 'cutting-edge',
            'next-generation', 'game-changing', 'disruptive', 'emerging'
        ]
        
        innovation_keywords = [
            'ai', 'artificial intelligence', 'machine learning', 'automation',
            'robotics', 'digital twin', 'smart', 'intelligent'
        ]
        
        for item in content_items:
            # Category analysis
            category = item.get("category", "General")
            categories[category] = categories.get(category, 0) + 1
            
            # Impact analysis
            business_impact = item.get("business_impact", "low")
            if business_impact == "high":
                high_impact_count += 1
            
            # Content analysis
            content_text = (item.get("content", "") + " " + item.get("title", "")).lower()
            
            # Check for trending indicators
            for keyword in trending_keywords:
                if keyword in content_text:
                    trending_topics.append(item.get("title", "")[:50])
                    break
            
            # Check for innovation mentions
            innovation_score = sum(1 for keyword in innovation_keywords if keyword in content_text)
            if innovation_score >= 2:
                innovation_mentions += 1
        
        # Find top categories
        top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            "total_articles": total_articles,
            "categories": dict(categories),
            "top_categories": top_categories,
            "high_impact_count": high_impact_count,
            "trending_topics": trending_topics[:5],  # Top 5 trending
            "innovation_mentions": innovation_mentions,
            "quality_indicators": {
                "high_impact_ratio": high_impact_count / max(total_articles, 1),
                "category_diversity": len(categories),
                "innovation_ratio": innovation_mentions / max(total_articles, 1)
            }
        }
    
    def _generate_superhuman_summary(self, analysis: Dict[str, Any]) -> str:
        """
        Generate Superhuman-style executive summary
        """
        total_articles = analysis["total_articles"]
        top_categories = analysis["top_categories"]
        high_impact = analysis["high_impact_count"]
        trending = analysis["trending_topics"]
        innovation_ratio = analysis["quality_indicators"]["innovation_ratio"]
        
        current_date = datetime.now().strftime("%B %d, %Y")
        
        # Dynamic greeting based on content quality
        if innovation_ratio > 0.6:
            greeting = "Incredible week for AEC innovation!"
        elif high_impact > 5:
            greeting = "Power-packed edition incoming!"
        else:
            greeting = "Hello, AEC innovators!"
        
        # Main summary content
        summary = f"""
{greeting}

Welcome to your FREE {current_date} AEC AI intelligence briefing! I've personally curated **{total_articles} game-changing stories** from across the industry.

**This week's power moves:**
"""
        
        # Add top category insights
        if top_categories:
            top_cat, top_count = top_categories[0]
            summary += f"• **{top_cat}** is absolutely exploding right now (**{top_count} major developments**)\n"
        
        summary += f"• **{high_impact} 'drop everything and read this'** level stories\n"
        
        # Add trending insights
        if trending:
            summary += f"• **{len(trending)} breakthrough announcements** you need to know about\n"
        
        # Add innovation insight
        if innovation_ratio > 0.4:
            summary += "• **AI adoption acceleration** across multiple AEC sectors\n"
        
        # Add category breakdown
        if len(top_categories) > 1:
            other_cats = [cat for cat, count in top_categories[1:3]]
            summary += f"• Strong developments in **{', '.join(other_cats)}**\n"
        
        # Action plan
        summary += f"""
**Your 3-minute action plan:**
1. **Quick wins** → Scan the high-impact stories for immediate opportunities
2. **Strategic intel** → Bookmark the breakthrough technologies for Q4 planning  
3. **Competitive edge** → Forward the best insights to your team

**Why this newsletter stays FREE:**
Because great information should be accessible to everyone building the future. I monetize through consulting and industry partnerships – never your inbox.

**Reading time:** ~{total_articles * 1.5:.0f} minutes total (perfectly digestible!)

*Found value here? Share with a colleague who'd appreciate staying ahead of the curve!*

Let's dive in!
        """.strip()
        
        return summary
    
    def _generate_standard_summary(self, analysis: Dict[str, Any]) -> str:
        """
        Generate standard executive summary
        """
        total_articles = analysis["total_articles"]
        top_categories = analysis["top_categories"]
        high_impact = analysis["high_impact_count"]
        
        summary = f"""
**Executive Summary**

This week's AEC AI news digest includes {total_articles} curated articles covering the latest developments in artificial intelligence applications for the architecture, engineering, and construction industry.

**Key Highlights:**
- {high_impact} high-impact stories requiring immediate attention
- Major developments in {', '.join([cat for cat, count in top_categories[:2]])}
- Comprehensive coverage across {len(analysis['categories'])} industry categories

**Content Organization:**
Articles are organized by business impact and industry relevance to help busy professionals quickly identify the most important developments.
        """.strip()
        
        return summary
    
    def _organize_content_into_sections(self, content_items: List[Dict[str, Any]]) -> List[NewsletterSection]:
        """
        Organize content into structured newsletter sections
        """
        sections = []
        
        # Group by business impact first
        high_impact = []
        medium_impact = []
        low_impact = []
        
        for item in content_items:
            impact = item.get("business_impact", "low")
            if impact == "high":
                high_impact.append(item)
            elif impact == "medium":
                medium_impact.append(item)
            else:
                low_impact.append(item)
        
        # Create high impact section
        if high_impact:
            sections.append(NewsletterSection(
                title="Must-Read: High Impact Developments",
                content="Critical developments that could significantly impact your business operations and strategic planning.",
                articles=high_impact[:8],  # Limit to top 8
                priority=1
            ))
        
        # Group medium impact by category
        medium_by_category = {}
        for item in medium_impact:
            category = item.get("category", "General")
            if category not in medium_by_category:
                medium_by_category[category] = []
            medium_by_category[category].append(item)
        
        # Create category sections for medium impact
        for category, items in medium_by_category.items():
            if len(items) >= 2:  # Only create section if multiple articles
                sections.append(NewsletterSection(
                    title=f"Industry Focus: {category}",
                    content=f"Latest developments and trends in {category.lower()}.",
                    articles=items[:5],  # Limit per category
                    priority=2
                ))
        
        # Create emerging trends section for low impact but interesting content
        if low_impact:
            trending_items = [item for item in low_impact if self._is_trending_content(item)]
            if trending_items:
                sections.append(NewsletterSection(
                    title="Emerging Trends & Research",
                    content="Early-stage developments and research findings worth monitoring.",
                    articles=trending_items[:5],
                    priority=3
                ))
        
        return sections
    
    def _is_trending_content(self, item: Dict[str, Any]) -> bool:
        """
        Determine if content represents trending topics
        """
        content_text = (item.get("content", "") + " " + item.get("title", "")).lower()
        
        trending_indicators = [
            'emerging', 'future', 'next-generation', 'upcoming', 'pilot',
            'beta', 'prototype', 'research', 'study', 'experiment'
        ]
        
        return any(indicator in content_text for indicator in trending_indicators)
    
    def _generate_subject_lines(self, content_items: List[Dict[str, Any]], metrics: NewsletterMetrics) -> List[str]:
        """
        Generate multiple subject line variations for A/B testing
        """
        current_date = datetime.now()
        week_descriptor = self._get_week_descriptor(current_date)
        
        # Analyze content for subject line generation
        top_topics = []
        innovation_count = 0
        
        for item in content_items:
            if item.get("business_impact") == "high":
                title = item.get("title", "")
                # Extract key terms from title
                if any(word in title.lower() for word in ['ai', 'artificial intelligence', 'automation']):
                    innovation_count += 1
                    top_topics.append(self._extract_key_topic(title))
        
        subject_lines = []
        
        # Primary subject line (performance focused)
        if innovation_count >= 5:
            subject_lines.append(f"AI revolution in AEC: {innovation_count} major breakthroughs this {week_descriptor}")
        elif metrics.high_impact_articles >= 3:
            subject_lines.append(f"{metrics.high_impact_articles} game-changing AEC developments you can't miss")
        else:
            subject_lines.append(f"Your {week_descriptor} AEC AI intelligence briefing")
        
        # Alternative subject lines for A/B testing
        if self.ab_testing_enabled:
            subject_lines.extend([
                f"AEC AI Weekly: {metrics.total_articles} curated insights",
                f"What's revolutionizing construction this {week_descriptor}?",
                f"Your competitive edge: {current_date.strftime('%b %d')} AEC intel",
                f"Breaking: Major AEC AI developments this {week_descriptor}"
            ])
        
        return subject_lines[:5]  # Return top 5 variations
    
    def _get_week_descriptor(self, date: datetime) -> str:
        """
        Get appropriate week descriptor (week/month)
        """
        day = date.day
        if day <= 7:
            return "week"
        elif day <= 14:
            return "week"
        else:
            return "month"
    
    def _extract_key_topic(self, title: str) -> str:
        """
        Extract key topic from article title
        """
        # Simple extraction - find technology/topic keywords
        tech_keywords = [
            'AI', 'artificial intelligence', 'machine learning', 'automation',
            'BIM', 'digital twin', 'robotics', 'IoT', 'smart building'
        ]
        
        title_lower = title.lower()
        for keyword in tech_keywords:
            if keyword.lower() in title_lower:
                return keyword
        
        # Fallback to first significant word
        words = title.split()
        for word in words:
            if len(word) > 4 and word.lower() not in ['this', 'that', 'with', 'from']:
                return word
        
        return "Technology"
    
    def _calculate_newsletter_metrics(self, content_items: List[Dict[str, Any]]) -> NewsletterMetrics:
        """
        Calculate newsletter performance metrics
        """
        total_articles = len(content_items)
        high_impact_count = sum(1 for item in content_items if item.get("business_impact") == "high")
        
        # Count unique categories
        categories = set(item.get("category", "General") for item in content_items)
        categories_covered = len(categories)
        
        # Calculate reading time (150 words per minute average)
        total_words = 0
        quality_scores = []
        
        for item in content_items:
            content = item.get("content", "")
            total_words += len(content.split())
            
            # Extract quality score if available
            quality_score = item.get("quality_score", 0.5)
            quality_scores.append(quality_score)
        
        estimated_read_time = max(1, total_words // 150)  # minutes
        quality_avg = sum(quality_scores) / len(quality_scores) if quality_scores else 0.5
        
        # Content freshness (simplified)
        freshness_avg = 0.8  # Assume most content is fresh
        
        return NewsletterMetrics(
            total_articles=total_articles,
            high_impact_articles=high_impact_count,
            categories_covered=categories_covered,
            estimated_read_time=estimated_read_time,
            content_freshness_avg=freshness_avg,
            quality_score_avg=quality_avg
        )
    
    def _calculate_reading_time(self, text: str) -> int:
        """
        Calculate estimated reading time in minutes
        """
        words = len(text.split())
        return max(1, words // 150)  # 150 words per minute
    
    def _generate_html_newsletter(self, newsletter: Newsletter) -> str:
        """
        Generate HTML version of newsletter
        """
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AEC AI Weekly #{newsletter.issue_number}</title>
    <style>
        {self._get_newsletter_css()}
    </style>
</head>
<body>
    <div class="container">
        {self._generate_html_header(newsletter)}
        {self._generate_html_summary(newsletter)}
        {self._generate_html_sections(newsletter)}
        {self._generate_html_footer(newsletter)}
    </div>
</body>
</html>
        """.strip()
        
        return html
    
    def _get_newsletter_css(self) -> str:
        """
        Get CSS styles for newsletter
        """
        return f"""
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            background-color: #f8fafc;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, {self.brand_colors['primary']} 0%, {self.brand_colors['secondary']} 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 700;
        }}
        .header .meta {{
            margin-top: 10px;
            opacity: 0.9;
            font-size: 14px;
        }}
        .summary {{
            background: white;
            padding: 30px;
            border-left: 4px solid {self.brand_colors['primary']};
            margin: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section {{
            margin: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .section-header {{
            background: {self.brand_colors['primary']};
            color: white;
            padding: 15px 20px;
            font-weight: 600;
            font-size: 18px;
        }}
        .section-content {{
            padding: 20px;
        }}
        .article {{
            border-bottom: 1px solid #e2e8f0;
            padding: 20px 0;
        }}
        .article:last-child {{
            border-bottom: none;
        }}
        .article h3 {{
            margin: 0 0 10px 0;
            color: #2d3748;
            font-size: 16px;
        }}
        .article a {{
            color: {self.brand_colors['primary']};
            text-decoration: none;
        }}
        .article a:hover {{
            text-decoration: underline;
        }}
        .impact-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
            margin-bottom: 8px;
        }}
        .impact-high {{ background: #fed7d7; color: #c53030; }}
        .impact-medium {{ background: #feebc8; color: #dd6b20; }}
        .impact-low {{ background: #c6f6d5; color: #2f855a; }}
        .footer {{
            text-align: center;
            padding: 30px;
            color: #718096;
            font-size: 14px;
            background: #f7fafc;
        }}
        .metrics {{
            background: #f7fafc;
            padding: 15px 20px;
            margin: 20px;
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
        }}
        .metric {{
            text-align: center;
            flex: 1;
            min-width: 120px;
        }}
        .metric-value {{
            font-weight: bold;
            font-size: 24px;
            color: {self.brand_colors['primary']};
        }}
        .metric-label {{
            font-size: 12px;
            color: #718096;
            text-transform: uppercase;
        }}
        """
    
    def _generate_html_header(self, newsletter: Newsletter) -> str:
        """
        Generate HTML header section
        """
        return f"""
        <div class="header">
            <h1>AEC AI Weekly</h1>
            <div class="meta">
                Issue #{newsletter.issue_number} • {newsletter.date.strftime('%B %d, %Y')} • {newsletter.metrics.estimated_read_time} min read
            </div>
        </div>
        """
    
    def _generate_html_summary(self, newsletter: Newsletter) -> str:
        """
        Generate HTML summary section
        """
        # Convert markdown-style formatting to HTML
        summary_html = newsletter.executive_summary.replace('\n', '<br>')
        summary_html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', summary_html)
        summary_html = re.sub(r'• (.*?)(?=<br>|$)', r'<li>\1</li>', summary_html)
        summary_html = re.sub(r'(<li>.*</li>)', r'<ul>\1</ul>', summary_html)
        
        return f"""
        <div class="summary">
            {summary_html}
        </div>
        
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">{newsletter.metrics.total_articles}</div>
                <div class="metric-label">Articles</div>
            </div>
            <div class="metric">
                <div class="metric-value">{newsletter.metrics.high_impact_articles}</div>
                <div class="metric-label">High Impact</div>
            </div>
            <div class="metric">
                <div class="metric-value">{newsletter.metrics.categories_covered}</div>
                <div class="metric-label">Categories</div>
            </div>
            <div class="metric">
                <div class="metric-value">{newsletter.metrics.quality_score_avg:.1f}</div>
                <div class="metric-label">Avg Quality</div>
            </div>
        </div>
        """
    
    def _generate_html_sections(self, newsletter: Newsletter) -> str:
        """
        Generate HTML for all newsletter sections
        """
        sections_html = ""
        
        for section in newsletter.sections:
            articles_html = ""
            
            for article in section.articles:
                impact = article.get("business_impact", "low")
                impact_class = f"impact-{impact}"
                
                # Clean up title and summary
                title = article.get("title", "No title")
                summary = article.get("summary", "")[:200] + "..." if len(article.get("summary", "")) > 200 else article.get("summary", "")
                url = article.get("url", "#")
                source = article.get("source", "Unknown source")
                
                articles_html += f"""
                <div class="article">
                    <span class="impact-badge {impact_class}">{impact} impact</span>
                    <h3><a href="{url}" target="_blank">{title}</a></h3>
                    <p>{summary}</p>
                    <small>Source: {self._extract_domain_from_url(source)}</small>
                </div>
                """
            
            sections_html += f"""
            <div class="section">
                <div class="section-header">{section.title}</div>
                <div class="section-content">
                    <p><em>{section.content}</em></p>
                    {articles_html}
                </div>
            </div>
            """
        
        return sections_html
    
    def _generate_html_footer(self, newsletter: Newsletter) -> str:
        """
        Generate HTML footer
        """
        return f"""
        <div class="footer">
            <p>Made with care for the AEC community<br>
            <a href="#unsubscribe">Unsubscribe</a> | <a href="#archive">View Archive</a> | <a href="#feedback">Feedback</a></p>
            <p><small>Generated on {newsletter.generation_timestamp.strftime('%Y-%m-%d %H:%M')} UTC</small></p>
        </div>
        """
    
    def _generate_text_newsletter(self, newsletter: Newsletter) -> str:
        """
        Generate plain text version of newsletter
        """
        text = f"""
AEC AI WEEKLY #{newsletter.issue_number}
{newsletter.date.strftime('%B %d, %Y')} • {newsletter.metrics.estimated_read_time} min read

{newsletter.executive_summary}

NEWSLETTER METRICS:
- Total Articles: {newsletter.metrics.total_articles}
- High Impact: {newsletter.metrics.high_impact_articles}
- Categories: {newsletter.metrics.categories_covered}
- Quality Score: {newsletter.metrics.quality_score_avg:.1f}/1.0

"""
        
        # Add sections
        for section in newsletter.sections:
            text += f"\n{section.title.upper()}\n"
            text += "=" * len(section.title) + "\n"
            text += f"{section.content}\n\n"
            
            for i, article in enumerate(section.articles, 1):
                title = article.get("title", "No title")
                url = article.get("url", "")
                impact = article.get("business_impact", "low")
                summary = article.get("summary", "")
                
                text += f"{i}. [{impact.upper()} IMPACT] {title}\n"
                if summary:
                    text += f"   {summary[:150]}...\n"
                text += f"   Read more: {url}\n\n"
        
        text += """
---
Made with care for the AEC community
Unsubscribe | Archive | Feedback
        """.strip()
        
        return text
    
    def _extract_domain_from_url(self, url: str) -> str:
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
    
    async def _format_newsletter_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply formatting and structure to newsletter content
        """
        try:
            content = data.get("content", "")
            format_type = data.get("format", "html")
            
            if format_type == "html":
                formatted_content = self._apply_html_formatting(content)
            else:
                formatted_content = self._apply_text_formatting(content)
            
            return {
                "status": "success",
                "formatted_content": formatted_content,
                "original_length": len(content),
                "formatted_length": len(formatted_content)
            }
            
        except Exception as e:
            logger.error(f"Error formatting content: {e}")
            return {"status": "error", "message": str(e)}
    
    def _apply_html_formatting(self, content: str) -> str:
        """
        Apply HTML formatting rules
        """
        # Apply markdown-like formatting
        formatted = content
        
        # Bold text
        formatted = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', formatted)
        
        # Italic text
        formatted = re.sub(r'\*(.*?)\*', r'<em>\1</em>', formatted)
        
        # Links
        formatted = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', formatted)
        
        # Line breaks
        formatted = formatted.replace('\n\n', '</p><p>').replace('\n', '<br>')
        
        # Wrap in paragraphs
        if not formatted.startswith('<p>'):
            formatted = f'<p>{formatted}</p>'
        
        return formatted
    
    def _apply_text_formatting(self, content: str) -> str:
        """
        Apply text formatting rules
        """
        # Clean up extra whitespace
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            cleaned_line = line.strip()
            if cleaned_line:
                cleaned_lines.append(cleaned_line)
            elif cleaned_lines and cleaned_lines[-1]:  # Preserve paragraph breaks
                cleaned_lines.append('')
        
        return '\n'.join(cleaned_lines)
    
    async def _test_subject_lines(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        A/B test subject lines
        """
        try:
            subject_lines = data.get("subject_lines", [])
            
            if not subject_lines:
                return {"status": "error", "message": "No subject lines provided for testing"}
            
            # Simple scoring based on length, keywords, and engagement factors
            results = []
            
            for subject in subject_lines:
                score = self._score_subject_line(subject)
                results.append({
                    "subject_line": subject,
                    "score": score,
                    "length": len(subject),
                    "word_count": len(subject.split())
                })
            
            # Sort by score
            results.sort(key=lambda x: x["score"], reverse=True)
            
            return {
                "status": "success",
                "test_results": results,
                "recommended": results[0] if results else None,
                "total_tested": len(subject_lines)
            }
            
        except Exception as e:
            logger.error(f"Error testing subject lines: {e}")
            return {"status": "error", "message": str(e)}
    
    def _score_subject_line(self, subject: str) -> float:
        """
        Score subject line for effectiveness
        """
        score = 0.0
        subject_lower = subject.lower()
        
        # Length optimization (30-50 characters ideal)
        length = len(subject)
        if 30 <= length <= 50:
            score += 20
        elif 20 <= length < 30 or 50 < length <= 60:
            score += 15
        else:
            score += 5
        
        # Power words
        power_words = [
            'breakthrough', 'exclusive', 'urgent', 'breaking', 'revolutionary',
            'game-changing', 'must-read', 'critical', 'major', 'insider'
        ]
        score += sum(10 for word in power_words if word in subject_lower)
        
        # Numbers and specificity
        if any(char.isdigit() for char in subject):
            score += 15
        
        # Urgency indicators
        urgency_words = ['this week', 'today', 'now', 'latest', 'new']
        score += sum(5 for word in urgency_words if word in subject_lower)
        
        # Question format
        if subject.endswith('?'):
            score += 10
        
        # Personalization
        if 'your' in subject_lower:
            score += 5
        
        return min(100, score)  # Cap at 100
    
    async def _get_newsletter_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive newsletter metrics
        """
        try:
            if not self.generated_newsletters:
                return {
                    "status": "success",
                    "message": "No newsletters generated yet",
                    "metrics": {}
                }
            
            total_newsletters = len(self.generated_newsletters)
            
            # Calculate averages
            avg_articles = sum(n.metrics.total_articles for n in self.generated_newsletters) / total_newsletters
            avg_high_impact = sum(n.metrics.high_impact_articles for n in self.generated_newsletters) / total_newsletters
            avg_read_time = sum(n.metrics.estimated_read_time for n in self.generated_newsletters) / total_newsletters
            avg_quality = sum(n.metrics.quality_score_avg for n in self.generated_newsletters) / total_newsletters
            
            # Recent performance (last 5 newsletters)
            recent_newsletters = self.generated_newsletters[-5:]
            recent_avg_quality = sum(n.metrics.quality_score_avg for n in recent_newsletters) / len(recent_newsletters)
            
            return {
                "status": "success",
                "metrics": {
                    "total_newsletters_generated": total_newsletters,
                    "averages": {
                        "articles_per_newsletter": avg_articles,
                        "high_impact_per_newsletter": avg_high_impact,
                        "read_time_minutes": avg_read_time,
                        "quality_score": avg_quality
                    },
                    "recent_performance": {
                        "last_5_newsletters_quality": recent_avg_quality,
                        "quality_trend": "improving" if recent_avg_quality > avg_quality else "declining"
                    },
                    "latest_newsletter": asdict(self.generated_newsletters[-1].metrics) if self.generated_newsletters else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting newsletter metrics: {e}")
            return {"status": "error", "message": str(e)}
    
    def _initialize_formatting_rules(self) -> Dict[str, Any]:
        """
        Initialize content formatting rules
        """
        return {
            "max_line_length": 80,
            "paragraph_spacing": True,
            "auto_link_urls": True,
            "emoji_support": True,
            "markdown_support": True
        }
    
    async def health_check(self) -> bool:
        """
        Check writer health
        """
        try:
            # Test summary generation
            test_items = [{
                "title": "Test AI Article",
                "content": "This is a test article about artificial intelligence in construction.",
                "category": "AI Design Tools",
                "business_impact": "medium"
            }]
            
            result = await self._create_executive_summary(test_items)
            return result.get("status") == "success"
            
        except Exception as e:
            logger.error(f"Writer health check error: {e}")
            return False
    
    async def cleanup(self):
        """
        Cleanup writer resources
        """
        # Keep only recent newsletters in memory
        if len(self.generated_newsletters) > 50:
            self.generated_newsletters = self.generated_newsletters[-25:]
        
        logger.info(f"WriterAgent {self.agent_id} cleaned up")