#!/bin/sh

# Hash location
HASH_FILE="/usr/src/app/app/sql/function_trigger.sql.hash"
SQL_SCRIPT="/usr/src/app/app/sql/function_trigger.sql"

compute_hash() {
  md5sum "${SQL_SCRIPT}" | awk '{print $1}'
}

# Check PostgreSQL readiness
until pg_isready -h db -U "${DATABASE_USERNAME}"; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 2
done

# Set PGPASSWORD environment variable for psql
export PGPASSWORD="${DATABASE_PASSWORD}"

# Run Alembic migrations
echo "Running Alembic migrations..."
alembic upgrade head

# Run the SQL script for creating functions, triggers, and sequences
# Run only if there are any changes, check the hash
CURRENT_HASH=$(compute_hash)

if [ -f "${HASH_FILE}" ]; then
  STORED_HASH=$(cat "${HASH_FILE}")
  if [ "${CURRENT_HASH}" != "${STORED_HASH}" ]; then
    echo "Running SQL script..."
    if ! psql -h db -U "${DATABASE_USERNAME}" -d "${DATABASE_NAME}" -f "${SQL_SCRIPT}"; then
      echo "Failed to execute the SQL script" >&2
      exit 1
    fi
    # Update the hash
    echo "${CURRENT_HASH}" > "${HASH_FILE}"
  else
    echo "No changes in SQL script. Skipping..."
  fi
else
  echo "Hash file not found. Running SQL script..."
  if ! psql -h db -U "${DATABASE_USERNAME}" -d "${DATABASE_NAME}" -f "${SQL_SCRIPT}"; then
    echo "Failed to execute the SQL script" >&2
    exit 1
  fi
  # Create hash file with current hash
  echo "${CURRENT_HASH}" > "${HASH_FILE}"
fi

# Start the application
echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
