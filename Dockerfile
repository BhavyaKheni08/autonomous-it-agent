# Use python 3.10 slim as base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for psycopg2/asyncpg
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# No default CMD, defined in docker-compose
