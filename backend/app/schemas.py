from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Any, Dict
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    EMPLOYEE = "employee"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class EventType(str, Enum):
    CHECK_IN = "check-in"
    CHECK_OUT = "check-out"


class CameraType(str, Enum):
    ENTRY = "entry"
    EXIT = "exit"
    MONITORING = "monitoring"


# Base schemas
class UserBase(BaseModel):
    employee_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    department: Optional[str] = Field(None, max_length=100)
    designation: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role: UserRole = UserRole.EMPLOYEE
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    department: Optional[str] = Field(None, max_length=100)
    designation: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    
    @validator('password')
    def validate_password(cls, v):
        if v is not None:
            if len(v) < 8:
                raise ValueError('Password must be at least 8 characters long')
            if not any(c.isupper() for c in v):
                raise ValueError('Password must contain at least one uppercase letter')
            if not any(c.islower() for c in v):
                raise ValueError('Password must contain at least one lowercase letter')
            if not any(c.isdigit() for c in v):
                raise ValueError('Password must contain at least one digit')
        return v


class UserResponse(UserBase):
    last_login_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class UserProfile(BaseModel):
    employee_id: str
    name: str
    email: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole
    last_login_time: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        orm_mode = True


# Face schemas
class FaceBase(BaseModel):
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class FaceResponse(FaceBase):
    id: int
    employee_id: str
    image_path: str
    quality_score: Optional[float] = None
    created_at: datetime
    
    class Config:
        orm_mode = True


# Log schemas
class LogBase(BaseModel):
    event_type: EventType
    camera_id: int
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = None


class LogCreate(LogBase):
    employee_id: str


class LogResponse(LogBase):
    id: int
    employee_id: str
    timestamp: datetime
    user: Optional[UserProfile] = None
    
    class Config:
        orm_mode = True


# Camera schemas
class CameraBase(BaseModel):
    location: str = Field(..., min_length=1, max_length=200)
    stream_url: Optional[str] = Field(None, max_length=500)
    camera_type: CameraType = CameraType.ENTRY
    resolution_width: int = Field(1920, ge=640, le=3840)
    resolution_height: int = Field(1080, ge=480, le=2160)
    fps: int = Field(30, ge=1, le=60)
    is_active: bool = True


class CameraCreate(CameraBase):
    pass


class CameraUpdate(BaseModel):
    location: Optional[str] = Field(None, min_length=1, max_length=200)
    stream_url: Optional[str] = Field(None, max_length=500)
    camera_type: Optional[CameraType] = None
    resolution_width: Optional[int] = Field(None, ge=640, le=3840)
    resolution_height: Optional[int] = Field(None, ge=480, le=2160)
    fps: Optional[int] = Field(None, ge=1, le=60)
    is_active: Optional[bool] = None


class CameraResponse(CameraBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


# Authentication schemas
class LoginRequest(BaseModel):
    employee_id: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfile


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


# File upload schemas
class FileUploadResponse(BaseModel):
    filename: str
    file_path: str
    file_size: int
    upload_time: datetime


class FaceEnrollmentRequest(BaseModel):
    employee_id: str = Field(..., min_length=1, max_length=50)


class FaceEnrollmentResponse(BaseModel):
    success: bool
    message: str
    face_count: int
    quality_scores: List[float]
    faces: List[FaceResponse]


# Dashboard and statistics schemas
class DashboardStats(BaseModel):
    total_employees: int
    active_employees: int
    total_faces_enrolled: int
    total_logs_today: int
    check_ins_today: int
    check_outs_today: int
    active_cameras: int


class EmployeePresenceStatus(BaseModel):
    employee_id: str
    name: str
    status: str  # "checked-in", "checked-out", "unknown"
    last_event_time: Optional[datetime] = None
    last_event_type: Optional[EventType] = None


class AttendanceReport(BaseModel):
    employee_id: str
    name: str
    date: str
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    total_hours: Optional[float] = None
    status: str  # "present", "absent", "partial"


# Pagination schemas
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(10, ge=1, le=100)
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
    
    @classmethod
    def create(cls, items: List[Any], total: int, page: int, size: int):
        pages = (total + size - 1) // size  # Ceiling division
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )


# WebSocket message schemas
class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


class LiveDetectionEvent(BaseModel):
    employee_id: str
    name: str
    event_type: EventType
    camera_id: int
    camera_location: str
    confidence_score: float
    timestamp: datetime
    image_data: Optional[str] = None  # Base64 encoded image


# Error schemas
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ValidationErrorResponse(BaseModel):
    error: str = "validation_error"
    message: str
    details: List[Dict[str, Any]]