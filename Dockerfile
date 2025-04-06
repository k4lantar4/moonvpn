# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies
# Add any build-time dependencies needed for your Python packages here
# RUN apt-get update && apt-get install -y --no-install-recommends some-package && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Expose ports if needed (e.g., for FastAPI)
# EXPOSE 8000

# Default command can be overridden in docker-compose.yml
# CMD ["python", "api/main.py"] # Or bot/main.py
