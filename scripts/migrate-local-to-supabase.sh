#!/bin/bash
# Migreer data van lokale Postgres (Docker volume) naar Supabase.
# Gebruik: vanuit projectroot: ./scripts/migrate-local-to-supabase.sh

set -e
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && source .env && set +a

DUMP_FILE="$(pwd)/.local_data_dump.sql"
SEQ_FILE="$(pwd)/.seq_fix.sql"
MIGRATE_DIR="$(pwd)"

echo "--- Local → Supabase data migration ---"

# 1. Start lokale Postgres op 5433 (evt. bestaande container op 5432 laten)
if [ ! -d "postgres-data" ] || [ ! -f "postgres-data/PG_VERSION" ]; then
    echo "Geen lokaal postgres-data gevonden. Niets om te migreren."
    exit 1
fi

CONTAINER="wbw_migrate_local"
docker rm -f "$CONTAINER" 2>/dev/null || true
echo "Start lokale DB op port 5433..."
docker run -d --name "$CONTAINER" \
  -p "5433:5432" \
  -v "$(pwd)/postgres-data:/var/lib/postgresql/data" \
  -v "${MIGRATE_DIR}:/migrate" \
  -e "POSTGRES_USER=${POSTGRES_USER}" \
  -e "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}" \
  -e "POSTGRES_DB=${POSTGRES_DB}" \
  postgres:15-alpine

# Wacht tot Postgres in de container klaar is (geen host pg_isready nodig)
echo "Wachten op Postgres in container..."
sleep 5
for i in $(seq 1 60); do
  if docker exec "$CONTAINER" pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" 2>/dev/null; then
    break
  fi
  if [ "$i" -eq 60 ]; then
    echo "Timeout. Container logs:"
    docker logs "$CONTAINER" 2>&1 | tail -30
    docker rm -f "$CONTAINER" 2>/dev/null || true
    exit 1
  fi
  sleep 1
done
echo "Lokale DB is bereikbaar."

# 2. Dump binnen de container (geen pg_dump op host nodig)
echo "Dumpen van data..."
docker exec "$CONTAINER" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  --data-only --no-owner --no-privileges --exclude-table-data=alembic_version -f /migrate/.local_data_dump.sql

# 3. Container stoppen
docker rm -f "$CONTAINER" 2>/dev/null || true

# 4. Import in Supabase via Docker (geen psql op host nodig)
echo "Importeren in Supabase..."
docker run --rm -v "${MIGRATE_DIR}:/migrate" -e DIRECT_URL="$DIRECT_URL" postgres:15-alpine \
  sh -c 'psql "$DIRECT_URL" -v ON_ERROR_STOP=1 -c "SET session_replication_role = replica;" -f /migrate/.local_data_dump.sql -c "SET session_replication_role = DEFAULT;"'

# 5. Sequences bijwerken
echo "Sequences bijwerken..."
cat > "$SEQ_FILE" <<'SQLEOF'
DO $$
DECLARE r RECORD;
BEGIN
  FOR r IN
    SELECT n.nspname AS schema, c.relname AS seqname
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.relkind = 'S' AND n.nspname = 'public'
  LOOP
    IF r.seqname::text ~ '_id_seq$' THEN
      EXECUTE format('SELECT setval(%L, COALESCE((SELECT MAX(id) FROM %I.%I), 1))',
        r.schema || '.' || r.seqname, r.schema, regexp_replace(r.seqname::text, '_id_seq$', '')::name);
    END IF;
  END LOOP;
END $$;
SQLEOF
docker run --rm -v "${MIGRATE_DIR}:/migrate" -e DIRECT_URL="$DIRECT_URL" postgres:15-alpine \
  sh -c 'psql "$DIRECT_URL" -v ON_ERROR_STOP=1 -f /migrate/.seq_fix.sql'

rm -f "$DUMP_FILE" "$SEQ_FILE"
echo "Klaar. Data staat op Supabase."
echo "Lokaal volume postgres-data is ongewijzigd; je kunt het later verwijderen als je wilt."