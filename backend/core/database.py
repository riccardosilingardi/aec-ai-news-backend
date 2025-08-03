"""
Database Layer - SQLite for development, PostgreSQL for production

TODO:
[ ] Article storage with full metadata
[ ] Newsletter issue tracking
[ ] Source performance metrics
[ ] User subscription management (integration with Supabase)
[ ] Content analytics and engagement tracking
[ ] Agent performance logging
"""

import sqlite3
import asyncio
import aiosqlite
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import asdict
import json
import os

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False

from .agent_base import ContentItem

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Unified database interface for multi-agent system"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or "sqlite:///aec_ai_news.db"
        self.is_postgres = self.database_url.startswith("postgresql://")
        self.pool = None
        self.sqlite_path = None
        
        if not self.is_postgres:
            # Extract SQLite path
            self.sqlite_path = self.database_url.replace("sqlite:///", "")
            if not os.path.isabs(self.sqlite_path):
                self.sqlite_path = os.path.join(os.getcwd(), self.sqlite_path)
    
    async def initialize(self):
        """Initialize database connection and create tables"""
        if self.is_postgres and ASYNCPG_AVAILABLE:
            await self._init_postgres()
        else:
            await self._init_sqlite()
        await self._create_tables()
    
    async def _init_postgres(self):
        """Initialize PostgreSQL connection pool"""
        try:
            self.pool = await asyncpg.create_pool(self.database_url)
            logger.info("PostgreSQL connection pool created")
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL pool: {e}")
            raise
    
    async def _init_sqlite(self):
        """Initialize SQLite database"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.sqlite_path), exist_ok=True)
            logger.info(f"SQLite database initialized at: {self.sqlite_path}")
        except Exception as e:
            logger.error(f"Failed to initialize SQLite: {e}")
            raise
    
    async def _create_tables(self):
        """Create database tables"""
        if self.is_postgres:
            await self._create_postgres_tables()
        else:
            await self._create_sqlite_tables()
    
    async def _create_sqlite_tables(self):
        """Create SQLite tables"""
        async with aiosqlite.connect(self.sqlite_path) as db:
            # Articles table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL,
                    discovered_at TIMESTAMP NOT NULL,
                    content_type TEXT DEFAULT 'rss',
                    quality_score REAL DEFAULT 0.0,
                    ai_relevance REAL DEFAULT 0.0,
                    category TEXT DEFAULT '',
                    sentiment TEXT DEFAULT '',
                    processing_status TEXT DEFAULT 'new',
                    agent_metadata TEXT,
                    content_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Newsletter issues table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS newsletter_issues (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    issue_number INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    html_content TEXT,
                    published_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    open_rate REAL,
                    click_rate REAL,
                    subscriber_count INTEGER
                )
            """)
            
            # Source metrics table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS source_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    last_scraped TIMESTAMP,
                    last_success TIMESTAMP,
                    success_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    avg_response_time REAL,
                    reliability_score REAL DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Agent performance table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS agent_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    agent_type TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    execution_time REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    error_message TEXT
                )
            """)
            
            await db.commit()
            logger.info("SQLite tables created successfully")
    
    async def _create_postgres_tables(self):
        """Create PostgreSQL tables"""
        async with self.pool.acquire() as conn:
            # Articles table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id SERIAL PRIMARY KEY,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL,
                    discovered_at TIMESTAMP NOT NULL,
                    content_type TEXT DEFAULT 'rss',
                    quality_score REAL DEFAULT 0.0,
                    ai_relevance REAL DEFAULT 0.0,
                    category TEXT DEFAULT '',
                    sentiment TEXT DEFAULT '',
                    processing_status TEXT DEFAULT 'new',
                    agent_metadata JSONB,
                    content_hash TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Newsletter issues table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS newsletter_issues (
                    id SERIAL PRIMARY KEY,
                    issue_number INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    html_content TEXT,
                    published_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW(),
                    open_rate REAL,
                    click_rate REAL,
                    subscriber_count INTEGER
                )
            """)
            
            logger.info("PostgreSQL tables created successfully")
    
    async def store_content_item(self, item: ContentItem) -> int:
        """Store a content item in the database"""
        try:
            if self.is_postgres:
                return await self._store_content_postgres(item)
            else:
                return await self._store_content_sqlite(item)
        except Exception as e:
            logger.error(f"Error storing content item: {e}")
            raise
    
    async def _store_content_sqlite(self, item: ContentItem) -> int:
        """Store content item in SQLite"""
        async with aiosqlite.connect(self.sqlite_path) as db:
            cursor = await db.execute("""
                INSERT OR REPLACE INTO articles (
                    url, title, content, source, discovered_at,
                    content_type, quality_score, ai_relevance,
                    category, sentiment, processing_status,
                    agent_metadata, content_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.url, item.title, item.content, item.source,
                item.discovered_at, item.content_type, item.quality_score,
                item.ai_relevance, item.category, item.sentiment,
                item.processing_status, json.dumps(item.agent_metadata or {}),
                getattr(item, 'content_hash', None)
            ))
            await db.commit()
            return cursor.lastrowid
    
    async def _store_content_postgres(self, item: ContentItem) -> int:
        """Store content item in PostgreSQL"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO articles (
                    url, title, content, source, discovered_at,
                    content_type, quality_score, ai_relevance,
                    category, sentiment, processing_status,
                    agent_metadata, content_hash
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                ON CONFLICT (url) DO UPDATE SET
                    title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    quality_score = EXCLUDED.quality_score,
                    ai_relevance = EXCLUDED.ai_relevance,
                    category = EXCLUDED.category,
                    sentiment = EXCLUDED.sentiment,
                    processing_status = EXCLUDED.processing_status,
                    agent_metadata = EXCLUDED.agent_metadata
                RETURNING id
            """, item.url, item.title, item.content, item.source,
                item.discovered_at, item.content_type, item.quality_score,
                item.ai_relevance, item.category, item.sentiment,
                item.processing_status, item.agent_metadata or {},
                getattr(item, 'content_hash', None)
            )
            return row['id']
    
    async def get_content_by_status(self, status: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get content items by processing status"""
        if self.is_postgres:
            return await self._get_content_postgres(status, limit)
        else:
            return await self._get_content_sqlite(status, limit)
    
    async def _get_content_sqlite(self, status: str, limit: int) -> List[Dict[str, Any]]:
        """Get content from SQLite"""
        async with aiosqlite.connect(self.sqlite_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM articles 
                WHERE processing_status = ? 
                ORDER BY discovered_at DESC 
                LIMIT ?
            """, (status, limit)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def _get_content_postgres(self, status: str, limit: int) -> List[Dict[str, Any]]:
        """Get content from PostgreSQL"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM articles 
                WHERE processing_status = $1 
                ORDER BY discovered_at DESC 
                LIMIT $2
            """, status, limit)
            return [dict(row) for row in rows]
    
    async def update_content_status(self, content_id: int, status: str, 
                                  quality_score: float = None, 
                                  ai_relevance: float = None,
                                  category: str = None):
        """Update content processing status and scores"""
        updates = ["processing_status = ?"]
        params = [status]
        
        if quality_score is not None:
            updates.append("quality_score = ?")
            params.append(quality_score)
        
        if ai_relevance is not None:
            updates.append("ai_relevance = ?")
            params.append(ai_relevance)
        
        if category is not None:
            updates.append("category = ?")
            params.append(category)
        
        params.append(content_id)
        
        if self.is_postgres:
            # Convert to PostgreSQL syntax
            updates = [u.replace("?", f"${i+1}") for i, u in enumerate(updates)]
            query = f"UPDATE articles SET {', '.join(updates)} WHERE id = ${len(params)}"
            async with self.pool.acquire() as conn:
                await conn.execute(query, *params)
        else:
            query = f"UPDATE articles SET {', '.join(updates)} WHERE id = ?"
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute(query, params)
                await db.commit()
    
    async def log_agent_performance(self, agent_id: str, agent_type: str, 
                                  task_type: str, execution_time: float, 
                                  status: str, error_message: str = None):
        """Log agent performance metrics"""
        if self.is_postgres:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO agent_performance 
                    (agent_id, agent_type, task_type, execution_time, status, error_message)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, agent_id, agent_type, task_type, execution_time, status, error_message)
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute("""
                    INSERT INTO agent_performance 
                    (agent_id, agent_type, task_type, execution_time, status, error_message)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (agent_id, agent_type, task_type, execution_time, status, error_message))
                await db.commit()
    
    async def cleanup(self):
        """Cleanup database connections"""
        if self.is_postgres and self.pool:
            await self.pool.close()
        logger.info("Database connections cleaned up")