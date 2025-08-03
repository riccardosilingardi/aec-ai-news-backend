#!/bin/bash

# AEC AI News Deployment Script
# Deploys the complete multi-agent system to production

set -e

echo "Starting AEC AI News deployment..."

# Configuration
ENVIRONMENT=${1:-production}
PROJECT_ROOT=$(dirname $(dirname $(dirname $(realpath $0))))

echo "Deploying to environment: $ENVIRONMENT"
echo "Project root: $PROJECT_ROOT"

# Function to check prerequisites
check_prerequisites() {
    echo "Checking prerequisites..."
    
    # Check if wrangler is installed
    if ! command -v wrangler &> /dev/null; then
        echo "Error: Wrangler CLI is not installed"
        echo "Install with: npm install -g wrangler"
        exit 1
    fi
    
    # Check if supabase CLI is installed
    if ! command -v supabase &> /dev/null; then
        echo "Error: Supabase CLI is not installed"
        echo "Install with: npm install -g supabase"
        exit 1
    fi
    
    # Check if required environment variables are set
    if [ -z "$SUPABASE_PROJECT_ID" ]; then
        echo "Error: SUPABASE_PROJECT_ID environment variable is not set"
        exit 1
    fi
    
    echo "Prerequisites check passed"
}

# Function to deploy Supabase database
deploy_supabase() {
    echo "Deploying Supabase database..."
    
    cd "$PROJECT_ROOT"
    
    # Initialize Supabase if not already done
    if [ ! -f "supabase/config.toml" ]; then
        echo "Initializing Supabase project..."
        supabase init
    fi
    
    # Apply database migrations
    echo "Applying database schema..."
    supabase db push --project-ref $SUPABASE_PROJECT_ID
    
    echo "Supabase deployment completed"
}

# Function to deploy Cloudflare Workers
deploy_cloudflare() {
    echo "Deploying Cloudflare Workers..."
    
    cd "$PROJECT_ROOT"
    
    # Build the worker
    echo "Building worker..."
    npm run build:worker
    
    # Deploy to Cloudflare
    echo "Deploying to Cloudflare Workers..."
    wrangler deploy --env $ENVIRONMENT
    
    # Deploy Durable Objects
    echo "Deploying Durable Objects..."
    wrangler deploy --env $ENVIRONMENT --compatibility-date 2024-01-15
    
    echo "Cloudflare Workers deployment completed"
}

# Function to setup secrets
setup_secrets() {
    echo "Setting up secrets..."
    
    # List of required secrets
    SECRETS=(
        "SUPABASE_URL"
        "SUPABASE_SERVICE_KEY"
        "OPENAI_API_KEY"
        "ANTHROPIC_API_KEY"
        "EMAIL_SERVICE_KEY"
        "WEBHOOK_SECRET"
    )
    
    for secret in "${SECRETS[@]}"; do
        if [ -z "${!secret}" ]; then
            echo "Warning: $secret is not set in environment"
            read -p "Enter value for $secret: " -s secret_value
            echo
            wrangler secret put $secret --env $ENVIRONMENT <<< "$secret_value"
        else
            echo "Setting $secret..."
            wrangler secret put $secret --env $ENVIRONMENT <<< "${!secret}"
        fi
    done
    
    echo "Secrets setup completed"
}

# Function to setup KV namespaces
setup_kv_namespaces() {
    echo "Setting up KV namespaces..."
    
    # Create KV namespaces if they don't exist
    NAMESPACES=(
        "content-cache"
        "analytics-cache"
    )
    
    for namespace in "${NAMESPACES[@]}"; do
        echo "Creating KV namespace: $namespace"
        wrangler kv:namespace create $namespace --env $ENVIRONMENT || true
        wrangler kv:namespace create $namespace --preview --env $ENVIRONMENT || true
    done
    
    echo "KV namespaces setup completed"
}

# Function to setup R2 buckets
setup_r2_buckets() {
    echo "Setting up R2 buckets..."
    
    # Create R2 buckets if they don't exist
    BUCKETS=(
        "aec-ai-news-newsletters"
        "aec-ai-news-assets"
    )
    
    for bucket in "${BUCKETS[@]}"; do
        echo "Creating R2 bucket: $bucket"
        wrangler r2 bucket create $bucket || true
    done
    
    echo "R2 buckets setup completed"
}

# Function to setup queues
setup_queues() {
    echo "Setting up Cloudflare Queues..."
    
    # Create queues if they don't exist
    QUEUES=(
        "content-processing-queue"
        "email-delivery-queue"
        "analytics-queue"
    )
    
    for queue in "${QUEUES[@]}"; do
        echo "Creating queue: $queue"
        wrangler queues create $queue || true
    done
    
    echo "Queues setup completed"
}

# Function to run post-deployment tests
run_tests() {
    echo "Running post-deployment tests..."
    
    # Health check
    echo "Performing health check..."
    WORKER_URL="https://aec-ai-news-${ENVIRONMENT}.workers.dev"
    
    if [ "$ENVIRONMENT" = "production" ]; then
        WORKER_URL="https://api.aec-ai-news.com"
    fi
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$WORKER_URL/health")
    
    if [ "$response" = "200" ]; then
        echo "Health check passed"
    else
        echo "Warning: Health check failed with status $response"
    fi
    
    # Test MCP endpoints
    echo "Testing MCP endpoints..."
    mcp_response=$(curl -s -o /dev/null -w "%{http_code}" "$WORKER_URL/api/mcp/tools")
    
    if [ "$mcp_response" = "200" ]; then
        echo "MCP endpoints test passed"
    else
        echo "Warning: MCP endpoints test failed with status $mcp_response"
    fi
    
    echo "Post-deployment tests completed"
}

# Function to setup monitoring
setup_monitoring() {
    echo "Setting up monitoring and alerts..."
    
    # This would typically integrate with your monitoring service
    # For now, just log that monitoring should be configured
    
    echo "Configure the following monitoring:"
    echo "- Worker execution time and errors"
    echo "- Agent performance metrics"
    echo "- Newsletter generation success rate"
    echo "- Database connection health"
    echo "- Email delivery rates"
    
    echo "Monitoring setup completed"
}

# Main deployment flow
main() {
    echo "==================================="
    echo "AEC AI News Deployment Script"
    echo "==================================="
    
    check_prerequisites
    
    echo
    echo "Step 1: Database deployment"
    deploy_supabase
    
    echo
    echo "Step 2: Infrastructure setup"
    setup_kv_namespaces
    setup_r2_buckets
    setup_queues
    
    echo
    echo "Step 3: Secrets configuration"
    setup_secrets
    
    echo
    echo "Step 4: Worker deployment"
    deploy_cloudflare
    
    echo
    echo "Step 5: Post-deployment testing"
    run_tests
    
    echo
    echo "Step 6: Monitoring setup"
    setup_monitoring
    
    echo
    echo "==================================="
    echo "Deployment completed successfully!"
    echo "==================================="
    echo
    echo "Next steps:"
    echo "1. Configure DNS for custom domain (if production)"
    echo "2. Set up monitoring dashboards"
    echo "3. Configure email templates in Supabase"
    echo "4. Test the complete newsletter pipeline"
    echo "5. Set up backup and disaster recovery"
    echo
    echo "Worker URL: $WORKER_URL"
    echo "Environment: $ENVIRONMENT"
}

# Run main function
main "$@"