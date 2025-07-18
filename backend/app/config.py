import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    # Database Configuration
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "face_tracking"
    db_user: str = "postgres"
    db_password: str = "password"
    
    # JWT Security
    jwt_secret_key: str = "your-super-secret-jwt-key-change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # Face Recognition Configuration
    known_faces_dir: str = "./known_faces"
    face_detection_threshold: float = 0.5
    face_match_threshold: float = 0.6
    embedding_model: str = "antelopev2"
    
    # File Storage
    upload_dir: str = "./uploads"
    max_file_size: int = 10485760  # 10MB
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    workers: int = 4
    
    # Camera Configuration
    default_camera_resolution_width: int = 1920
    default_camera_resolution_height: int = 1080
    default_camera_fps: int = 30
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"
    
    # CORS Settings
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    allowed_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allowed_headers: List[str] = ["*"]
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10
    
    @validator('allowed_origins', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @validator('allowed_methods', pre=True)
    def parse_cors_methods(cls, v):
        if isinstance(v, str):
            return [method.strip() for method in v.split(',')]
        return v
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()