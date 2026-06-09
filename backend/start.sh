#!/bin/sh

echo "Waiting for Postgres to be ready..."

while ! python -c "
import psycopg2, os, sys

db_host = os.getenv('DATABASE_HOST', 'db')
db_port = os.getenv('DATABASE_PORT', '5432')
db_name = os.getenv('DATABASE_NAME')
db_user = os.getenv('DATABASE_USER')
db_pass = os.getenv('DATABASE_PASSWORD')

if not all([db_name, db_user, db_pass]):
    print('[ERROR] Faltan variables críticas (NAME, USER o PASSWORD) en el entorno/.env', file=sys.stderr)
    sys.exit(1)

try:
    psycopg2.connect(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_pass
    )
except Exception:
    sys.exit(1)
sys.exit(0)
" 2>/dev/null; do
  echo "Postgres is unavailable (or missing env variables) - sleeping 5s"
  sleep 5
done

echo "Postgres is up - fetching OSM stops and routes..."

if python osm_fetch.py && python osm_routes.py; then
    echo "OSM data processed successfully."
else
    echo "[WARNING] OSM synchronization encountered errors. Proceeding to boot..."
fi

echo "Starting Flask Server..."
exec python app.py