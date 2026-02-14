#!/bin/bash
# skills.sh - One-Command Deployment for AutoPMO
# Usage: ./skills.sh [demo|cluster|dev|test|reset]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ASCII Art Logo
print_logo() {
    echo -e "${BLUE}"
    cat << "EOF"
    ___        __       ____  __  _______
   /   | __  __/ /_____/ __ \/  |/  / __ \
  / /| |/ / / / __/ __ / /_/ / /|_/ / / / /
 / ___ / /_/ / /_/ /_/ / ____/ /  / / /_/ /
/_/  |_\__,_/\__/\____/_/   /_/  /_/\____/

AI-Powered Project Management Office
EOF
    echo -e "${NC}"
}

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_deps=()
    
    # Check for required commands
    command -v python3 >/dev/null 2>&1 || missing_deps+=("python3")
    command -v pip3 >/dev/null 2>&1 || missing_deps+=("pip3")
    command -v git >/dev/null 2>&1 || missing_deps+=("git")
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        log_info "Please install missing dependencies and try again."
        exit 1
    fi
    
    log_success "All prerequisites met"
}

# Demo mode - Docker Compose
deploy_demo() {
    log_info "Starting AutoPMO in Demo Mode (Docker Compose)..."
    
    # Check for docker/podman
    if command -v docker >/dev/null 2>&1; then
        CONTAINER_CMD="docker"
    elif command -v podman >/dev/null 2>&1; then
        CONTAINER_CMD="podman"
    else
        log_error "Docker or Podman is required for demo mode"
        exit 1
    fi
    
    log_info "Using container runtime: $CONTAINER_CMD"
    
    # Create docker-compose if not exists
    if [ ! -f "docker-compose.yaml" ]; then
        log_info "Generating docker-compose.yaml..."
        cat > docker-compose.yaml <<EOF
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: autopmo
      POSTGRES_USER: autopmo
      POSTGRES_PASSWORD: autopmo_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U autopmo"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: autopmo
      MINIO_ROOT_PASSWORD: autopmo_password
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://autopmo:autopmo_password@postgres:5432/autopmo
      - REDIS_URL=redis://redis:6379/0
      - MINIO_ENDPOINT=minio:9000
      - LOG_LEVEL=INFO
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./api:/app
      - ./agents:/app/agents
      - ./models:/app/models

  dashboard:
    build:
      context: ./dashboard
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    depends_on:
      - api

volumes:
  postgres_data:
  redis_data:
  minio_data:
EOF
    fi
    
    # Start services
    log_info "Starting services..."
    $CONTAINER_CMD-compose up -d
    
    # Wait for services
    log_info "Waiting for services to be healthy..."
    sleep 10
    
    # Initialize database
    log_info "Initializing database..."
    python3 scripts/init-database.py
    
    # Load demo data
    log_info "Loading demo data..."
    python3 scripts/generate-sample-data.py
    
    log_success "Demo deployment complete!"
    echo ""
    log_info "Access AutoPMO at:"
    echo -e "${GREEN}  🌐 Dashboard: http://localhost:3000${NC}"
    echo -e "${GREEN}  📡 API: http://localhost:8000${NC}"
    echo -e "${GREEN}  📊 MinIO Console: http://localhost:9001${NC}"
    echo ""
    log_info "Default credentials:"
    echo -e "${YELLOW}  Username: demo-pm${NC}"
    echo -e "${YELLOW}  Password: AutoPMO2024!${NC}"
    echo ""
    log_info "To stop: $CONTAINER_CMD-compose down"
}

# OpenShift Cluster deployment
deploy_cluster() {
    log_info "Deploying to OpenShift Cluster..."
    
    # Check for oc command
    if ! command -v oc >/dev/null 2>&1; then
        log_error "OpenShift CLI (oc) is required"
        log_info "Install from: https://mirror.openshift.com/pub/openshift-v4/clients/ocp/"
        exit 1
    fi
    
    # Check if logged in
    if ! oc whoami &> /dev/null; then
        log_error "Not logged into OpenShift cluster"
        log_info "Please run: oc login <cluster-url>"
        exit 1
    fi
    
    # Get cluster info
    log_info "Connected to: $(oc cluster-info | grep 'Kubernetes' | awk '{print $NF}')"
    
    # Prompt for namespace
    read -p "Enter namespace name (default: autopmo): " NAMESPACE
    NAMESPACE=${NAMESPACE:-autopmo}
    
    # Create namespace
    log_info "Creating namespace: $NAMESPACE"
    oc new-project $NAMESPACE || oc project $NAMESPACE
    
    # Install operators
    log_info "Installing required operators..."
    log_warning "This may take 5-10 minutes..."
    
    # OpenShift AI Operator
    log_info "Installing OpenShift AI Operator..."
    oc apply -f openshift/operators/openshift-ai-operator.yaml
    
    # Wait for operator
    log_info "Waiting for operator installation..."
    sleep 30
    
    # Deploy base resources
    log_info "Deploying base resources..."
    oc apply -f openshift/base/
    
    # Deploy storage
    log_info "Creating persistent storage..."
    oc apply -f openshift/storage/
    
    # Deploy databases
    log_info "Deploying databases..."
    oc apply -f openshift/databases/
    
    # Wait for databases
    log_info "Waiting for databases to be ready..."
    oc wait --for=condition=Ready pod -l app=postgresql --timeout=300s
    oc wait --for=condition=Ready pod -l app=redis --timeout=300s
    
    # Initialize database
    log_info "Initializing database..."
    oc run --rm -i --restart=Never init-db --image=python:3.11-slim \
        --command -- python3 /scripts/init-database.py
    
    # Deploy security
    log_info "Configuring security..."
    oc apply -f openshift/security/
    
    # Deploy ML models
    log_info "Deploying ML models..."
    oc apply -f openshift/models/
    
    # Deploy agents
    log_info "Deploying AI agents..."
    oc apply -f openshift/agents/
    
    # Deploy API
    log_info "Deploying API..."
    oc apply -f openshift/api/
    
    # Deploy dashboard
    log_info "Deploying dashboard..."
    oc apply -f openshift/dashboard/
    
    # Create routes
    log_info "Creating routes..."
    DASHBOARD_ROUTE=$(oc get route autopmo-dashboard -o jsonpath='{.spec.host}')
    API_ROUTE=$(oc get route autopmo-api -o jsonpath='{.spec.host}')
    
    # Setup monitoring
    log_info "Configuring monitoring..."
    oc apply -f openshift/monitoring/
    
    log_success "Cluster deployment complete!"
    echo ""
    log_info "Access AutoPMO at:"
    echo -e "${GREEN}  🌐 Dashboard: https://$DASHBOARD_ROUTE${NC}"
    echo -e "${GREEN}  📡 API: https://$API_ROUTE${NC}"
    echo ""
    log_info "Default credentials:"
    echo -e "${YELLOW}  Username: admin${NC}"
    echo -e "${YELLOW}  Password: (check Red Hat SSO)${NC}"
}

