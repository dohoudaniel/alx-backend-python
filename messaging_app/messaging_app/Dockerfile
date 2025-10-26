# Dockerfile
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create app directory
WORKDIR /app

# Install system dependencies (for psycopg2 etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt /app/

RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Copy project code
COPY . /app/

# Ensure entrypoint is executable
COPY ./entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

# Use the entrypoint to run migrations/collectstatic if desired, then run gunicorn
ENTRYPOINT ["/app/entrypoint.sh"]
# Default command: run gunicorn binding to 0.0.0.0:8000
CMD ["gunicorn", "messaging_app.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]

