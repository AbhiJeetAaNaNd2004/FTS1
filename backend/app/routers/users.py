from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional
import logging

from ..database import get_db
from ..auth import (
    get_current_active_user, require_admin, require_super_admin,
    require_admin_or_self, hash_password, UserRole
)
from ..models import User, Face, Log
from ..schemas import (
    UserCreate, UserUpdate, UserResponse, UserProfile,
    PaginationParams, PaginatedResponse
)

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=PaginatedResponse)
async def get_users(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name, employee_id, or email"),
    department: Optional[str] = Query(None, description="Filter by department"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get paginated list of users (Admin only)"""
    
    try:
        # Build query
        query = db.query(User)
        
        # Apply filters
        if search:
            search_filter = or_(
                User.name.ilike(f"%{search}%"),
                User.employee_id.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        if department:
            query = query.filter(User.department.ilike(f"%{department}%"))
        
        if role:
            query = query.filter(User.role == role.value)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        pagination = PaginationParams(page=page, size=size)
        users = query.offset(pagination.offset).limit(pagination.size).all()
        
        # Convert to response models
        user_responses = [
            UserResponse(
                employee_id=user.employee_id,
                name=user.name,
                email=user.email,
                department=user.department,
                designation=user.designation,
                phone=user.phone,
                role=UserRole(user.role),
                is_active=user.is_active,
                last_login_time=user.last_login_time,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            for user in users
        ]
        
        return PaginatedResponse.create(user_responses, total, page, size)
    
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users"
        )


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new user (Admin only)"""
    
    try:
        # Check if employee_id already exists
        existing_user = db.query(User).filter(User.employee_id == user_data.employee_id).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee ID already exists"
            )
        
        # Check if email already exists (if provided)
        if user_data.email:
            existing_email = db.query(User).filter(User.email == user_data.email).first()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )
        
        # Only super admin can create admin or super_admin users
        if user_data.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            if UserRole(current_user.role) != UserRole.SUPER_ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only super admin can create admin users"
                )
        
        # Hash password
        password_hash = hash_password(user_data.password)
        
        # Create user
        db_user = User(
            employee_id=user_data.employee_id,
            name=user_data.name,
            email=user_data.email,
            department=user_data.department,
            designation=user_data.designation,
            phone=user_data.phone,
            role=user_data.role.value,
            is_active=user_data.is_active,
            password_hash=password_hash
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"User created: {db_user.employee_id} by {current_user.employee_id}")
        
        return UserResponse(
            employee_id=db_user.employee_id,
            name=db_user.name,
            email=db_user.email,
            department=db_user.department,
            designation=db_user.designation,
            phone=db_user.phone,
            role=UserRole(db_user.role),
            is_active=db_user.is_active,
            last_login_time=db_user.last_login_time,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.get("/{employee_id}", response_model=UserResponse)
async def get_user(
    employee_id: str,
    current_user: User = Depends(require_admin_or_self(employee_id)),
    db: Session = Depends(get_db)
):
    """Get user by employee_id"""
    
    user = db.query(User).filter(User.employee_id == employee_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        employee_id=user.employee_id,
        name=user.name,
        email=user.email,
        department=user.department,
        designation=user.designation,
        phone=user.phone,
        role=UserRole(user.role),
        is_active=user.is_active,
        last_login_time=user.last_login_time,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.put("/{employee_id}", response_model=UserResponse)
async def update_user(
    employee_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user"""
    
    # Get target user
    user = db.query(User).filter(User.employee_id == employee_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions
    is_admin = UserRole(current_user.role) in [UserRole.ADMIN, UserRole.SUPER_ADMIN]
    is_self = current_user.employee_id == employee_id
    
    if not (is_admin or is_self):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Role change restrictions
    if user_data.role:
        # Only super admin can change roles
        if UserRole(current_user.role) != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super admin can change user roles"
            )
        
        # Cannot change own role unless creating another super admin
        if current_user.employee_id == employee_id:
            # Count existing super admins
            super_admin_count = db.query(User).filter(
                User.role == UserRole.SUPER_ADMIN.value,
                User.is_active == True
            ).count()
            
            if super_admin_count <= 1 and user_data.role != UserRole.SUPER_ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot change role - at least one super admin must exist"
                )
    
    # Non-admin users can only update their own basic info
    if not is_admin and is_self:
        # Restrict what employees can update
        allowed_fields = {"name", "email", "phone", "password"}
        update_fields = {k for k, v in user_data.dict(exclude_unset=True).items() if v is not None}
        
        if not update_fields.issubset(allowed_fields):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Employees can only update name, email, phone, and password"
            )
    
    try:
        # Check email uniqueness if being updated
        if user_data.email and user_data.email != user.email:
            existing_email = db.query(User).filter(
                User.email == user_data.email,
                User.employee_id != employee_id
            ).first()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )
        
        # Update fields
        update_data = user_data.dict(exclude_unset=True)
        
        if "password" in update_data:
            update_data["password_hash"] = hash_password(update_data.pop("password"))
        
        if "role" in update_data:
            update_data["role"] = update_data["role"].value
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"User updated: {employee_id} by {current_user.employee_id}")
        
        return UserResponse(
            employee_id=user.employee_id,
            name=user.name,
            email=user.email,
            department=user.department,
            designation=user.designation,
            phone=user.phone,
            role=UserRole(user.role),
            is_active=user.is_active,
            last_login_time=user.last_login_time,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {employee_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.delete("/{employee_id}")
async def delete_user(
    employee_id: str,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """Delete user (Super Admin only)"""
    
    # Get target user
    user = db.query(User).filter(User.employee_id == employee_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Cannot delete self
    if current_user.employee_id == employee_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Ensure at least one super admin remains
    if UserRole(user.role) == UserRole.SUPER_ADMIN:
        super_admin_count = db.query(User).filter(
            User.role == UserRole.SUPER_ADMIN.value,
            User.is_active == True
        ).count()
        
        if super_admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last super admin"
            )
    
    try:
        # Instead of hard delete, deactivate the user
        user.is_active = False
        db.commit()
        
        logger.info(f"User deactivated: {employee_id} by {current_user.employee_id}")
        
        return {"message": f"User {employee_id} has been deactivated"}
    
    except Exception as e:
        logger.error(f"Error deleting user {employee_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )


@router.get("/{employee_id}/summary")
async def get_user_summary(
    employee_id: str,
    current_user: User = Depends(require_admin_or_self(employee_id)),
    db: Session = Depends(get_db)
):
    """Get user summary with statistics"""
    
    user = db.query(User).filter(User.employee_id == employee_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Get face count
        face_count = db.query(Face).filter(
            Face.employee_id == employee_id,
            Face.is_active == True
        ).count()
        
        # Get log statistics
        total_logs = db.query(Log).filter(Log.employee_id == employee_id).count()
        
        # Get recent activity (last 30 days)
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        recent_logs = db.query(Log).filter(
            Log.employee_id == employee_id,
            Log.timestamp >= thirty_days_ago
        ).count()
        
        # Get last check-in/check-out
        last_checkin = db.query(Log).filter(
            Log.employee_id == employee_id,
            Log.event_type == "check-in"
        ).order_by(Log.timestamp.desc()).first()
        
        last_checkout = db.query(Log).filter(
            Log.employee_id == employee_id,
            Log.event_type == "check-out"
        ).order_by(Log.timestamp.desc()).first()
        
        return {
            "user": UserProfile(
                employee_id=user.employee_id,
                name=user.name,
                email=user.email,
                department=user.department,
                designation=user.designation,
                phone=user.phone,
                role=UserRole(user.role),
                last_login_time=user.last_login_time,
                created_at=user.created_at
            ),
            "statistics": {
                "face_count": face_count,
                "total_logs": total_logs,
                "recent_logs_30d": recent_logs,
                "last_checkin": last_checkin.timestamp if last_checkin else None,
                "last_checkout": last_checkout.timestamp if last_checkout else None
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting user summary for {employee_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user summary"
        )