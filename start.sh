#!/bin/bash

# Face Recognition System Startup Script
# This script helps deploy and initialize the system

set -e

echo "🚀 Starting Face Recognition System Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if Docker and Docker Compose are installed
check_dependencies() {
    print_status "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Dependencies check passed!"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p backend/known_faces
    mkdir -p backend/uploads
    mkdir -p backend/logs
    mkdir -p nginx/logs
    mkdir -p nginx/ssl
    
    print_success "Directories created!"
}

# Setup environment file
setup_environment() {
    if [ ! -f .env ]; then
        print_status "Creating environment file from template..."
        cp .env.example .env
        print_warning "Please edit .env file with your configuration before continuing!"
        print_warning "Especially change the JWT_SECRET_KEY for production!"
        
        read -p "Press [Enter] to continue after editing .env file..."
    else
        print_status "Environment file already exists."
    fi
}

# Build and start services
start_services() {
    print_status "Building and starting services..."
    
    # Pull latest images
    docker-compose pull postgres redis nginx
    
    # Build and start services
    docker-compose up -d --build
    
    print_success "Services started!"
}

# Wait for services to be healthy
wait_for_services() {
    print_status "Waiting for services to be ready..."
    
    # Wait for database
    echo -n "Waiting for database"
    while ! docker-compose exec -T postgres pg_isready -U postgres &>/dev/null; do
        echo -n "."
        sleep 2
    done
    echo ""
    print_success "Database is ready!"
    
    # Wait for backend
    echo -n "Waiting for backend"
    while ! curl -s http://localhost:8000/health &>/dev/null; do
        echo -n "."
        sleep 2
    done
    echo ""
    print_success "Backend is ready!"
    
    # Wait for frontend through nginx
    echo -n "Waiting for frontend"
    while ! curl -s http://localhost/ &>/dev/null; do
        echo -n "."
        sleep 2
    done
    echo ""
    print_success "Frontend is ready!"
}

# Create initial admin user
create_admin_user() {
    print_status "Creating initial admin user..."
    
    # Check if admin already exists
    if docker-compose exec -T backend python -c "
from app.database import get_db
from app.models import User
db = next(get_db())
admin = db.query(User).filter(User.employee_id == 'admin').first()
exit(0 if admin else 1)
" 2>/dev/null; then
        print_warning "Admin user already exists!"
        return
    fi
    
    # Create admin user
    docker-compose exec -T backend python -c "
from app.auth import hash_password
from app.database import get_db
from app.models import User

try:
    db = next(get_db())
    admin = User(
        employee_id='admin',
        name='System Administrator',
        email='admin@company.com',
        role='super_admin',
        password_hash=hash_password('admin123'),
        is_active=True
    )
    db.add(admin)
    db.commit()
    print('✅ Admin user created successfully!')
    print('   Employee ID: admin')
    print('   Password: admin123')
    print('   ⚠️  PLEASE CHANGE THE DEFAULT PASSWORD!')
except Exception as e:
    print(f'❌ Error creating admin user: {e}')
    exit(1)
"
    
    print_success "Initial admin user created!"
}

# Display final information
show_completion_info() {
    print_success "🎉 Face Recognition System is now running!"
    echo ""
    echo "📍 Access Points:"
    echo "   Frontend:  http://localhost"
    echo "   Backend:   http://localhost/api"
    echo "   API Docs:  http://localhost/docs"
    echo ""
    echo "👤 Default Admin Credentials:"
    echo "   Employee ID: admin"
    echo "   Password:    admin123"
    echo ""
    echo "⚠️  Important Security Notes:"
    echo "   1. Change the default admin password immediately"
    echo "   2. Update JWT_SECRET_KEY in .env for production"
    echo "   3. Configure SSL certificates for HTTPS"
    echo "   4. Review and update other security settings"
    echo ""
    echo "📊 Service Status:"
    docker-compose ps
    echo ""
    echo "📝 View logs with: docker-compose logs -f [service_name]"
    echo "🛑 Stop system with: docker-compose down"
    echo ""
    print_success "Deployment completed successfully! 🚀"
}

# Show help
show_help() {
    echo "Face Recognition System Startup Script"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  start     Start the complete system (default)"
    echo "  stop      Stop all services"
    echo "  restart   Restart all services"
    echo "  logs      Show logs from all services"
    echo "  status    Show status of all services"
    echo "  clean     Stop and remove all containers and volumes"
    echo "  help      Show this help message"
    echo ""
}

# Main execution
case "${1:-start}" in
    "start")
        check_dependencies
        create_directories
        setup_environment
        start_services
        wait_for_services
        create_admin_user
        show_completion_info
        ;;
    "stop")
        print_status "Stopping services..."
        docker-compose down
        print_success "Services stopped!"
        ;;
    "restart")
        print_status "Restarting services..."
        docker-compose down
        docker-compose up -d
        print_success "Services restarted!"
        ;;
    "logs")
        docker-compose logs -f
        ;;
    "status")
        docker-compose ps
        ;;
    "clean")
        print_warning "This will remove all containers, volumes, and data!"
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_status "Cleaning up..."
            docker-compose down -v --remove-orphans
            docker system prune -f
            print_success "Cleanup completed!"
        else
            print_status "Cleanup cancelled."
        fi
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    *)
        print_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac