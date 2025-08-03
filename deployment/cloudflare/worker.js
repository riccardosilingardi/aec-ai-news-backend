/**
 * Cloudflare Worker for AEC AI News Multi-Agent System
 * Serverless backend deployment
 */

import { MultiAgentSystem } from '../backend/multi_agent_system.js';
import { AECMCPServer } from '../backend/mcp/server.js';
import { SystemConfig } from '../backend/core/config.js';

// Durable Object for Agent Orchestrator
export class AgentOrchestrator {
  constructor(state, env) {
    this.state = state;
    this.env = env;
    this.multiAgentSystem = null;
  }

  async fetch(request) {
    try {
      if (!this.multiAgentSystem) {
        await this.initializeSystem();
      }

      const url = new URL(request.url);
      
      switch (url.pathname) {
        case '/health':
          return await this.handleHealthCheck();
        
        case '/task':
          return await this.handleTaskExecution(request);
        
        case '/status':
          return await this.handleSystemStatus();
        
        default:
          return new Response('Not Found', { status: 404 });
      }
    } catch (error) {
      console.error('Worker error:', error);
      return new Response(JSON.stringify({ error: error.message }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  }

  async initializeSystem() {
    const config = new SystemConfig({
      database_url: this.env.SUPABASE_URL,
      environment: this.env.ENVIRONMENT || 'production',
      log_level: this.env.LOG_LEVEL || 'info'
    });

    this.multiAgentSystem = new MultiAgentSystem(config);
    await this.multiAgentSystem.initialize();
  }

  async handleHealthCheck() {
    const health = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      system_initialized: !!this.multiAgentSystem,
      agents: {}
    };

    if (this.multiAgentSystem) {
      for (const [agentType, agent] of Object.entries(this.multiAgentSystem.agents)) {
        health.agents[agentType] = await agent.health_check();
      }
    }

    return new Response(JSON.stringify(health), {
      headers: { 'Content-Type': 'application/json' }
    });
  }

  async handleTaskExecution(request) {
    if (request.method !== 'POST') {
      return new Response('Method Not Allowed', { status: 405 });
    }

    const task = await request.json();
    const result = await this.multiAgentSystem.execute_task(task);

    return new Response(JSON.stringify(result), {
      headers: { 'Content-Type': 'application/json' }
    });
  }

  async handleSystemStatus() {
    const status = {
      uptime: this.multiAgentSystem?.uptime || 0,
      active_tasks: this.multiAgentSystem?.orchestrator?.task_queue?.length || 0,
      agents_status: {},
      last_update: new Date().toISOString()
    };

    if (this.multiAgentSystem) {
      for (const [agentType, agent] of Object.entries(this.multiAgentSystem.agents)) {
        status.agents_status[agentType] = {
          status: await agent.health_check() ? 'healthy' : 'unhealthy',
          tasks_completed: agent.tasks_completed || 0
        };
      }
    }

    return new Response(JSON.stringify(status), {
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// Durable Object for Content Pipeline
export class ContentPipeline {
  constructor(state, env) {
    this.state = state;
    this.env = env;
  }

  async fetch(request) {
    const url = new URL(request.url);
    
    switch (url.pathname) {
      case '/discover':
        return await this.handleContentDiscovery(request);
      
      case '/analyze':
        return await this.handleContentAnalysis(request);
      
      case '/curate':
        return await this.handleContentCuration(request);
      
      case '/generate':
        return await this.handleNewsletterGeneration(request);
      
      default:
        return new Response('Not Found', { status: 404 });
    }
  }

  async handleContentDiscovery(request) {
    // Trigger Scout Agent for content discovery
    const orchestratorId = this.env.AGENT_ORCHESTRATOR.idFromName('main');
    const orchestrator = this.env.AGENT_ORCHESTRATOR.get(orchestratorId);
    
    const task = {
      task_id: `discovery-${Date.now()}`,
      agent_type: 'scout',
      priority: 'HIGH',
      data: { type: 'comprehensive_discovery' },
      created_at: new Date().toISOString()
    };

    return await orchestrator.fetch(new Request('http://localhost/task', {
      method: 'POST',
      body: JSON.stringify(task)
    }));
  }

  async handleContentAnalysis(request) {
    // Trigger Curator Agent for content analysis
    const orchestratorId = this.env.AGENT_ORCHESTRATOR.idFromName('main');
    const orchestrator = this.env.AGENT_ORCHESTRATOR.get(orchestratorId);
    
    const task = {
      task_id: `analysis-${Date.now()}`,
      agent_type: 'curator',
      priority: 'MEDIUM',
      data: { type: 'bulk_analysis' },
      created_at: new Date().toISOString()
    };

    return await orchestrator.fetch(new Request('http://localhost/task', {
      method: 'POST',
      body: JSON.stringify(task)
    }));
  }

  async handleContentCuration(request) {
    // Manual content curation override
    const body = await request.json();
    
    const orchestratorId = this.env.AGENT_ORCHESTRATOR.idFromName('main');
    const orchestrator = this.env.AGENT_ORCHESTRATOR.get(orchestratorId);
    
    const task = {
      task_id: `curation-${Date.now()}`,
      agent_type: 'curator',
      priority: 'HIGH',
      data: { 
        type: 'manual_curation',
        selections: body.selections || {}
      },
      created_at: new Date().toISOString()
    };

    return await orchestrator.fetch(new Request('http://localhost/task', {
      method: 'POST',
      body: JSON.stringify(task)
    }));
  }

  async handleNewsletterGeneration(request) {
    // Trigger Writer Agent for newsletter generation
    const orchestratorId = this.env.AGENT_ORCHESTRATOR.idFromName('main');
    const orchestrator = this.env.AGENT_ORCHESTRATOR.get(orchestratorId);
    
    const task = {
      task_id: `newsletter-${Date.now()}`,
      agent_type: 'writer',
      priority: 'HIGH',
      data: { type: 'generate_newsletter' },
      created_at: new Date().toISOString()
    };

    const response = await orchestrator.fetch(new Request('http://localhost/task', {
      method: 'POST',
      body: JSON.stringify(task)
    }));

    // Store newsletter in R2 if generation successful
    const result = await response.json();
    if (result.status === 'success' && result.newsletter) {
      await this.env.NEWSLETTER_STORAGE.put(
        `newsletters/${task.task_id}.html`,
        result.newsletter.html_content,
        {
          httpMetadata: {
            contentType: 'text/html',
          },
          customMetadata: {
            title: result.newsletter.title,
            generated_at: new Date().toISOString()
          }
        }
      );
    }

    return response;
  }
}

// Main Worker fetch handler
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    };

    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    try {
      // Route requests to appropriate handlers
      if (url.pathname.startsWith('/api/mcp')) {
        return await handleMCPRequest(request, env);
      } else if (url.pathname.startsWith('/api/agents')) {
        return await handleAgentRequest(request, env);
      } else if (url.pathname.startsWith('/api/content')) {
        return await handleContentRequest(request, env);
      } else if (url.pathname.startsWith('/webhook')) {
        return await handleWebhook(request, env);
      } else if (url.pathname === '/health') {
        return await handleGlobalHealth(env);
      } else {
        return new Response('Not Found', { status: 404 });
      }
    } catch (error) {
      console.error('Global worker error:', error);
      return new Response(JSON.stringify({ error: error.message }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
  },

  // Scheduled event handler
  async scheduled(event, env, ctx) {
    switch (event.cron) {
      case '0 */6 * * *': // Every 6 hours
        await triggerContentDiscovery(env);
        break;
      
      case '0 8 * * 1': // Monday 8 AM
        await triggerNewsletterGeneration(env);
        break;
    }
  },

  // Queue consumer
  async queue(batch, env) {
    for (const message of batch.messages) {
      try {
        await processQueueMessage(message, env);
        message.ack();
      } catch (error) {
        console.error('Queue processing error:', error);
        message.retry();
      }
    }
  }
};

// Helper functions
async function handleMCPRequest(request, env) {
  const orchestratorId = env.AGENT_ORCHESTRATOR.idFromName('main');
  const orchestrator = env.AGENT_ORCHESTRATOR.get(orchestratorId);
  
  return await orchestrator.fetch(request);
}

async function handleAgentRequest(request, env) {
  const url = new URL(request.url);
  const agentType = url.pathname.split('/')[3];
  
  const orchestratorId = env.AGENT_ORCHESTRATOR.idFromName('main');
  const orchestrator = env.AGENT_ORCHESTRATOR.get(orchestratorId);
  
  return await orchestrator.fetch(request);
}

async function handleContentRequest(request, env) {
  const pipelineId = env.CONTENT_PIPELINE.idFromName('main');
  const pipeline = env.CONTENT_PIPELINE.get(pipelineId);
  
  return await pipeline.fetch(request);
}

async function handleWebhook(request, env) {
  // Verify webhook signature
  const signature = request.headers.get('X-Signature');
  if (!verifyWebhookSignature(request, signature, env.WEBHOOK_SECRET)) {
    return new Response('Unauthorized', { status: 401 });
  }

  const payload = await request.json();
  
  // Process webhook event
  await env.CONTENT_QUEUE.send(payload);
  
  return new Response('OK');
}

async function handleGlobalHealth(env) {
  const health = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    services: {
      orchestrator: 'unknown',
      pipeline: 'unknown'
    }
  };

  try {
    const orchestratorId = env.AGENT_ORCHESTRATOR.idFromName('main');
    const orchestrator = env.AGENT_ORCHESTRATOR.get(orchestratorId);
    const orchResponse = await orchestrator.fetch(new Request('http://localhost/health'));
    health.services.orchestrator = orchResponse.ok ? 'healthy' : 'unhealthy';
  } catch (e) {
    health.services.orchestrator = 'error';
  }

  try {
    const pipelineId = env.CONTENT_PIPELINE.idFromName('main');
    const pipeline = env.CONTENT_PIPELINE.get(pipelineId);
    const pipeResponse = await pipeline.fetch(new Request('http://localhost/health'));
    health.services.pipeline = pipeResponse.ok ? 'healthy' : 'unhealthy';
  } catch (e) {
    health.services.pipeline = 'error';
  }

  return new Response(JSON.stringify(health), {
    headers: { 'Content-Type': 'application/json' }
  });
}

async function triggerContentDiscovery(env) {
  const pipelineId = env.CONTENT_PIPELINE.idFromName('main');
  const pipeline = env.CONTENT_PIPELINE.get(pipelineId);
  
  await pipeline.fetch(new Request('http://localhost/discover', { method: 'POST' }));
}

async function triggerNewsletterGeneration(env) {
  const pipelineId = env.CONTENT_PIPELINE.idFromName('main');
  const pipeline = env.CONTENT_PIPELINE.get(pipelineId);
  
  await pipeline.fetch(new Request('http://localhost/generate', { method: 'POST' }));
}

async function processQueueMessage(message, env) {
  const payload = message.body;
  
  // Route message based on type
  switch (payload.type) {
    case 'content_discovered':
      await handleContentDiscovered(payload, env);
      break;
    
    case 'content_analyzed':
      await handleContentAnalyzed(payload, env);
      break;
    
    case 'newsletter_generated':
      await handleNewsletterGenerated(payload, env);
      break;
    
    default:
      console.warn('Unknown message type:', payload.type);
  }
}

async function handleContentDiscovered(payload, env) {
  // Store content in KV cache
  await env.CONTENT_CACHE.put(
    `content:${payload.content_id}`,
    JSON.stringify(payload.content),
    { expirationTtl: 86400 } // 24 hours
  );
}

async function handleContentAnalyzed(payload, env) {
  // Update content analysis in cache
  const existing = await env.CONTENT_CACHE.get(`content:${payload.content_id}`, 'json');
  if (existing) {
    existing.analysis = payload.analysis;
    await env.CONTENT_CACHE.put(
      `content:${payload.content_id}`,
      JSON.stringify(existing),
      { expirationTtl: 86400 }
    );
  }
}

async function handleNewsletterGenerated(payload, env) {
  // Store newsletter analytics
  await env.ANALYTICS_CACHE.put(
    `newsletter:${payload.newsletter_id}`,
    JSON.stringify({
      id: payload.newsletter_id,
      generated_at: payload.timestamp,
      content_count: payload.content_count,
      quality_score: payload.quality_score
    }),
    { expirationTtl: 2592000 } // 30 days
  );
}

function verifyWebhookSignature(request, signature, secret) {
  // Implement webhook signature verification
  // This is a placeholder - implement actual signature verification
  return signature && secret;
}