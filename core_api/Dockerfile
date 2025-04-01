# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (if any, e.g., for database drivers)
# RUN apt-get update && apt-get install -y --no-install-recommends some-package && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Copy the requirements file first to leverage Docker cache
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8888

# Command to run the application using Uvicorn
# Use 0.0.0.0 to make it accessible from outside the container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8888"] 