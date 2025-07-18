import os
import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
import logging
from datetime import datetime
import base64
import io
from PIL import Image
from sqlalchemy.orm import Session
import asyncio
import aiofiles
from concurrent.futures import ThreadPoolExecutor

try:
    from insightface.app import FaceAnalysis
except ImportError:
    FaceAnalysis = None
    logging.warning("InsightFace not available. Face recognition features will be disabled.")

from ..config import settings
from ..models import User, Face, Log, Camera
from ..schemas import FaceResponse, FaceEnrollmentResponse

logger = logging.getLogger(__name__)


class FaceRecognitionService:
    """Service for face recognition operations"""
    
    def __init__(self):
        self.app = None
        self.known_faces_dir = settings.known_faces_dir
        self.face_detection_threshold = settings.face_detection_threshold
        self.face_match_threshold = settings.face_match_threshold
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize face analysis app
        self._initialize_face_app()
        
        # Ensure directories exist
        os.makedirs(self.known_faces_dir, exist_ok=True)
        os.makedirs(settings.upload_dir, exist_ok=True)
    
    def _initialize_face_app(self):
        """Initialize the InsightFace application"""
        if FaceAnalysis is None:
            logger.error("InsightFace not available")
            return
        
        try:
            self.app = FaceAnalysis(
                name=settings.embedding_model,
                providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
            )
            self.app.prepare(ctx_id=0, det_size=(640, 640))
            logger.info("Face recognition model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize face recognition model: {e}")
            self.app = None
    
    def is_available(self) -> bool:
        """Check if face recognition is available"""
        return self.app is not None
    
    async def detect_faces(self, image_data: bytes) -> List[Dict[str, Any]]:
        """Detect faces in an image and return face information"""
        if not self.is_available():
            raise RuntimeError("Face recognition not available")
        
        try:
            # Convert bytes to numpy array
            image_array = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError("Invalid image data")
            
            # Run face detection in thread pool
            loop = asyncio.get_event_loop()
            faces = await loop.run_in_executor(
                self.executor, 
                self._detect_faces_sync, 
                image
            )
            
            return faces
        
        except Exception as e:
            logger.error(f"Error detecting faces: {e}")
            raise
    
    def _detect_faces_sync(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Synchronous face detection"""
        faces = self.app.get(image)
        
        face_data = []
        for i, face in enumerate(faces):
            # Calculate quality score based on various factors
            quality_score = self._calculate_quality_score(face, image)
            
            face_info = {
                "face_id": i,
                "bbox": face.bbox.tolist(),
                "landmarks": face.landmark_2d_106.tolist() if hasattr(face, 'landmark_2d_106') else None,
                "embedding": face.embedding.tolist(),
                "quality_score": quality_score,
                "confidence": float(face.det_score) if hasattr(face, 'det_score') else 1.0
            }
            face_data.append(face_info)
        
        return face_data
    
    def _calculate_quality_score(self, face, image: np.ndarray) -> float:
        """Calculate face quality score based on various metrics"""
        try:
            # Basic quality metrics
            bbox = face.bbox
            x1, y1, x2, y2 = map(int, bbox)
            
            # Face size score (larger faces are generally better)
            face_area = (x2 - x1) * (y2 - y1)
            image_area = image.shape[0] * image.shape[1]
            size_score = min(face_area / (image_area * 0.1), 1.0)  # Normalize to 0-1
            
            # Crop face region
            face_region = image[y1:y2, x1:x2]
            
            # Sharpness score (Laplacian variance)
            gray_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            sharpness = cv2.Laplacian(gray_face, cv2.CV_64F).var()
            sharpness_score = min(sharpness / 1000, 1.0)  # Normalize
            
            # Brightness score
            brightness = np.mean(gray_face)
            brightness_score = 1.0 - abs(brightness - 127) / 127  # Optimal around 127
            
            # Detection confidence
            confidence_score = float(face.det_score) if hasattr(face, 'det_score') else 1.0
            
            # Weighted average
            quality_score = (
                size_score * 0.3 +
                sharpness_score * 0.3 +
                brightness_score * 0.2 +
                confidence_score * 0.2
            )
            
            return float(quality_score)
        
        except Exception as e:
            logger.warning(f"Error calculating quality score: {e}")
            return 0.5  # Default quality score
    
    async def enroll_face(
        self, 
        db: Session, 
        employee_id: str, 
        image_files: List[bytes], 
        filenames: List[str]
    ) -> FaceEnrollmentResponse:
        """Enroll face(s) for an employee"""
        if not self.is_available():
            raise RuntimeError("Face recognition not available")
        
        # Verify user exists
        user = db.query(User).filter(User.employee_id == employee_id).first()
        if not user:
            raise ValueError(f"User with employee_id {employee_id} not found")
        
        enrolled_faces = []
        quality_scores = []
        successful_enrollments = 0
        
        # Create employee directory
        employee_dir = os.path.join(self.known_faces_dir, employee_id)
        os.makedirs(employee_dir, exist_ok=True)
        
        for i, (image_data, filename) in enumerate(zip(image_files, filenames)):
            try:
                # Detect faces
                faces = await self.detect_faces(image_data)
                
                if len(faces) != 1:
                    logger.warning(f"Expected 1 face in {filename}, found {len(faces)}")
                    continue
                
                face_info = faces[0]
                
                # Check quality threshold
                if face_info["quality_score"] < 0.3:  # Minimum quality threshold
                    logger.warning(f"Face quality too low in {filename}: {face_info['quality_score']}")
                    continue
                
                # Save image
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                image_filename = f"face_{timestamp}_{i}.jpg"
                image_path = os.path.join(employee_dir, image_filename)
                
                async with aiofiles.open(image_path, 'wb') as f:
                    await f.write(image_data)
                
                # Store in database
                face_record = Face(
                    employee_id=employee_id,
                    image_path=image_path,
                    embedding_vector=face_info["embedding"],
                    quality_score=face_info["quality_score"]
                )
                
                db.add(face_record)
                db.flush()  # Get the ID
                
                enrolled_faces.append(FaceResponse(
                    id=face_record.id,
                    employee_id=employee_id,
                    image_path=image_path,
                    quality_score=face_info["quality_score"],
                    created_at=face_record.created_at
                ))
                
                quality_scores.append(face_info["quality_score"])
                successful_enrollments += 1
                
            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")
                continue
        
        db.commit()
        
        success = successful_enrollments > 0
        message = f"Successfully enrolled {successful_enrollments} faces"
        if successful_enrollments < len(image_files):
            message += f" ({len(image_files) - successful_enrollments} failed)"
        
        return FaceEnrollmentResponse(
            success=success,
            message=message,
            face_count=successful_enrollments,
            quality_scores=quality_scores,
            faces=enrolled_faces
        )
    
    async def recognize_face(self, image_data: bytes, db: Session) -> Optional[Dict[str, Any]]:
        """Recognize a face in an image"""
        if not self.is_available():
            return None
        
        try:
            # Detect faces
            faces = await self.detect_faces(image_data)
            
            if not faces:
                return None
            
            # Use the best quality face
            best_face = max(faces, key=lambda x: x["quality_score"])
            
            if best_face["quality_score"] < 0.3:  # Minimum quality for recognition
                return None
            
            # Get all enrolled faces from database
            enrolled_faces = db.query(Face).filter(Face.is_active == True).all()
            
            if not enrolled_faces:
                return None
            
            # Find best match
            best_match = None
            best_distance = float('inf')
            
            query_embedding = np.array(best_face["embedding"])
            
            for enrolled_face in enrolled_faces:
                stored_embedding = np.array(enrolled_face.embedding_vector)
                
                # Calculate cosine similarity
                similarity = np.dot(query_embedding, stored_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(stored_embedding)
                )
                
                distance = 1 - similarity
                
                if distance < best_distance and similarity > self.face_match_threshold:
                    best_distance = distance
                    best_match = enrolled_face
            
            if best_match:
                user = db.query(User).filter(User.employee_id == best_match.employee_id).first()
                
                return {
                    "employee_id": best_match.employee_id,
                    "name": user.name if user else "Unknown",
                    "confidence": 1 - best_distance,
                    "quality_score": best_face["quality_score"],
                    "face_bbox": best_face["bbox"]
                }
            
            return None
        
        except Exception as e:
            logger.error(f"Error in face recognition: {e}")
            return None
    
    async def delete_face(self, db: Session, face_id: int, current_user: User) -> bool:
        """Delete a face record and associated files"""
        face = db.query(Face).filter(Face.id == face_id).first()
        
        if not face:
            return False
        
        # Check permissions
        from ..auth import check_face_access_permission
        if not check_face_access_permission(face.employee_id, current_user):
            raise PermissionError("Insufficient permissions to delete this face")
        
        try:
            # Delete image file
            if os.path.exists(face.image_path):
                os.remove(face.image_path)
            
            # Delete database record
            db.delete(face)
            db.commit()
            
            logger.info(f"Deleted face {face_id} for employee {face.employee_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting face {face_id}: {e}")
            db.rollback()
            return False
    
    async def get_user_faces(self, db: Session, employee_id: str) -> List[FaceResponse]:
        """Get all faces for a user"""
        faces = db.query(Face).filter(
            Face.employee_id == employee_id,
            Face.is_active == True
        ).all()
        
        return [
            FaceResponse(
                id=face.id,
                employee_id=face.employee_id,
                image_path=face.image_path,
                quality_score=face.quality_score,
                created_at=face.created_at
            )
            for face in faces
        ]
    
    async def get_face_image(self, db: Session, face_id: int) -> Optional[bytes]:
        """Get face image data"""
        face = db.query(Face).filter(Face.id == face_id).first()
        
        if not face or not os.path.exists(face.image_path):
            return None
        
        try:
            async with aiofiles.open(face.image_path, 'rb') as f:
                return await f.read()
        except Exception as e:
            logger.error(f"Error reading face image {face_id}: {e}")
            return None
    
    def base64_to_bytes(self, base64_string: str) -> bytes:
        """Convert base64 string to bytes"""
        try:
            # Remove data URL prefix if present
            if base64_string.startswith('data:image'):
                base64_string = base64_string.split(',')[1]
            
            return base64.b64decode(base64_string)
        except Exception as e:
            logger.error(f"Error decoding base64 image: {e}")
            raise ValueError("Invalid base64 image data")
    
    def bytes_to_base64(self, image_bytes: bytes, format: str = "JPEG") -> str:
        """Convert bytes to base64 string"""
        try:
            base64_string = base64.b64encode(image_bytes).decode('utf-8')
            return f"data:image/{format.lower()};base64,{base64_string}"
        except Exception as e:
            logger.error(f"Error encoding image to base64: {e}")
            raise ValueError("Failed to encode image")


# Global face service instance
face_service = FaceRecognitionService()