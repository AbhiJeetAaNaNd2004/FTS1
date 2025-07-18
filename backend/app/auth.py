import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import logging

from .config import settings
from .database import get_db
from .models import User
from .schemas import UserRole

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token security
security = HTTPBearer()

# Token types
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


class AuthenticationError(Exception):
    """Custom authentication error"""
    pass


class AuthorizationError(Exception):
    """Custom authorization error"""
    pass


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": ACCESS_TOKEN_TYPE
    })
    
    try:
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating access token: {e}")
        raise AuthenticationError("Failed to create access token")


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": REFRESH_TOKEN_TYPE
    })
    
    try:
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating refresh token: {e}")
        raise AuthenticationError("Failed to create refresh token")


def verify_token(token: str, token_type: str = ACCESS_TOKEN_TYPE) -> Dict[str, Any]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        
        # Check token type
        if payload.get("type") != token_type:
            raise AuthenticationError("Invalid token type")
        
        # Check if token is expired
        exp = payload.get("exp")
        if exp is None:
            raise AuthenticationError("Token missing expiration")
        
        if datetime.utcnow() > datetime.fromtimestamp(exp):
            raise AuthenticationError("Token has expired")
        
        return payload
    
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.JWTError as e:
        logger.error(f"JWT decode error: {e}")
        raise AuthenticationError("Invalid token")


def authenticate_user(db: Session, employee_id: str, password: str) -> Optional[User]:
    """Authenticate a user with employee ID and password"""
    try:
        user = db.query(User).filter(
            User.employee_id == employee_id,
            User.is_active == True
        ).first()
        
        if not user:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        # Update last login time
        user.last_login_time = datetime.utcnow()
        db.commit()
        
        return user
    
    except Exception as e:
        logger.error(f"Error authenticating user {employee_id}: {e}")
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_token(credentials.credentials)
        employee_id: str = payload.get("sub")
        
        if employee_id is None:
            raise credentials_exception
        
    except AuthenticationError:
        raise credentials_exception
    
    user = db.query(User).filter(
        User.employee_id == employee_id,
        User.is_active == True
    ).first()
    
    if user is None:
        raise credentials_exception
    
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def require_role(allowed_roles: list[UserRole]):
    """Decorator to require specific roles for access"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if UserRole(current_user.role) not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    
    return role_checker


# Role-specific dependencies
def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Require admin or super_admin role"""
    if UserRole(current_user.role) not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


def require_super_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Require super_admin role"""
    if UserRole(current_user.role) != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin privileges required"
        )
    return current_user


def require_admin_or_self(employee_id: str):
    """Require admin role or accessing own data"""
    def permission_checker(current_user: User = Depends(get_current_active_user)) -> User:
        is_admin = UserRole(current_user.role) in [UserRole.ADMIN, UserRole.SUPER_ADMIN]
        is_self = current_user.employee_id == employee_id
        
        if not (is_admin or is_self):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    
    return permission_checker


def check_face_access_permission(employee_id: str, current_user: User) -> bool:
    """Check if user has permission to access face data for an employee"""
    # Admin and super admin can access all face data
    if UserRole(current_user.role) in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        return True
    
    # Employees can only access their own face data
    if current_user.employee_id == employee_id:
        return True
    
    return False


def check_log_access_permission(employee_id: str, current_user: User) -> bool:
    """Check if user has permission to access log data for an employee"""
    # Admin and super admin can access all logs
    if UserRole(current_user.role) in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        return True
    
    # Employees can only access their own logs
    if current_user.employee_id == employee_id:
        return True
    
    return False


def get_user_permissions(user: User) -> Dict[str, bool]:
    """Get user permissions based on role"""
    role = UserRole(user.role)
    
    permissions = {
        "can_view_all_users": False,
        "can_create_users": False,
        "can_update_users": False,
        "can_delete_users": False,
        "can_view_all_logs": False,
        "can_create_logs": False,
        "can_view_cameras": False,
        "can_manage_cameras": False,
        "can_view_live_feed": False,
        "can_enroll_faces": False,
        "can_delete_faces": False,
        "can_view_dashboard": False,
        "can_manage_system": False,
    }
    
    if role == UserRole.EMPLOYEE:
        permissions.update({
            "can_view_dashboard": True,
        })
    
    elif role == UserRole.ADMIN:
        permissions.update({
            "can_view_all_users": True,
            "can_create_users": True,
            "can_update_users": True,
            "can_view_all_logs": True,
            "can_create_logs": True,
            "can_view_cameras": True,
            "can_manage_cameras": True,
            "can_view_live_feed": True,
            "can_enroll_faces": True,
            "can_delete_faces": True,
            "can_view_dashboard": True,
        })
    
    elif role == UserRole.SUPER_ADMIN:
        # Super admin has all permissions
        permissions = {key: True for key in permissions}
    
    return permissions


class RateLimiter:
    """Simple in-memory rate limiter"""
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is allowed based on rate limit"""
        now = datetime.utcnow()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests outside the window
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if (now - req_time).total_seconds() < window
        ]
        
        # Check if under limit
        if len(self.requests[key]) < limit:
            self.requests[key].append(now)
            return True
        
        return False


# Global rate limiter instance
rate_limiter = RateLimiter()


def check_rate_limit(key: str, limit: int = None, window: int = 60):
    """Check rate limit for a given key"""
    if limit is None:
        limit = settings.rate_limit_per_minute
    
    if not rate_limiter.is_allowed(key, limit, window):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )