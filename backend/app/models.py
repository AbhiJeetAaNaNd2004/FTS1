from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY
from .database import Base


class User(Base):
    """User model representing employees and admin users"""
    __tablename__ = 'users'
    
    employee_id = Column(String, primary_key=True, index=True)  # Company-assigned employee ID
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default='employee')  # employee, admin, super_admin
    email = Column(String, unique=True)
    department = Column(String)
    designation = Column(String)
    phone = Column(String)
    is_active = Column(Boolean, default=True)
    last_login_time = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    faces = relationship("Face", back_populates="user", cascade="all, delete-orphan")
    logs = relationship("Log", back_populates="user")


class Face(Base):
    """Face model storing images and embeddings for face recognition"""
    __tablename__ = 'faces'
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, ForeignKey('users.employee_id'), nullable=False, index=True)
    image_path = Column(String, nullable=False)
    embedding_vector = Column(ARRAY(Float), nullable=False)  # PostgreSQL array for embeddings
    quality_score = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="faces")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_faces_employee_id', 'employee_id'),
        Index('idx_faces_created_at', 'created_at'),
        Index('idx_faces_is_active', 'is_active'),
    )


class Log(Base):
    """Log model for tracking check-in/check-out events"""
    __tablename__ = 'logs'
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, ForeignKey('users.employee_id'), nullable=False, index=True)
    timestamp = Column(DateTime, default=func.now(), index=True)
    event_type = Column(String, nullable=False)  # check-in, check-out
    camera_id = Column(Integer, ForeignKey('cameras.id'), nullable=False)
    confidence_score = Column(Float)
    metadata = Column(JSON)  # Additional event data
    
    # Relationships
    user = relationship("User", back_populates="logs")
    camera = relationship("Camera", back_populates="logs")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_logs_employee_id_timestamp', 'employee_id', 'timestamp'),
        Index('idx_logs_timestamp', 'timestamp'),
        Index('idx_logs_event_type', 'event_type'),
        Index('idx_logs_camera_id', 'camera_id'),
    )


class Camera(Base):
    """Camera model for managing video feed sources"""
    __tablename__ = 'cameras'
    
    id = Column(Integer, primary_key=True, index=True)
    location = Column(String, nullable=False)
    stream_url = Column(String)
    camera_type = Column(String, default='entry')  # entry, exit, monitoring
    resolution_width = Column(Integer, default=1920)
    resolution_height = Column(Integer, default=1080)
    fps = Column(Integer, default=30)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    logs = relationship("Log", back_populates="camera")


# Legacy models for backward compatibility
class Employee(Base):
    """Legacy employee model - kept for compatibility"""
    __tablename__ = 'employees'
    
    id = Column(String, primary_key=True, index=True)
    employee_name = Column(String, nullable=False)
    department = Column(String)
    designation = Column(String)
    email = Column(String)
    phone = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    embeddings = relationship("FaceEmbedding", back_populates="employee")
    attendance_records = relationship("AttendanceRecord", back_populates="employee")
    tracking_records = relationship("TrackingRecord", back_populates="employee")


class FaceEmbedding(Base):
    """Legacy face embedding model - kept for compatibility"""
    __tablename__ = 'face_embeddings'
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, ForeignKey('employees.id'), nullable=False)
    embedding_data = Column(Text, nullable=False)  # Base64 encoded embedding
    embedding_type = Column(String, default='enroll')
    quality_score = Column(Float)
    source_image_path = Column(String)
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    employee = relationship("Employee", back_populates="embeddings")


class AttendanceRecord(Base):
    """Legacy attendance record model - kept for compatibility"""
    __tablename__ = 'attendance_records'
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, ForeignKey('employees.id'), nullable=False)
    camera_id = Column(Integer, nullable=False)
    event_type = Column(String, nullable=False)
    timestamp = Column(DateTime, default=func.now())
    confidence_score = Column(Float)
    work_status = Column(String, default='working')
    is_valid = Column(Boolean, default=True)
    notes = Column(Text)
    
    # Relationships
    employee = relationship("Employee", back_populates="attendance_records")


class TrackingRecord(Base):
    """Legacy tracking record model - kept for compatibility"""
    __tablename__ = 'tracking_records'
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, ForeignKey('employees.id'), nullable=False)
    camera_id = Column(Integer, nullable=False)
    position_x = Column(Float)
    position_y = Column(Float)
    confidence_score = Column(Float)
    quality_metrics = Column(JSON)
    timestamp = Column(DateTime, default=func.now())
    tracking_state = Column(String, default='active')
    
    # Relationships
    employee = relationship("Employee", back_populates="tracking_records")


class CameraConfig(Base):
    """Legacy camera config model - kept for compatibility"""
    __tablename__ = 'camera_configs'
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, unique=True, nullable=False)
    camera_name = Column(String, nullable=False)
    camera_type = Column(String, default='entry')
    resolution_width = Column(Integer, default=1920)
    resolution_height = Column(Integer, default=1080)
    fps = Column(Integer, default=30)
    gpu_id = Column(Integer, default=0)
    tripwire_config = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class SystemLog(Base):
    """System log model for application-level logging"""
    __tablename__ = 'system_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    log_level = Column(String, default='INFO')
    message = Column(Text, nullable=False)
    component = Column(String)
    employee_id = Column(String)
    camera_id = Column(Integer)
    timestamp = Column(DateTime, default=func.now())
    additional_data = Column(JSON)