# Development mode
deploy_dev() {
    log_info "Setting up development environment..."
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    log_info "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    
    # Install pre-commit hooks
    if [ -f ".pre-commit-config.yaml" ]; then
        log_info "Installing pre-commit hooks..."
        pre-commit install
    fi
    
    # Start local databases
    log_info "Starting local databases..."
    if command -v docker >/dev/null 2>&1; then
        docker run -d --name autopmo-postgres \
            -e POSTGRES_PASSWORD=dev_password \
            -e POSTGRES_DB=autopmo \
            -p 5432:5432 \
            postgres:15-alpine
        
        docker run -d --name autopmo-redis \
            -p 6379:6379 \
            redis:7-alpine
    fi
    
    # Initialize database
    log_info "Initializing database..."
    python scripts/init-database.py
    
    # Load sample data
    log_info "Loading sample data..."
    python scripts/generate-sample-data.py
    
    log_success "Development environment ready!"
    echo ""
    log_info "To activate virtual environment:"
    echo -e "${YELLOW}  source venv/bin/activate${NC}"
    echo ""
    log_info "To start API server:"
    echo -e "${YELLOW}  cd api && uvicorn main:app --reload${NC}"
    echo ""
    log_info "To start dashboard:"
    echo -e "${YELLOW}  cd dashboard && npm install && npm run dev${NC}"
}

# Run tests
run_tests() {
    log_info "Running test suite..."
    
    # Activate virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Run tests
    log_info "Running unit tests..."
    pytest tests/unit -v --cov=agents --cov=api --cov-report=html
    
    log_info "Running integration tests..."
    pytest tests/integration -v
    
    log_success "All tests passed!"
    log_info "Coverage report: htmlcov/index.html"
}

# Reset/cleanup
reset_demo() {
    log_warning "This will delete all AutoPMO data!"
    read -p "Are you sure? (yes/no): " confirmation
    
    if [ "$confirmation" != "yes" ]; then
        log_info "Reset cancelled"
        exit 0
    fi
    
    log_info "Stopping services..."
    
    if command -v docker-compose >/dev/null 2>&1; then
        docker-compose down -v
    elif command -v podman-compose >/dev/null 2>&1; then
        podman-compose down -v
    fi
    
    # Remove local data
    rm -rf postgres_data redis_data minio_data
    
    log_success "Reset complete!"
}

# Main menu
show_menu() {
    echo ""
    log_info "AutoPMO Deployment Options:"
    echo ""
    echo "1. Demo Mode (Docker Compose - Quick Start)"
    echo "2. OpenShift Cluster Deployment (Production)"
    echo "3. Development Environment Setup"
    echo "4. Run Tests"
    echo "5. Reset/Cleanup"
    echo "6. Exit"
    echo ""
    read -p "Select option [1-6]: " choice
    
    case $choice in
        1) deploy_demo ;;
        2) deploy_cluster ;;
        3) deploy_dev ;;
        4) run_tests ;;
        5) reset_demo ;;
        6) exit 0 ;;
        *) log_error "Invalid option"; show_menu ;;
    esac
}

# Main execution
main() {
    print_logo
    
    log_info "AutoPMO Deployment Script v1.0"
    log_info "===============================

"
    
    check_prerequisites
    
    # Parse command line argument
    if [ $# -eq 0 ]; then
        show_menu
    else
        case $1 in
            demo) deploy_demo ;;
            cluster) deploy_cluster ;;
            dev) deploy_dev ;;
            test) run_tests ;;
            reset) reset_demo ;;
            *)
                log_error "Unknown command: $1"
                echo "Usage: ./skills.sh [demo|cluster|dev|test|reset]"
                exit 1
                ;;
        esac
    fi
}

# Run main function
main "$@"
