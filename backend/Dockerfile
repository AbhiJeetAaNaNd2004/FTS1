FROM python:3.10.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    curl \
    git \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    libgl1-mesa-glx \
    libglib2.0-dev \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/known_faces /app/uploads /app/logs

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy application code
COPY backend/app/ ./app/
COPY db_config.py .
COPY db_models.py .
COPY db_manager.py .

# Copy the updated models to the backend app directory
COPY backend/app/models.py ./app/models.py

# Create a startup script
RUN echo '#!/bin/bash\n\
set -e\n\
echo "Starting Face Recognition System Backend..."\n\
echo "Waiting for database..."\n\
while ! nc -z postgres 5432; do\n\
  sleep 1\n\
done\n\
echo "Database is ready!"\n\
echo "Creating database tables..."\n\
python -c "from app.database import create_tables; create_tables()"\n\
echo "Starting FastAPI server..."\n\
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4\n\
' > /app/start.sh && chmod +x /app/start.sh

# Install netcat for database health check
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set proper permissions
RUN chown -R nobody:nogroup /app
USER nobody

# Start the application
CMD ["/app/start.sh"]