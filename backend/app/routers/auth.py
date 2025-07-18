from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import timedelta
import logging

from ..database import get_db
from ..auth import (
    authenticate_user, create_access_token, create_refresh_token,
    verify_token, hash_password, verify_password, get_current_active_user,
    check_rate_limit, REFRESH_TOKEN_TYPE
)
from ..models import User
from ..schemas import (
    LoginRequest, TokenResponse, RefreshTokenRequest, 
    PasswordChangeRequest, UserProfile, UserRole
)
from ..config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()
logger = logging.getLogger(__name__)


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Authenticate user and return JWT tokens"""
    
    # Rate limiting based on IP address
    client_ip = request.client.host
    check_rate_limit(f"login:{client_ip}", limit=10, window=300)  # 10 attempts per 5 minutes
    
    # Authenticate user
    user = authenticate_user(db, login_data.employee_id, login_data.password)
    
    if not user:
        logger.warning(f"Failed login attempt for employee_id: {login_data.employee_id} from IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect employee ID or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is inactive"
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    token_data = {"sub": user.employee_id, "role": user.role}
    access_token = create_access_token(token_data, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(token_data)
    
    user_profile = UserProfile(
        employee_id=user.employee_id,
        name=user.name,
        email=user.email,
        department=user.department,
        designation=user.designation,
        phone=user.phone,
        role=UserRole(user.role),
        last_login_time=user.last_login_time,
        created_at=user.created_at
    )
    
    logger.info(f"Successful login for employee_id: {user.employee_id}")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=user_profile
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    
    # Rate limiting
    client_ip = request.client.host
    check_rate_limit(f"refresh:{client_ip}", limit=20, window=300)
    
    try:
        payload = verify_token(refresh_data.refresh_token, token_type=REFRESH_TOKEN_TYPE)
        employee_id = payload.get("sub")
        
        if not employee_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user from database
        user = db.query(User).filter(
            User.employee_id == employee_id,
            User.is_active == True
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new tokens
        access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        
        token_data = {"sub": user.employee_id, "role": user.role}
        access_token = create_access_token(token_data, expires_delta=access_token_expires)
        new_refresh_token = create_refresh_token(token_data)
        
        user_profile = UserProfile(
            employee_id=user.employee_id,
            name=user.name,
            email=user.email,
            department=user.department,
            designation=user.designation,
            phone=user.phone,
            role=UserRole(user.role),
            last_login_time=user.last_login_time,
            created_at=user.created_at
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60,
            user=user_profile
        )
    
    except Exception as e:
        logger.error(f"Refresh token error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """Logout user (client should discard tokens)"""
    
    logger.info(f"User {current_user.employee_id} logged out")
    
    return {
        "message": "Successfully logged out",
        "detail": "Please discard your tokens on the client side"
    }


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user profile"""
    
    return UserProfile(
        employee_id=current_user.employee_id,
        name=current_user.name,
        email=current_user.email,
        department=current_user.department,
        designation=current_user.designation,
        phone=current_user.phone,
        role=UserRole(current_user.role),
        last_login_time=current_user.last_login_time,
        created_at=current_user.created_at
    )


@router.post("/change-password")
async def change_password(
    request: Request,
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    
    # Rate limiting
    client_ip = request.client.host
    check_rate_limit(f"change_password:{current_user.employee_id}", limit=5, window=300)
    
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Hash new password
    new_password_hash = hash_password(password_data.new_password)
    
    # Update password in database
    try:
        current_user.password_hash = new_password_hash
        db.commit()
        
        logger.info(f"Password changed for user {current_user.employee_id}")
        
        return {"message": "Password changed successfully"}
    
    except Exception as e:
        logger.error(f"Error changing password for user {current_user.employee_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.get("/verify")
async def verify_token_endpoint(current_user: User = Depends(get_current_active_user)):
    """Verify if current token is valid"""
    
    return {
        "valid": True,
        "employee_id": current_user.employee_id,
        "role": current_user.role,
        "message": "Token is valid"
    }


@router.get("/permissions")
async def get_user_permissions(current_user: User = Depends(get_current_active_user)):
    """Get user permissions based on role"""
    
    from ..auth import get_user_permissions
    permissions = get_user_permissions(current_user)
    
    return {
        "employee_id": current_user.employee_id,
        "role": current_user.role,
        "permissions": permissions
    }