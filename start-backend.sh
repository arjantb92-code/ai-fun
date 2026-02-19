#!/bin/bash
# Better WBW - Backend Starter

# Load .env so DATABASE_URL / DIRECT_URL are set (Supabase = skip Docker)
[ -f .env ] && set -a && source .env && set +a

echo "--- Starting Backend Services ---"

# 1. Clean up port 5001
echo "Cleaning port 5001..."
lsof -t -i :5001 | xargs kill -9 2>/dev/null || true

# 2. Start local DB only if not using external (e.g. Supabase)
if [ -z "$DATABASE_URL" ]; then
    if ! docker info > /dev/null 2>&1; then
        echo "Error: Docker is not running. Please start Docker Desktop."
        exit 1
    fi
    echo "Starting Database..."
    docker compose up -d
else
    echo "Using external database (DATABASE_URL set). Skipping Docker."
fi

# 3. Apply Database Migrations
echo "Applying Database Migrations..."
source venv/bin/activate
export PYTHONPATH=$PYTHONPATH:.
cd backend && flask db upgrade && cd ..

# 4. Start Flask
echo "Starting Flask Server (Port 5001)..."
mkdir -p logs
python3 backend/app.py > logs/backend_$(date +%Y%m%d_%H%M%S).log 2>&1
