#!/bin/bash
# Better WBW - Backend Starter
# Gebruik:  ./start-backend.sh         (kies via .env)
#           ./start-backend.sh --local (forceer lokale Docker-DB)
#           ./start-backend.sh --remote (forceer Supabase/prod uit .env)

[ -f .env ] && set -a && source .env && set +a

# Override: --local = altijd lokaal, --remote = altijd DATABASE_URL uit .env
case "${1:-}" in
  --local)  unset DATABASE_URL DIRECT_URL ;;
  --remote) if [ -z "$DATABASE_URL" ] || [ -z "$DIRECT_URL" ]; then
              echo "Error: --remote vereist DATABASE_URL en DIRECT_URL in .env."
              exit 1
            fi ;;
  "")       ;;
  *)        echo "Usage: $0 [--local|--remote]"; exit 1 ;;
esac

echo "--- Starting Backend Services ---"

# 1. Clean up port 5001
echo "Cleaning port 5001..."
lsof -t -i :5001 | xargs kill -9 2>/dev/null || true

# 2. Start local DB only if not using external (e.g. Supabase)
if [ -z "$DATABASE_URL" ]; then
    echo "DB: lokaal (Docker)"
    if ! docker info > /dev/null 2>&1; then
        echo "Error: Docker is not running. Please start Docker Desktop."
        exit 1
    fi
    docker compose up -d
    export DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:5432/${POSTGRES_DB}"
    export DIRECT_URL="$DATABASE_URL"
else
    echo "DB: remote (Supabase/prod)"
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
