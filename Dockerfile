# فایل Dockerfile برای ساخت ایمیج Docker

FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  POETRY_VERSION=1.7.1 \
  POETRY_HOME="/opt/poetry" \
  POETRY_VIRTUALENVS_IN_PROJECT=false \
  POETRY_NO_INTERACTION=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  gcc \
  default-libmysqlclient-dev \
  pkg-config \
  && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --upgrade pip \
  && pip install "poetry==$POETRY_VERSION"

# Set working directory
WORKDIR /app

# Copy poetry.lock* and pyproject.toml in case they exist
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

# Copy the project code
COPY . .

# Create scripts directory and copy the CLI script
RUN mkdir -p /usr/local/bin
COPY scripts/moonvpn.sh /usr/local/bin/moonvpn
RUN chmod +x /usr/local/bin/moonvpn

# Command to run
CMD ["python", "-m", "bot.main"]
