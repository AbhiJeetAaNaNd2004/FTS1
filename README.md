# Face Recognition System

A comprehensive role-based single-page web application for on-premise face recognition system with real-time detection, tracking, and attendance management.

## 🎯 System Overview

This system provides a complete face recognition solution with:

- **JWT-based Authentication** with role-based access control
- **Real-time Face Detection & Recognition** using InsightFace
- **Employee Management** with enrollment and lifecycle management
- **Live Video Feed Processing** with face tracking
- **Attendance Logging** with check-in/check-out events
- **Modern Web Interface** with React and Tailwind CSS
- **Scalable Architecture** with Docker containerization

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React SPA     │────│   Nginx Proxy   │────│   FastAPI       │
│   (Frontend)    │    │   (Load Balancer)│    │   (Backend)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   PostgreSQL    │    │     Redis       │
                       │   (Database)    │    │   (Caching)     │
                       └─────────────────┘    └─────────────────┘
```

## 👥 User Roles

### Employee
- View personal dashboard with attendance logs
- View personal face enrollment status
- Change password

### Admin
- All employee permissions
- Create, read, update employee records
- Manage face enrollments for all employees
- View all attendance logs
- Access live camera feeds
- Manage camera configurations

### Super Admin
- All admin permissions
- Create, update, delete admin accounts
- System-wide configuration
- Full user lifecycle management

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- 8GB+ RAM (for face recognition models)
- NVIDIA GPU (optional, for better performance)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd face-recognition-system
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the system**
   ```bash
   docker-compose up -d
   ```

4. **Create initial super admin**
   ```bash
   docker-compose exec backend python -c "
   from app.auth import hash_password
   from app.database import get_db
   from app.models import User
   
   db = next(get_db())
   admin = User(
       employee_id='admin',
       name='System Administrator',
       email='admin@company.com',
       role='super_admin',
       password_hash=hash_password('admin123')
   )
   db.add(admin)
   db.commit()
   print('Admin created: admin / admin123')
   "
   ```

5. **Access the application**
   - Frontend: http://localhost
   - Backend API: http://localhost/api
   - API Documentation: http://localhost/docs

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Database
DB_HOST=postgres
DB_NAME=face_tracking
DB_USER=postgres
DB_PASSWORD=your-secure-password

# JWT Security
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Face Recognition
FACE_DETECTION_THRESHOLD=0.5
FACE_MATCH_THRESHOLD=0.6
EMBEDDING_MODEL=antelopev2

# Server
WORKERS=4
LOG_LEVEL=INFO
```

### Database Schema

The system uses PostgreSQL with the following main tables:

- `users` - Employee accounts and authentication
- `faces` - Face images and embeddings
- `logs` - Attendance check-in/check-out events
- `cameras` - Camera configuration and management

### Face Recognition Models

The system uses InsightFace with the AnteLope v2 model:
- **Detection**: RetinaFace
- **Recognition**: ArcFace
- **Embedding Size**: 512 dimensions

## 📱 Frontend Features

### Modern UI Components
- Responsive design with Tailwind CSS
- Role-based navigation
- Real-time notifications
- Dark/light theme support
- File upload with progress
- Data tables with pagination and search

### Key Pages
- **Dashboard**: Overview with statistics and recent activity
- **Users**: Employee management with CRUD operations
- **Faces**: Face enrollment and management
- **Logs**: Attendance tracking and reporting
- **Cameras**: Live feed viewing and camera management
- **Profile**: Personal settings and password change

## 🔌 Backend API

### Authentication Endpoints
```
POST /api/auth/login          # User authentication
POST /api/auth/logout         # User logout
POST /api/auth/refresh        # Token refresh
GET  /api/auth/me            # Current user profile
POST /api/auth/change-password # Password change
GET  /api/auth/permissions   # User permissions
```

### User Management
```
GET    /api/users/           # List users (paginated)
POST   /api/users/           # Create user
GET    /api/users/{id}       # Get user details
PUT    /api/users/{id}       # Update user
DELETE /api/users/{id}       # Delete user
GET    /api/users/{id}/summary # User statistics
```

