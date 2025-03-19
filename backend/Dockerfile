FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/core:/app/utils:/app/config

# Set work directory
WORKDIR /app
COPY core /app/core
COPY utils /app/utils
COPY config /app/config

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create log directory
RUN mkdir -p /app/logs

# Set permissions
RUN chmod +x /app/bot/entrypoint.sh

# Set entrypoint
ENTRYPOINT ["/app/bot/entrypoint.sh"]

# Run the bot
CMD ["python", "-m", "bot.main"] 