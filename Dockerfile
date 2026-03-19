FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system packages required for certain Python modules and SQLite
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy all application code
COPY . .

# Create a data directory for persistent SQLite storage
RUN mkdir -p /data

# By default, run the client app (overridden in docker-compose)
EXPOSE 5001 5005
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "app:app"]