### Face Management
```
GET    /api/faces/user/{id}  # Get user faces
POST   /api/faces/enroll/{id} # Enroll face
DELETE /api/faces/{id}       # Delete face
GET    /api/faces/{id}/image # Get face image
POST   /api/faces/detect     # Detect faces in image
```

### Attendance Logs
```
GET  /api/logs/              # List logs (paginated)
POST /api/logs/              # Create log entry
GET  /api/logs/user/{id}     # User-specific logs
GET  /api/logs/attendance-report # Attendance report
GET  /api/logs/presence-status   # Current presence status
```

## 🛡️ Security

### Authentication & Authorization
- JWT tokens with configurable expiration
- Role-based access control (RBAC)
- Password hashing with bcrypt
- Rate limiting on sensitive endpoints
- CORS protection

### Data Protection
- Input validation with Pydantic
- SQL injection prevention with ORM
- File upload validation
- Secure headers with Nginx
- Optional TLS/SSL encryption

### Face Data Security
- Encrypted embedding storage
- Access logging for face operations
- Role-based face data access
- Secure file handling

## 📊 Monitoring & Logging

### Application Logging
- Structured logging with configurable levels
- Request/response logging
- Error tracking and alerting
- Performance metrics

### Health Checks
```bash
# Check system health
curl http://localhost/health

# Check individual services
docker-compose ps
docker-compose logs backend
```

### Database Monitoring
```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Check table sizes
SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size 
FROM pg_tables WHERE schemaname='public';
```

## 🔄 Development

### Local Development Setup

1. **Backend Development**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

2. **Frontend Development**
   ```bash
   cd frontend
   npm install
   npm start
   ```

### Code Quality
- Backend: Black, isort, mypy
- Frontend: ESLint, Prettier
- Pre-commit hooks available

### Testing
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📈 Performance Optimization

### Face Recognition
- GPU acceleration with CUDA
- Model caching and preloading
- Batch processing for multiple faces
- Quality-based filtering

### Database
- Indexed columns for fast queries
- Connection pooling
- Query optimization
- Periodic maintenance

### Caching
- Redis for session storage
- API response caching
- Static asset caching with Nginx

## 🚀 Production Deployment

### Hardware Requirements
- **CPU**: 8+ cores (Intel/AMD)
- **RAM**: 16GB+ (32GB recommended)
- **Storage**: 500GB+ SSD
- **GPU**: NVIDIA GTX 1060+ (optional)
- **Network**: Gigabit Ethernet

### Scaling Considerations
- **Horizontal**: Multiple backend instances
- **Vertical**: GPU acceleration for face processing
- **Database**: Read replicas for reporting
- **Caching**: Redis cluster for high availability

### Backup Strategy
```bash
# Database backup
docker-compose exec postgres pg_dump -U postgres face_tracking > backup.sql

# Face images backup
tar -czf faces_backup.tar.gz backend/known_faces/

# Full system backup
docker-compose down
tar -czf system_backup.tar.gz .
```

## 🛠️ Troubleshooting

### Common Issues

1. **Face recognition not working**
   ```bash
   # Check if InsightFace is properly installed
   docker-compose exec backend python -c "from insightface.app import FaceAnalysis; print('OK')"
   ```

2. **Database connection errors**
   ```bash
   # Check database status
   docker-compose exec postgres pg_isready -U postgres
   ```

3. **Frontend not loading**
   ```bash
   # Check nginx configuration
   docker-compose exec nginx nginx -t
   ```

### Log Analysis
```bash
# View real-time logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f nginx

# Check specific service
docker-compose logs backend | grep ERROR
```

## 📝 API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost/docs
- **ReDoc**: http://localhost/redoc

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For technical support:
1. Check the troubleshooting section
2. Review logs for error messages
3. Check GitHub issues
4. Contact system administrators

## 🔮 Roadmap

- [ ] Mobile application
- [ ] Advanced analytics and reporting
- [ ] Integration with external systems
- [ ] Multi-language support
- [ ] Enhanced security features
- [ ] Performance optimizations

---

**Built with ❤️ for secure and efficient face recognition**