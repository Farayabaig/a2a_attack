#!/bin/bash
set -e

echo "=== A2A Security POC - Docker Entrypoint ==="

# Wait for PostgreSQL if using it
if [ "${DB_USE_POSTGRES}" = "true" ]; then
    echo "Waiting for PostgreSQL to be ready..."
    until pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}"; do
        echo "PostgreSQL is unavailable - sleeping"
        sleep 2
    done
    echo "PostgreSQL is up!"
    
    # Initialize database
    echo "Initializing database..."
    python scripts/init_database.py || echo "Database init skipped or already initialized"
fi

# Execute the command
exec "$@"

