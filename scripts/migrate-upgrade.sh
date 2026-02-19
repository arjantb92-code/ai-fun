#!/bin/bash
# Run migrations tegen de database in je omgeving.
# Lokaal: zorg dat DATABASE_URL/DIRECT_URL niet gezet zijn (of lokaal); dan start je met start-backend.sh.
# Supabase: zet in .env de Supabase DATABASE_URL + DIRECT_URL en run dit script.

set -e
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && source .env && set +a

if [ -z "$DIRECT_URL" ]; then
  echo "DIRECT_URL niet gezet. Voor lokaal: gebruik start-backend.sh (zet URL automatisch)."
  echo "Voor Supabase: zet DIRECT_URL (en DATABASE_URL) in .env."
  exit 1
fi

echo "Migrations draaien (DIRECT_URL gebruikt voor DDL)..."
source venv/bin/activate
export PYTHONPATH=$PYTHONPATH:.
cd backend && flask db upgrade && cd ..
echo "Klaar."