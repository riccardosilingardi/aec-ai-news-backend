# Multi-stage Docker build for AEC AI News Multi-Agent System
# Alternative deployment option for containerized environments

# Stage 1: Base Python environment
FROM python:3.11-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Development environment
FROM base as development

# Install development dependencies
COPY backend/requirements_enhanced.txt requirements_enhanced.txt
RUN pip install --no-cache-dir -r requirements_enhanced.txt

# Copy source code
COPY backend/ .

# Expose ports
EXPOSE 8000 3000

# Development command
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Stage 3: Production environment
FROM base as production

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy only necessary files
COPY backend/core/ ./core/
COPY backend/agents/ ./agents/
COPY backend/mcp/ ./mcp/
COPY backend/multi_agent_system.py .
COPY backend/main.py .

# Set up logging directory
RUN mkdir -p /app/logs && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Production command
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Stage 4: MCP Server only
FROM base as mcp-server

# Copy MCP-specific files
COPY backend/core/ ./core/
COPY backend/mcp/ ./mcp/
COPY backend/agents/ ./agents/
COPY backend/mcp_server_main.py .

# Create non-root user
RUN groupadd -r mcpuser && useradd -r -g mcpuser mcpuser
RUN chown -R mcpuser:mcpuser /app
USER mcpuser

# Expose MCP port
EXPOSE 3000

# Health check for MCP server
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# MCP server command
CMD ["python", "mcp_server_main.py"]