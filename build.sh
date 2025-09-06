#!/bin/bash

# Inbound Carrier Sales AI - Build and Deploy Script
# This script builds, tests, and deploys the application to both GitHub and Heroku

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if git is clean
check_git_status() {
    print_status "Checking git status..."
    
    if [ -n "$(git status --porcelain)" ]; then
        print_warning "Working directory is not clean. Staging all changes..."
        git add .
    else
        print_success "Working directory is clean"
    fi
}

# Run tests if they exist
run_tests() {
    print_status "Running tests..."
    
    if [ -f "requirements.txt" ] && grep -q "pytest" requirements.txt; then
        if command -v pytest &> /dev/null; then
            pytest || {
                print_error "Tests failed!"
                exit 1
            }
            print_success "All tests passed"
        else
            print_warning "pytest not installed, skipping tests"
        fi
    else
        print_warning "No tests found, skipping test execution"
    fi
}

# Build Docker image
build_docker() {
    print_status "Building Docker image..."
    
    if command -v docker &> /dev/null; then
        docker build -t inbound-carrier-sales-api . || {
            print_error "Docker build failed!"
            exit 1
        }
        print_success "Docker image built successfully"
    else
        print_warning "Docker not installed, skipping Docker build"
    fi
}

# Test Docker container
test_docker() {
    print_status "Testing Docker container..."
    
    if command -v docker &> /dev/null; then
        # Check if .env file exists
        if [ ! -f ".env" ]; then
            print_warning "No .env file found, creating sample .env for testing"
            cat > .env.test << EOF
API_SECRET_KEY=test-key-for-build-script
FMCSA_API_KEY=test-fmcsa-key
MONGODB_URI=mongodb://localhost:27017/test
DATABASE_NAME=test
LOADS_COLLECTION_NAME=loads
CARRIERS_CALLS_COLLECTION_NAME=carriers_calls
FLASK_ENV=production
PORT=5000
DEBUG=false
EOF
            ENV_FILE=".env.test"
        else
            ENV_FILE=".env"
        fi
        
        # Run container in background
        docker run -d --name test-container -p 5001:5000 --env-file $ENV_FILE inbound-carrier-sales-api || {
            print_error "Failed to start Docker container"
            exit 1
        }
        
        # Wait for container to start
        sleep 5
        
        # Test health endpoint
        if curl -f http://localhost:5001/health &> /dev/null; then
            print_success "Docker container is running and healthy"
        else
            print_warning "Health check failed, but container started"
        fi
        
        # Clean up
        docker stop test-container &> /dev/null || true
        docker rm test-container &> /dev/null || true
        [ -f ".env.test" ] && rm .env.test
    fi
}

# Commit changes
commit_changes() {
    print_status "Committing changes..."
    
    if [ -n "$(git status --porcelain)" ]; then
        # Get commit message from user or use default
        if [ -z "$1" ]; then
            echo -n "Enter commit message (or press Enter for default): "
            read commit_message
            if [ -z "$commit_message" ]; then
                commit_message="Update application - $(date '+%Y-%m-%d %H:%M')"
            fi
        else
            commit_message="$1"
        fi
        
        git commit -m "$commit_message

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
        print_success "Changes committed: $commit_message"
    else
        print_success "No changes to commit"
    fi
}

# Push to GitHub
push_to_github() {
    print_status "Pushing to GitHub..."
    
    # Check if origin remote exists
    if git remote | grep -q "^origin$"; then
        git push origin main || {
            print_error "Failed to push to GitHub"
            exit 1
        }
        print_success "Successfully pushed to GitHub"
    else
        print_warning "No 'origin' remote found, skipping GitHub push"
    fi
}

# Deploy to Heroku
deploy_to_heroku() {
    print_status "Deploying to Heroku..."
    
    # Check if heroku CLI is installed
    if ! command -v heroku &> /dev/null; then
        print_error "Heroku CLI not installed. Please install it first."
        exit 1
    fi
    
    # Check if heroku remote exists
    if git remote | grep -q "^heroku$"; then
        git push heroku main || {
            print_error "Failed to deploy to Heroku"
            exit 1
        }
        print_success "Successfully deployed to Heroku"
        
        # Run health check on Heroku
        print_status "Running health check on Heroku..."
        sleep 10  # Wait for deployment to complete
        
        # Get Heroku app URL
        HEROKU_URL=$(heroku apps:info --json | grep -o '"web_url":"[^"]*' | cut -d'"' -f4)
        if [ -n "$HEROKU_URL" ]; then
            if curl -f "${HEROKU_URL}health" &> /dev/null; then
                print_success "Heroku deployment is healthy: ${HEROKU_URL}"
            else
                print_warning "Health check failed on Heroku"
            fi
        fi
    else
        print_warning "No 'heroku' remote found, skipping Heroku deployment"
        print_status "To add Heroku remote: heroku git:remote -a your-app-name"
    fi
}

# Main execution
main() {
    echo -e "${BLUE}"
    echo "=================================================="
    echo "  Inbound Carrier Sales AI - Build & Deploy"
    echo "=================================================="
    echo -e "${NC}"
    
    # Parse command line arguments
    SKIP_TESTS=false
    SKIP_DOCKER=false
    SKIP_GITHUB=false
    SKIP_HEROKU=false
    COMMIT_MESSAGE=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --skip-docker)
                SKIP_DOCKER=true
                shift
                ;;
            --skip-github)
                SKIP_GITHUB=true
                shift
                ;;
            --skip-heroku)
                SKIP_HEROKU=true
                shift
                ;;
            --message)
                COMMIT_MESSAGE="$2"
                shift 2
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --skip-tests     Skip running tests"
                echo "  --skip-docker    Skip Docker build and test"
                echo "  --skip-github    Skip GitHub push"
                echo "  --skip-heroku    Skip Heroku deployment"
                echo "  --message MSG    Use custom commit message"
                echo "  --help          Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Execute build pipeline
    check_git_status
    
    if [ "$SKIP_TESTS" = false ]; then
        run_tests
    fi
    
    if [ "$SKIP_DOCKER" = false ]; then
        build_docker
        test_docker
    fi
    
    commit_changes "$COMMIT_MESSAGE"
    
    if [ "$SKIP_GITHUB" = false ]; then
        push_to_github
    fi
    
    if [ "$SKIP_HEROKU" = false ]; then
        deploy_to_heroku
    fi
    
    echo -e "${GREEN}"
    echo "=================================================="
    echo "  Build and deployment completed successfully!"
    echo "=================================================="
    echo -e "${NC}"
    
    # Show deployment URLs
    echo -e "${BLUE}Deployment URLs:${NC}"
    if [ "$SKIP_GITHUB" = false ]; then
        GITHUB_URL=$(git remote get-url origin 2>/dev/null | sed 's/\.git$//' | sed 's/git@github.com:/https:\/\/github.com\//')
        [ -n "$GITHUB_URL" ] && echo "📱 GitHub: $GITHUB_URL"
    fi
    if [ "$SKIP_HEROKU" = false ] && command -v heroku &> /dev/null; then
        HEROKU_URL=$(heroku apps:info --json 2>/dev/null | grep -o '"web_url":"[^"]*' | cut -d'"' -f4)
        [ -n "$HEROKU_URL" ] && echo "🚀 Heroku: $HEROKU_URL"
    fi
    echo "🐳 Docker: inbound-carrier-sales-api (local image)"
}

# Run main function with all arguments
main "$@"