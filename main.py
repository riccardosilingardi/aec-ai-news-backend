#!/usr/bin/env python3
"""
AEC AI News Multi-Agent System - Production Server
FastAPI application for Render deployment
"""
import os
import sys
import logging
from typing import Dict, Any
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.multi_agent_system import MultiAgentSystem
from backend.mcp.server import AECMCPServer
from backend.core.config import SystemConfig

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global system instance
multi_agent_system = None
mcp_server = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global multi_agent_system, mcp_server
    
    logger.info("Starting AEC AI News Multi-Agent System...")
    
    try:
        # Initialize system configuration
        config = SystemConfig({
            'database_url': os.getenv('SUPABASE_URL'),
            'database_key': os.getenv('SUPABASE_SERVICE_KEY'),
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
            'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
            'email_service_key': os.getenv('EMAIL_SERVICE_KEY'),
            'webhook_secret': os.getenv('WEBHOOK_SECRET'),
            'environment': os.getenv('ENVIRONMENT', 'production')
        })
        
        # Initialize multi-agent system
        multi_agent_system = MultiAgentSystem(config)
        await multi_agent_system.initialize()
        
        # Initialize MCP server
        mcp_server = AECMCPServer(multi_agent_system)
        await mcp_server.start()
        
        logger.info("System initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize system: {e}")
        raise
    finally:
        # Cleanup
        if mcp_server:
            await mcp_server.stop()
        if multi_agent_system:
            await multi_agent_system.shutdown()
        logger.info("System shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="AEC AI News Multi-Agent System",
    description="AI-powered newsletter system for Architecture, Engineering & Construction",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "AEC AI News Multi-Agent System", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        if not multi_agent_system:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        health_status = await multi_agent_system.get_health_status()
        return JSONResponse(
            status_code=200 if health_status.get('healthy', False) else 503,
            content=health_status
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"healthy": False, "error": str(e)}
        )

@app.post("/api/content/discover")
async def trigger_content_discovery(background_tasks: BackgroundTasks):
    """Trigger content discovery process"""
    try:
        if not multi_agent_system:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        # Run discovery in background
        background_tasks.add_task(multi_agent_system.run_content_discovery)
        
        return {"message": "Content discovery started", "status": "initiated"}
    except Exception as e:
        logger.error(f"Content discovery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/content/generate")
async def generate_newsletter(background_tasks: BackgroundTasks):
    """Generate newsletter"""
    try:
        if not multi_agent_system:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        # Run generation in background
        background_tasks.add_task(multi_agent_system.generate_newsletter)
        
        return {"message": "Newsletter generation started", "status": "initiated"}
    except Exception as e:
        logger.error(f"Newsletter generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/tools")
async def get_mcp_tools():
    """Get available MCP tools"""
    try:
        if not mcp_server:
            raise HTTPException(status_code=503, detail="MCP server not initialized")
        
        tools = await mcp_server.get_available_tools()
        return {"tools": tools}
    except Exception as e:
        logger.error(f"Failed to get MCP tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/{agent_name}/execute")
async def execute_agent(agent_name: str, task: Dict[str, Any]):
    """Execute specific agent task"""
    try:
        if not multi_agent_system:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        result = await multi_agent_system.execute_agent_task(agent_name, task)
        return {"result": result, "agent": agent_name}
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/status")
async def get_system_status():
    """Get detailed system status"""
    try:
        if not multi_agent_system:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        status = await multi_agent_system.get_system_status()
        return status
    except Exception as e:
        logger.error(f"System status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/newsletters")
async def get_newsletters():
    """Get newsletter history"""
    try:
        if not multi_agent_system:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        newsletters = await multi_agent_system.get_newsletter_history()
        return {"newsletters": newsletters}
    except Exception as e:
        logger.error(f"Failed to get newsletters: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )