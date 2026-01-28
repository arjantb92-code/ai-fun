#!/bin/bash
# Better WBW - Backend Starter

echo "--- Starting Backend Services ---"

# 1. Clean up port 5001
echo "Cleaning port 5001..."
lsof -t -i :5001 | xargs kill -9 2>/dev/null || true

# 2. Ensure Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker Desktop."
    exit 1
fi

# 3. Start Database
echo "Starting Database..."
docker compose up -d

# 4. Apply Database Migrations
echo "Applying Database Migrations..."
source venv/bin/activate
export PYTHONPATH=$PYTHONPATH:.
cd backend && flask db upgrade && cd ..

# 5. Start Flask
echo "Starting Flask Server (Port 5001)..."
python3 backend/app.py
